import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab
import pygetwindow as gw
import time
import json
import datetime

# Thiết lập pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Đường dẫn tới file JSON
species_path = r"D:\PokeOne\PokeBot\Bot\Database\species.json"
type_effectiveness_path = r"D:\PokeOne\PokeBot\Bot\Database\type_effectiveness.json"

# Đọc dữ liệu từ file JSON
with open(species_path, 'r') as f:
    species_data = json.load(f)

with open(type_effectiveness_path, 'r') as f:
    type_effectiveness_data = json.load(f)

def switch_to_pokeone_window():
    windows = gw.getWindowsWithTitle('PokeOne')
    if windows:
        pokeone_window = windows[0]
        pokeone_window.activate()
        return True
    return False

def capture_screen():
    screen = ImageGrab.grab()
    screen_np = np.array(screen)
    screen_rgb = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)
    return screen_rgb

def find_opponent_pokemon_name(screen):
    # Cắt phần có thể chứa tên Pokémon đối thủ từ ảnh chụp màn hình
    x, y, width, height = 10, 10, 180, 50  # Điều chỉnh theo vị trí thực tế
    roi = screen[y:y+height, x:x+width]

    # Chuyển đổi ảnh thành màu xám và nhị phân để dễ dàng nhận diện ký tự
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Sử dụng pytesseract để nhận diện ký tự từ ảnh
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(binary, config=custom_config)

    # Trả về kết quả nhận diện
    return text.strip()

def clean_pokemon_name(text):
    # Duyệt qua danh sách Pokémon để tìm tên phù hợp
    for pokemon in species_data:
        if pokemon["name"].lower() in text.lower():
            return pokemon["name"], pokemon["types"]
    return None, None

def find_weakness(types):
    weaknesses = []
    for t in types:
        for effectiveness in type_effectiveness_data:
            if effectiveness["attack"] == t.lower() and effectiveness["effectiveness"] == 2:
                weaknesses.append(effectiveness["defend"])
    return weaknesses

def log_shiny_encounter(pokemon_name):
    with open("shiny_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()}: Gặp Pokémon Shiny: {pokemon_name}\n")

def main():
    if switch_to_pokeone_window():
        processed_pokemon = set()
        encounter_count = 0
        while encounter_count < 5:
            # Chụp màn hình
            screen = capture_screen()

            # Tìm tên Pokémon đối thủ
            raw_text = find_opponent_pokemon_name(screen)
            if raw_text and raw_text not in processed_pokemon:
                processed_pokemon.add(raw_text)
                encounter_count += 1

                if raw_text.startswith('S '):
                    log_shiny_encounter(raw_text)
                
                pokemon_name, pokemon_types = clean_pokemon_name(raw_text)
                if pokemon_name:
                    print(f"Tên Pokémon: {pokemon_name}")
                    print(f"Hệ của Pokémon: {pokemon_types}")
                    
                    weaknesses = find_weakness(pokemon_types)
                    if weaknesses:
                        print(f"{pokemon_name} yếu thế trước: {', '.join(weaknesses)}")
                    else:
                        print(f"{pokemon_name} không có hệ yếu thế đặc biệt.")
                else:
                    print("Không tìm thấy tên Pokémon phù hợp.")
            else:
                print("Không nhận diện được tên Pokémon hoặc đã xử lý.")
            
            # Chờ một khoảng thời gian trước khi chụp màn hình tiếp theo
            time.sleep(2)
        print("Đã gặp 5 Pokémon.")
    else:
        print("Không tìm thấy cửa sổ PokeOne")

if __name__ == "__main__":
    main()
