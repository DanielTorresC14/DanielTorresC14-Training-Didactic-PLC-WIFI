import json
import threading
import qrcode
from flask import Flask, request, jsonify, render_template, send_from_directory
import socket
from pyngrok import ngrok, conf

from rich import print
from rich.logging import RichHandler
import logging

# Configura el logging con RichHandler
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

conf.get_default().auth_token = "2xQprcnt5tRC67VvfEBolGOoOH3_3Vo2CpgnoMfD6K3raazd4"

HOST = ''
PORT = 5007
conn = None

app = Flask(__name__, static_folder='static')


def generar_qr (data:str, path:str) -> None:
    # Datos que deseas codifica

    # Crear el objeto QR
    qr = qrcode.QRCode(
        version=1,  # controla el tamaño del QR (1 es el más pequeño)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # tamaño de cada caja del código QR
        border=4,  # grosor del borde
    )

    # Añadir los datos
    qr.add_data(data)
    qr.make(fit=True)

    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar la imagen
    img.save(path)


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
    esp32_connection.sendall((json.dumps({id:value}) + '\n').encode())


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

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No necesita conectarse realmente
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        print(f'IP LOCAL: {ip_local}')
    except Exception:
        ip_local = "127.0.0.1"
    finally:
        s.close()
    return ip_local


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
    public_url = ngrok.connect(5000)
    print(f" * URL pública: {public_url}")
    generar_qr(public_url.__str__().split('"')[1], 'pagina_publica.png')
    generar_qr(f'http://{obtener_ip_local()}:5000', 'pagina_local.png')
    app.run(host='localhost', port=5000, debug=True, use_reloader=False)