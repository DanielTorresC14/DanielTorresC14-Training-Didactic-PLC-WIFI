import usocket as socket
import json

from connect_esp_wifi import connect_wifi
from machine import Pin

connect_wifi('ITZACATEPEC', '')

# Configuración inicial de pines (OUTPUT)
button_pins = {
    'button1': Pin(13, Pin.OUT),
    'button2': Pin(12, Pin.OUT),
    'button3': Pin(14, Pin.OUT),
    'button4': Pin(27, Pin.OUT),
    'button5': Pin(26, Pin.OUT),
    'button6': Pin(25, Pin.OUT),
    'emergency': Pin(18, Pin.OUT),
    'selector0': Pin(19, Pin.OUT),  # Selector posición 0
    'selector1': Pin(20, Pin.OUT),  # Selector posición 1
    'selector2': Pin(21, Pin.OUT)   # Selector posición 2
}

# Estados iniciales (0/1 para botones, 0-2 para selector)
button_states = {
    'button1': 1,
    'button2': 0,
    'button3': 0,
    'button4': 0,
    'button5': 0,
    'button6': 0,
    'emergency': 0,
    'selector': 0  # 0, 1 o 2
}

def update_pins():
    """Actualiza los pines físicos en < 0.1ms basado en button_states"""
    # Botones normales.
    normal_buttons = [f"button{i}" for i in range(1, 7)]
    normal_buttons.append('emergency')
    for btn in normal_buttons:
        button_pins[btn].value(button_states[btn])
    
    # Selector (solo un pin activo)
    selector_pos = button_states['selector']
    button_pins['selector0'].value(1 if selector_pos == 0 else 0)
    button_pins['selector1'].value(1 if selector_pos == 1 else 0)
    button_pins['selector2'].value(1 if selector_pos == 2 else 0)

# Ejemplo de uso:
if __name__ == "__main__":
    
    HOST = '10.177.127.195'  # La dirección del servidor remoto
    PORT = 5007         # El mismo puerto usado por el servidor

    # Crear un socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Conectar al servidor
        s.connect((HOST, PORT))
        print(f'Conectado a {HOST}:{PORT}')
        
        # Bucle principal para recibir datos
        while True:
            try:
                data = s.recv(1024)
                if not data:
                    continue
                print(data.decode())
                # Cambios desde la web
                button_states.update(json.loads((data.decode())))
                update_pins()
            except:
                pass
            
    except Exception as e:
        print(f'Error: {e}')