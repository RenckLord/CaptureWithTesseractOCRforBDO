import cv2
import numpy as np
import mss
import easyocr
import time
import re
from flask import Flask
from flask_socketio import SocketIO

# --- CONFIGURACIÓN ---
MONITOR_NUMBER = 1
CHAT_BOX_COORDS = {"top": 550, "left": 1460, "width": 395, "height": 250}
ITEMS_TO_TRACK_TEMPLATE = {
    "Bulto de brana endurecido": {"count": 0, "silver_value": 17000},
    "Cristal oscuro sellado":    {"count": 0, "silver_value": 11800},
    "Colgante de río renacido":  {"count": 0, "silver_value": 335000},
    "Semilla del vacío":          {"count": 0, "silver_value": 10000000},
    "Fragmento nocturno de agua":{"count": 0, "silver_value": 100000},
    "Oleaje de Okiara":          {"count": 0, "silver_value": 3000000},
    "Masa de magia pura":        {"count": 0, "silver_value": 51000},
    "Piedra oscura":             {"count": 0, "silver_value": 13500},
    "Resto de naturaleza":       {"count": 0, "silver_value": 500},
    "Aleta de naga magullada":   {"count": 0, "silver_value": 0},
    "Máscara de Bandido Desgastado": {"count": 0, "silver_value": 21000},
    "Piedra de Caphras":             {"count": 0, "silver_value": 1900000},
    "Piedra Negra":                  {"count": 0, "silver_value": 258000},
    "Polvo del Espíritu Ancestral":  {"count": 0, "silver_value": 325000},
    "El Origen de la Depredación Oscura": {"count": 0, "silver_value": 540000000},
    "Cristal de la Madrugada":       {"count": 0, "silver_value": 80000000},
    "Cristal de la Madrugada BON":   {"count": 0, "silver_value": 1000000000}
}
ITEMS_TO_TRACK = ITEMS_TO_TRACK_TEMPLATE.copy()
LOOT_MESSAGE_KEYWORD = "Has obtenido"

# --- SERVIDOR Y ESTADO DE SESIÓN ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
session_state = { "is_running": False, "is_paused": False, "start_time": 0, "time_offset": 0 }

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

def loot_counter_loop():
    print("Cargando modelo de OCR (EasyOCR)...")
    reader = easyocr.Reader(['es'], gpu=False)
    print("Modelo de OCR cargado.")
    
    last_canonical_tags = set()
    
    with mss.mss() as sct:
        target_monitor = sct.monitors[MONITOR_NUMBER]
        capture_coords = { "top": target_monitor["top"] + CHAT_BOX_COORDS["top"], "left": target_monitor["left"] + CHAT_BOX_COORDS["left"], "width": CHAT_BOX_COORDS["width"], "height": CHAT_BOX_COORDS["height"] }

        while True:
            elapsed_time = 0
            if session_state["is_running"]:
                if session_state["is_paused"]:
                    elapsed_time = session_state["time_offset"]
                else:
                    elapsed_time = (time.time() - session_state["start_time"]) + session_state["time_offset"]

            if not session_state["is_running"]:
                socketio.sleep(1)
                continue
            
            if not session_state["is_paused"]:
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
                last_canonical_tags = current_canonical_tags
            
            data_to_send = {"items": ITEMS_TO_TRACK, "elapsed_time": elapsed_time}
            socketio.emit('update_full_data', data_to_send)

            socketio.sleep(1.5)

@socketio.on('connect')
def handle_connect():
    print('Cliente de Overlay conectado.')
    socketio.emit('update_full_data', {"items": ITEMS_TO_TRACK, "elapsed_time": 0})

@socketio.on('control_session')
def handle_control_session(data):
    action = data.get('action')
    global ITEMS_TO_TRACK

    if action == 'start':
        if not session_state["is_running"]:
            print(" Iniciando sesión...")
            session_state.update({"is_running": True, "is_paused": False, "start_time": time.time(), "time_offset": 0})
            ITEMS_TO_TRACK = {k: v.copy() for k, v in ITEMS_TO_TRACK_TEMPLATE.items()}
            for item in ITEMS_TO_TRACK.values(): item['count'] = 0

    elif action == 'pause':
        if session_state["is_running"] and not session_state["is_paused"]:
            print("Pausando sesión...")
            session_state["is_paused"] = True
            session_state["time_offset"] += time.time() - session_state["start_time"]
        elif session_state["is_running"] and session_state["is_paused"]:
            print("Reanudando sesión...")
            session_state["is_paused"] = False
            session_state["start_time"] = time.time()

    elif action == 'stop':
        if session_state["is_running"]:
            print("Deteniendo sesión...")
            session_state.update({"is_running": False, "is_paused": False, "start_time": 0, "time_offset": 0})
            ITEMS_TO_TRACK = {k: v.copy() for k, v in ITEMS_TO_TRACK_TEMPLATE.items()}
            for item in ITEMS_TO_TRACK.values(): item['count'] = 0
            socketio.emit('update_full_data', {"items": {}, "elapsed_time": 0})

if __name__ == '__main__':
    print("Iniciando servidor de BDO Loot Tracker en http://127.0.0.1:5000")
    socketio.start_background_task(target=loot_counter_loop)
    socketio.run(app, host='127.0.0.1', port=5000)

