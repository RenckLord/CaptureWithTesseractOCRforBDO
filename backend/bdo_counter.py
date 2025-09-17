import cv2
import numpy as np
import mss
import easyocr
import time
import re
from flask import Flask
from flask_socketio import SocketIO

# --- CONFIGURACIÓN DE USUARIO ---
MONITOR_NUMBER = 1
CHAT_BOX_COORDS = {"top": 550, "left": 1460, "width": 395, "height": 250}

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
    "Resto de naturaleza":       {"count": 0, "silver_value": 500},
}
LOOT_MESSAGE_KEYWORD = "Has obtenido"

# --- CONFIGURACIÓN DEL SERVIDOR ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def get_canonical_loot_tags(text_block):
    canonical_tags = []
    lines = text_block.split('\n')
    for line in lines:
        if LOOT_MESSAGE_KEYWORD in line:
            for item_name in ITEMS_TO_TRACK.keys():
                if item_name in line:
                    quantity = 1
                    match = re.search(r'x(\d+)', line)
                    if match:
                        quantity = int(match.group(1))
                    canonical_tags.append(f"{item_name}|{quantity}")
                    break
    return canonical_tags

# --- BUCLE PRINCIPAL DEL CONTADOR ---
def loot_counter_loop():
    print("Cargando modelo de OCR (EasyOCR)... Esto puede tardar un momento.")
    # Usamos CPU explícitamente.
    reader = easyocr.Reader(['es'], gpu=False)
    print("Modelo de OCR cargado. Iniciando contador.")
    
    last_canonical_tags = set()
    start_time = time.time()

    with mss.mss() as sct:
        target_monitor = sct.monitors[MONITOR_NUMBER]
        capture_coords = {
            "top": target_monitor["top"] + CHAT_BOX_COORDS["top"],
            "left": target_monitor["left"] + CHAT_BOX_COORDS["left"],
            "width": CHAT_BOX_COORDS["width"],
            "height": CHAT_BOX_COORDS["height"],
        }

        while True:
            screenshot_img = sct.grab(capture_coords)
            img_np = np.array(screenshot_img)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            
            ocr_results = reader.readtext(img_bgr)
            current_text_block = "\n".join([result[1] for result in ocr_results])
            
            current_canonical_tags = set(get_canonical_loot_tags(current_text_block))
            new_loot = current_canonical_tags - last_canonical_tags
            
            if new_loot:
                for tag in new_loot:
                    try:
                        item_name, quantity_str = tag.split('|')
                        quantity = int(quantity_str)
                        if item_name in ITEMS_TO_TRACK:
                            ITEMS_TO_TRACK[item_name]['count'] += quantity
                            print(f"✔️ Detectado: {item_name} x{quantity}")
                    except ValueError:
                        continue
            
            total_loot = sum(d['count'] for d in ITEMS_TO_TRACK.values())
            total_silver = sum(d['count'] * d['silver_value'] for d in ITEMS_TO_TRACK.values())
            elapsed_time = time.time() - start_time
            data_to_send = {"total_loot": total_loot, "total_silver": total_silver, "elapsed_time": elapsed_time}
            socketio.emit('update_data', data_to_send)

            last_canonical_tags = current_canonical_tags
            socketio.sleep(1.5)

@socketio.on('connect')
def handle_connect():
    print('Cliente de Overlay conectado.')

if __name__ == '__main__':
    print("Iniciando servidor de BDO Loot Tracker en http://127.0.0.1:5000")
    socketio.start_background_task(target=loot_counter_loop)
    socketio.run(app, host='127.0.0.1', port=5000)