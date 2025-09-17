import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import keyboard
import os
import asyncio
from flask import Flask
from flask_socketio import SocketIO

# --- CONFIGURACIÓN DE USUARIO ---
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

# --- CONFIGURACIÓN DEL SERVIDOR ---
app = Flask(__name__)
# Permitimos la conexión desde cualquier origen (necesario para Electron)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- LÓGICA DE PROCESAMIENTO DE IMAGEN ---
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

# --- BUCLE PRINCIPAL DEL CONTADOR ---
async def loot_counter_loop():
    previous_lines = []
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
            processed_img_np = process_image(img_np)
            text_block = pytesseract.image_to_string(processed_img_np, lang='spa').strip()

            current_lines = [line for line in text_block.splitlines() if line.strip() and LOOT_MESSAGE_KEYWORD in line]
            
            common_suffix_len = 0
            for i in range(1, min(len(current_lines), len(previous_lines)) + 1):
                if current_lines[-i] == previous_lines[-i]:
                    common_suffix_len += 1
                else:
                    break
            
            new_lines = current_lines[:-common_suffix_len] if common_suffix_len > 0 else current_lines

            if new_lines:
                updated = False
                for line in new_lines:
                    match = re.search(r"\[(.+?)\](?:.*x(\d+))?", line)
                    if match:
                        item_name = match.group(1).strip()
                        quantity_str = match.group(2)
                        qty = int(quantity_str) if quantity_str else 1
                        
                        if item_name in ITEMS_TO_TRACK:
                            ITEMS_TO_TRACK[item_name]['count'] += qty
                            print(f"✔️ Detectado: {item_name} x{qty}")
                            updated = True
                
                if updated:
                    # Si hubo una actualización, prepara y envía los datos al front-end
                    total_loot = sum(d['count'] for d in ITEMS_TO_TRACK.values())
                    total_silver = sum(d['count'] * d['silver_value'] for d in ITEMS_TO_TRACK.values())
                    elapsed_time = time.time() - start_time
                    
                    data_to_send = {
                        "total_loot": total_loot,
                        "total_silver": total_silver,
                        "elapsed_time": elapsed_time
                    }
                    # Emite el evento 'update_data' que el front-end está escuchando
                    socketio.emit('update_data', data_to_send)

            previous_lines = current_lines
            await asyncio.sleep(1.5)

@socketio.on('connect')
def handle_connect():
    """Se ejecuta cuando el front-end se conecta."""
    print('Cliente de Overlay conectado.')

if __name__ == '__main__':
    print("Iniciando servidor de BDO Loot Tracker en http://127.0.0.1:5000")
    # Inicia el bucle de conteo en una tarea de fondo
    socketio.start_background_task(loot_counter_loop)
    # Inicia el servidor web
    socketio.run(app, host='127.0.0.1', port=5000)