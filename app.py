import os
import cv2
import numpy as np 
import base64      
from datetime import datetime 
from flask import Flask, render_template, request, jsonify, send_file


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    """Renderiza a página inicial."""
    return render_template('index.html')

@app.route('/image/<filename>')
def get_uploaded_image(filename):
    """Serve uma imagem previamente salva."""
    safe_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    if not safe_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return jsonify({'error': 'Acesso inválido'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

@app.route('/upload', methods=['POST'])
def process_uploaded_image():
    """Recebe uma imagem, aplica o filtro Canny e retorna a imagem processada."""
    if 'image' not in request.files:
        return jsonify({'error': 'Nenhuma parte de arquivo na requisição'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    client_ip = request.remote_addr
    current_dt_iso = datetime.now().isoformat()

    try:
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            app.logger.warning(f"Falha ao decodificar imagem de {client_ip}. Tipo: {file.content_type}")
            return jsonify({'error': 'Formato de imagem inválido ou não suportado'}), 400

        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_img, 100, 200)

        is_success, buffer = cv2.imencode(".png", edges)

        if not is_success:
            app.logger.error("Falha ao codificar a imagem processada para PNG.")
            return jsonify({'error': 'Falha ao codificar a imagem processada'}), 500

        img_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'message': 'Imagem recebida e processada com sucesso!',
            'datetime': current_dt_iso,
            'ip_address': client_ip,
            'processed_image_format': 'png',
            'processed_image_data_uri': f"data:image/png;base64,{img_base64}",
        })

    except Exception as e:
        app.logger.error(f"Erro ao processar imagem de {client_ip}: {e}", exc_info=True)
        return jsonify({'error': 'Erro interno no servidor durante o processamento da imagem'}), 500

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)
