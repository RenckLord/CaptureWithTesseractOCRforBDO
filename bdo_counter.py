import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import keyboard
import os

# --- CONFIGURACIÓN ---
DEBUG_MODE = False
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
MONITOR_NUMBER = 1
CHAT_BOX_COORDS = {"top": 550, "left": 1460, "width": 395, "height": 250}
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
# --- FIN DE LA CONFIGURACIÓN ---

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def process_image(img):
    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 
                                   11, 
                                   4)
    kernel = np.ones((1, 1), np.uint8)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    return thresh

def print_summary(items_data):
    clear_console()
    print(" BDO Loot Tracker by Gemini ")
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
    print(f"\nMonitoreando el botín en el MONITOR {MONITOR_NUMBER}... (Presiona 'q' para salir)")

# --- FUNCIÓN MODIFICADA ---
def parse_new_lines(new_lines, items_data):
    """
    Esta función ahora solo procesa las líneas que se le pasan,
    asumiendo que ya son nuevas y únicas.
    """
    updated = False
    for line in new_lines:
        if LOOT_MESSAGE_KEYWORD in line:
            for item_name in items_data.keys():
                if item_name in line:
                    quantity = 1
                    match = re.search(r'x(\d+)', line)
                    if match:
                        quantity = int(match.group(1))
                    
                    items_data[item_name]['count'] += quantity
                    updated = True
                    print(f"✔️ Detectado: {line}")
                    break 
    return updated

def main():
    # Esta variable guardará el texto del ciclo anterior.
    last_text_block = ""
    print("🚀 Iniciando BDO Loot Tracker...")
    print(f"Asegúrate de que el juego esté activo en el monitor {MONITOR_NUMBER}.")
    time.sleep(2)
    print_summary(ITEMS_TO_TRACK)

    with mss.mss() as sct:
        try:
            target_monitor = sct.monitors[MONITOR_NUMBER]
        except IndexError:
            print(f"🚨 ERROR: ¡El monitor número {MONITOR_NUMBER} no existe!")
            return
        
        capture_coords = {
            "top": target_monitor["top"] + CHAT_BOX_COORDS["top"],
            "left": target_monitor["left"] + CHAT_BOX_COORDS["left"],
            "width": CHAT_BOX_COORDS["width"],
            "height": CHAT_BOX_COORDS["height"],
        }

        while True:
            if keyboard.is_pressed('q'):
                print("\n🛑 Deteniendo el script...")
                break

            screenshot_img = sct.grab(capture_coords)
            img_np = np.array(screenshot_img)
            processed_img_np = process_image(img_np)
            current_text_block = pytesseract.image_to_string(processed_img_np, lang='spa').strip()

            # --- LÓGICA DE DETECCIÓN DE CAMBIOS ---
            # Solo continuamos si el texto actual es diferente al del ciclo anterior
            if current_text_block != last_text_block:
                
                # Convertimos los bloques de texto en conjuntos de líneas para compararlos
                last_lines = set(last_text_block.split('\n'))
                current_lines = set(current_text_block.split('\n'))
                
                # Calculamos las líneas que están en el texto actual pero no en el anterior
                new_lines = current_lines - last_lines
                
                # Si hay líneas nuevas, las procesamos
                if new_lines:
                    if parse_new_lines(new_lines, ITEMS_TO_TRACK):
                        print_summary(ITEMS_TO_TRACK)
                
                # Actualizamos el texto anterior para el próximo ciclo
                last_text_block = current_text_block
            
            time.sleep(1.5)

    print("\n--- RESUMEN FINAL DE LA SESIÓN ---")
    print_summary(ITEMS_TO_TRACK)

if __name__ == "__main__":
    main()