import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab
import pygetwindow as gw
import time
import json
import datetime
import subprocess

# Đường dẫn tới tệp hình ảnh và tệp JSON
CENTER_IMAGE_PATH = r"D:\PokeOne\PokeBot\Bot\Image\center.png"
GO_IMAGE_PATH = r"D:\PokeOne\PokeBot\Bot\Image\GO!.png"
LOGIN_IMAGE_PATH = r"D:\PokeOne\PokeBot\Bot\Image\Login.png"
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
MOVES_JSON_PATH = r"D:\PokeOne\PokeBot\Bot\Database\moves.json"
SPECIES_JSON_PATH = r"D:\PokeOne\PokeBot\Bot\Database\species.json"
TYPE_EFFECTIVENESS_JSON_PATH = r"D:\PokeOne\PokeBot\Bot\Database\type_effectiveness.json"

# Tải dữ liệu từ các tệp JSON
def load_json_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Không tìm thấy tệp {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Lỗi phân tích cú pháp JSON: {e}")
        return {}

moves_data = load_json_data(MOVES_JSON_PATH)
species_data = load_json_data(SPECIES_JSON_PATH)
type_effectiveness_data = load_json_data(TYPE_EFFECTIVENESS_JSON_PATH)

# Mở PokeOne launcher
def open_pokeone_launcher():
    launcher_path = r"D:\PokeOne\PokeOne\Launcher.exe"
    print(f"Đang mở Launcher từ {launcher_path}...")
    try:
        subprocess.Popen([launcher_path])
        time.sleep(3)  # Đợi 3 giây để Launcher mở
    except Exception as e:
        print(f"Không thể mở Launcher: {e}")

# Chuyển sang cửa sổ PokeOne
def switch_to_pokeone_window():
    print("Đang tập trung vào cửa sổ PokeOne...")
    windows = gw.getWindowsWithTitle('PokeOne')
    if windows:
        pokeone_window = windows[0]
        if not pokeone_window.isActive:
            pokeone_window.activate()
        pokeone_window.restore()
        pokeone_window.maximize()
        print("Đã kích hoạt cửa sổ PokeOne.")
        return True
    print("Không tìm thấy cửa sổ PokeOne. Vui lòng đảm bảo rằng trò chơi đang chạy.")
    return False

# Chụp màn hình
def capture_screen(region=None):
    print("Đang chụp màn hình...")
    if region:
        x1, y1, x2, y2 = region
        return np.array(ImageGrab.grab(bbox=(x1, y1, x2, y2)))
    return np.array(ImageGrab.grab())

# Phát hiện và nhấp chuột vào hình ảnh
def check_and_click_button(button_image_path):
    print(f"Đang phát hiện và nhấp vào nút từ {button_image_path}...")
    button_image = cv2.imread(button_image_path, cv2.IMREAD_GRAYSCALE)
    if button_image is None:
        print(f"Không thể tải hình ảnh từ {button_image_path}")
        return False

    screen = capture_screen()
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(screen_gray, button_image, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val > 0.8:
        print(f"Đã phát hiện nút từ {button_image_path}.")
        button_h, button_w = button_image.shape
        center_x = max_loc[0] + button_w // 2
        center_y = max_loc[1] + button_h // 2
        click_position(center_x, center_y)
        return True
    return False

# Nhấp chuột vào vị trí cụ thể
def click_position(x, y):
    print(f"Đang nhấp chuột vào vị trí ({x}, {y})...")
    from ctypes import windll
    windll.user32.SetCursorPos(x, y)
    windll.user32.mouse_event(2, 0, 0, 0, 0)  # nhấn chuột trái
    time.sleep(0.05)  # giữ nút trong 50ms
    windll.user32.mouse_event(4, 0, 0, 0, 0)  # thả chuột trái

# Phát hiện vòng tròn trung tâm
def detect_center_circle(screen):
    print("Đang phát hiện vòng tròn trung tâm...")
    template = cv2.imread(CENTER_IMAGE_PATH, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"Không thể tải hình ảnh mẫu từ {CENTER_IMAGE_PATH}")
        return None

    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val > 0.8:
        print("Đã phát hiện vòng tròn trung tâm.")
        return max_loc
    print("Không phát hiện được vòng tròn trung tâm.")
    return None

# Tiền xử lý hình ảnh
def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

# Trích xuất văn bản xung quanh trung tâm
def extract_text_around_center(screen, center_pos):
    print("Đang trích xuất văn bản xung quanh trung tâm...")
    h, w, _ = screen.shape
    skill_regions = [
        (center_pos[0] - 160, center_pos[1] - 50, center_pos[0] - 40, center_pos[1] - 10),
        (center_pos[0] + 50, center_pos[1] - 50, center_pos[0] + 170, center_pos[1] - 10),
        (center_pos[0] - 160, center_pos[1] + 20, center_pos[0] - 40, center_pos[1] + 80),
        (center_pos[0] + 50, center_pos[1] + 20, center_pos[0] + 170, center_pos[1] + 80),
    ]

    skill_texts = []
    for region in skill_regions:
        x1, y1, x2, y2 = region
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        skill_img = screen[y1:y2, x1:x2]
        preprocessed_img = preprocess_image(skill_img)
        text = pytesseract.image_to_string(preprocessed_img, config='--psm 7').strip()
        skill_texts.append(text)
    
    return skill_texts

# Tìm thông tin kỹ năng
def find_skill_info(skill_name):
    for move in moves_data:
        if move['name'].lower() == skill_name.lower():
            return move
    return None

# Tìm tên Pokémon đối thủ
def find_opponent_pokemon_name(screen):
    print("Đang tìm tên Pokémon đối thủ...")
    x, y, width, height = 10, 10, 180, 50
    roi = screen[y:y+height, x:x+width]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(binary, config=custom_config).strip()
    print(f"Nhận diện văn bản: {text}")
    return text

# Làm sạch tên Pokémon
def clean_pokemon_name(text):
    print("Đang làm sạch tên Pokémon...")
    cleaned_text = text.split()[1] if text.startswith('S ') else text
    for pokemon in species_data:
        if pokemon["name"].lower() in cleaned_text.lower():
            return pokemon["name"], pokemon["types"]
    return None, None

# Tìm hệ yếu thế
def find_weakness(types):
    weaknesses = []
    for t in types:
        for effectiveness in type_effectiveness_data:
            if effectiveness["attack"] == t.lower() and effectiveness["effectiveness"] == 2:
                weaknesses.append(effectiveness["defend"])
    return weaknesses

# Chọn hệ yếu thế có hiệu quả cao nhất
def select_best_weakness(weaknesses):
    if not weaknesses:
        return None
    effectiveness_count = {weakness: 0 for weakness in weaknesses}
    for effectiveness in type_effectiveness_data:
        if effectiveness["defend"] in weaknesses:
            effectiveness_count[effectiveness["defend"]] += 1
    return max(effectiveness_count, key=effectiveness_count.get, default=None)

# Tìm kỹ năng có power cao nhất
def find_highest_power_skill(skill_texts):
    skill_powers = []
    for text in skill_texts:
        if text:
            skill_info = find_skill_info(text)
            if skill_info and 'power' in skill_info:
                skill_powers.append((skill_info['name'], skill_info['power']))
    if skill_powers:
        return max(skill_powers, key=lambda x: (x[1] if x[1] is not None else 0))
    return None

# Ghi nhật ký khi gặp Pokémon Shiny
def log_shiny_encounter(pokemon_name):
    with open("shiny_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()}: Gặp Pokémon Shiny: {pokemon_name}\n")

# Vòng lặp chính
def main_loop():
    while True:
        try:
            if not switch_to_pokeone_window():
                open_pokeone_launcher()
                if check_and_click_button(GO_IMAGE_PATH):
                    time.sleep(2)
                    if check_and_click_button(LOGIN_IMAGE_PATH):
                        print("Đã nhấp vào nút Login.")
                time.sleep(5)
            else:
                screen = capture_screen()
                center_pos = detect_center_circle(screen)
                if center_pos:
                    skill_texts = extract_text_around_center(screen, center_pos)
                    print("Tên các kỹ năng được phát hiện:")
                    for text in skill_texts:
                        if text:
                            skill_info = find_skill_info(text)
                            if skill_info:
                                print(json.dumps(skill_info, indent=2, ensure_ascii=False))
                            else:
                                print(f"Không tìm thấy thông tin cho kỹ năng: {text}")
                    
                    # Chọn kỹ năng có power cao nhất
                    highest_power_skill = find_highest_power_skill(skill_texts)
                    if highest_power_skill:
                        print(f"Kỹ năng có power cao nhất: {highest_power_skill[0]} với power {highest_power_skill[1]}")
                    else:
                        print("Không tìm thấy thông tin power cho các kỹ năng.")
                
                raw_text = find_opponent_pokemon_name(screen)
                if raw_text:
                    if raw_text.startswith('S '):
                        log_shiny_encounter(raw_text)
                    pokemon_name, pokemon_types = clean_pokemon_name(raw_text)
                    if pokemon_name:
                        print(f"Tên Pokémon: {pokemon_name}")
                        print(f"Hệ của Pokémon: {pokemon_types}")
                        weaknesses = find_weakness(pokemon_types)
                        if weaknesses:
                            best_weakness = select_best_weakness(weaknesses)
                            if best_weakness:
                                print(f"Hệ yếu thế hiệu quả cao nhất: {best_weakness}")
                            else:
                                print("Không tìm thấy hệ yếu thế có hiệu quả.")
                        else:
                            print(f"{pokemon_name} không có hệ yếu thế đặc biệt.")
                    else:
                        print("Không tìm thấy tên Pokémon phù hợp.")
                else:
                    print("Không nhận diện được tên Pokémon hoặc đã xử lý.")
        except Exception as e:
            print(f"Đã xảy ra lỗi: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main_loop()
