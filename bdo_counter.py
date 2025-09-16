import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import keyboard
import os

# --- CONFIGURACIÓN DE USUARIO ---
DEBUG_MODE = False
MONITOR_NUMBER = 1
CHAT_BOX_COORDS = {"top": 550, "left": 1460, "width": 395, "height": 250}
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- LISTA DE OBJETOS A RASTREAR ---
ITEMS_TO_TRACK = {
    "Bulto de brana endurecido": {"count": 0, "silver_value": 17000},
    "Cristal oscuro sellado":    {"count": 0, "silver_value": 11800},
    "Colgante de río renacido":  {"count": 0, "silver_value": 335000},
    "Semilla del vacío":          {"count": 0, "silver_value": 10000000},
    "Fragmento nocturno de agua":{"count": 0, "silver_value": 100000},
    "Oleaje de Okiara":          {"count": 0, "silver_value": 3000000},
    "Masa de magia pura":        {"count": 0, "silver_value": 51000},
    "Piedra oscura":             {"count": 0, "silver_value": 13500},
    "Resto de naturaleza":       {"count": 0, "silver_value": 500}
}
LOOT_MESSAGE_KEYWORD = "Has obtenido"

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def process_image(img):
    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 
                                   11, 4)
    kernel = np.ones((1, 1), np.uint8)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    return thresh

def print_summary(items_data):
    clear_console()
    print(" BDO Loot Tracker")
    print("=" * 60)
    print(f"{'Objeto':<35} | {'Cantidad':>10} | {'Valor (Platas)':>15}")
    print("-" * 60)
    grand_total_silver = 0
    for name, data in items_data.items():
        if data['count'] > 0:
            total_silver = data['count'] * data['silver_value']
            grand_total_silver += total_silver
            print(f"{name:<35} | {data['count']:>10,} | {total_silver:>15,}")
    print("-" * 60)
    print(f"{'VALOR TOTAL ACUMULADO:':<48} | {grand_total_silver:>15,}")
    print("=" * 60)
    print(f"\nMonitoreando en MONITOR {MONITOR_NUMBER}... (Presiona 'q' para salir)")

def get_canonical_loot_tags(text_block, items_to_track):
    canonical_tags = []
    lines = text_block.split('\n')
    for line in lines:
        if LOOT_MESSAGE_KEYWORD in line:
            for item_name in items_to_track.keys():
                if item_name in line:
                    quantity = 1
                    match = re.search(r'x(\d+)', line)
                    if match:
                        quantity = int(match.group(1))
                    
                    canonical_tags.append(f"{item_name}|{quantity}")
                    break
    return canonical_tags

def main():
    last_canonical_tags = set()
    print("Iniciando BDO Loot Tracker...")
    print(f"Asegúrate de que el juego esté activo en el monitor {MONITOR_NUMBER}.")
    time.sleep(2)
    print_summary(ITEMS_TO_TRACK)

    with mss.mss() as sct:
        try:
            target_monitor = sct.monitors[MONITOR_NUMBER]
        except IndexError:
            print(f"ERROR: El monitor número {MONITOR_NUMBER} no existe.")
            return
        
        capture_coords = {
            "top": target_monitor["top"] + CHAT_BOX_COORDS["top"],
            "left": target_monitor["left"] + CHAT_BOX_COORDS["left"],
            "width": CHAT_BOX_COORDS["width"],
            "height": CHAT_BOX_COORDS["height"],
        }

        while True:
            if keyboard.is_pressed('q'):
                print("\nDeteniendo el script...")
                break

            screenshot_img = sct.grab(capture_coords)
            img_np = np.array(screenshot_img)
            processed_img_np = process_image(img_np)
            current_text_block = pytesseract.image_to_string(processed_img_np, lang='spa').strip()

            current_canonical_tags = set(get_canonical_loot_tags(current_text_block, ITEMS_TO_TRACK))
            new_loot = current_canonical_tags - last_canonical_tags
            
            if new_loot:
                updated = False
                for tag in new_loot:
                    try:
                        item_name, quantity_str = tag.split('|')
                        quantity = int(quantity_str)
                        
                        if item_name in ITEMS_TO_TRACK:
                            ITEMS_TO_TRACK[item_name]['count'] += quantity
                            updated = True
                    except ValueError:
                        continue
                
                if updated:
                    print_summary(ITEMS_TO_TRACK)

            last_canonical_tags = current_canonical_tags
            time.sleep(1.5)

    print("\n--- RESUMEN FINAL DE LA SESIÓN ---")
    print_summary(ITEMS_TO_TRACK)

if __name__ == "__main__":
    main()