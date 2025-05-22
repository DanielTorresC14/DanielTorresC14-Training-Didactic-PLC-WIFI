import json
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory
import socket
import os

HOST = ''
PORT = 5007
conn = None

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Sirve las imágenes y otros archivos estáticos"""
    return send_from_directory('static', filename)

@app.route('/api/signal', methods=['POST'])
def handle_signal():
    """API para recibir señales desde la interfaz web"""
    try:
        data = request.get_json()
        id = data.get('id')
        value = data.get('value')
        
        if id is None:
            return jsonify({"error": "Se requieren los parámetros 'id' y 'value'"}), 400
        
        # Enviar el estado a la ESP32 (aquí debes implementar la lógica de comunicación)
        send_to_esp32(id, value)
        
        return jsonify({"success": True, "message": f"Señal enviada: pin {id} = {value}"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



def send_to_esp32(id, value):
    global esp32_connection
    """Función para enviar datos a la ESP32"""
    print(f"Enviando a ESP32: id {id} = {value}")
    # Aquí implementarás la comunicación real con la ESP32
    esp32_connection.sendall(json.dumps({id:value}).encode())


def connectESP32():
    global esp32_connection
    print("Esperando conexión del ESP32...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    
    while True:
        try:
            conn, addr = s.accept()
            esp32_connection = conn
            print(f'Conectado con ESP32: {addr}')

            # El socket permanecerá activo para enviar datos cuando sea necesario
            
            # Espera hasta que la conexión se cierre para buscar una nueva
            while esp32_connection:
                import time
                time.sleep(1)  # Comprueba cada segundo
                
        except Exception as e:
            print(f"Error en la conexión: {e}")
        finally:
            if esp32_connection:
                esp32_connection.close()
            print("Conexión cerrada, esperando nueva conexión...")
            esp32_connection = None


if __name__ == '__main__':
    try:
        with open('templates/index.html', 'w') as f:
            with open('static/index.html', 'r') as source:
                f.write(source.read())
        print("Archivo HTML copiado correctamente")
    except Exception as e:
        print(f"Error al copiar el archivo HTML: {e}")

    # Iniciar el servidor de socket en un hilo separado.
    socket_thread = threading.Thread(target=connectESP32, daemon=True)
    socket_thread.start()
    
    # Iniciar la aplicación Flask
    print("Iniciando servidor web Flask...")
    app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)