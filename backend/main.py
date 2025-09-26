# main.py

# Importa a função que criamos no outro arquivo
from analyse import processar_imagem

import base64
import io
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
import cv2

# ================================
# API E VARIÁVEIS GLOBAIS
# ================================

#variavels para impedir que 
frames_since_detection = 0
leniencia_frames_falha = 6
resultados_de_falha = {"NAO IDENTIFICADO", "NENHUMA MÃO DETECTADA"}

current_result = "Aguardando..."

# fastapi é tipo o express
app = FastAPI()

# configurando o cors para deixar o backend se comunicar com o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # libera para qualquer origem no dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# modelo para os frames recebidos
class VideoFrame(BaseModel):
    frame: str

# ================================
# ENDPOINTS
# ================================

# endpoint para o envio do video da câmera do usuário
@app.post("/frame")
async def process_video_frame(data: VideoFrame):
    """
    Recebe um frame em base64, o processa para identificar o sinal,
    e armazena o resultado.
    """
    global current_result, frames_since_detection
    try:
        # Decodifica a imagem base64 recebida do frontend
        header, encoded = data.frame.split(",", 1)
        image_data = base64.b64decode(encoded)
        
        # Converte os dados da imagem para um formato que o OpenCV entende
        pil_image = Image.open(io.BytesIO(image_data))
        image_np = np.array(pil_image)
        # Converte de RGB (padrão do PIL) para BGR (padrão do OpenCV)
        image_cv2 = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        # Chama a função de processamento do outro arquivo
        result = processar_imagem(image_cv2)
        
        # Atualiza a variável global com o resultado
        if result in resultados_de_falha:
            if frames_since_detection < leniencia_frames_falha:
                frames_since_detection += 1
            else:
                current_result = result
        else:
            if frames_since_detection < leniencia_frames_falha / 3:
                frames_since_detection += 1
            else:
                frames_since_detection = 0
                current_result = result
        print(f"Frame processado. Resultado: {current_result}")

        return {
            "status": "Sucesso",
            "detected_sign": current_result,
        }

    except Exception as e:
        print(f"Erro: {e}")
        current_result = "Erro no processamento"
        return {"status": "erro", "mensagem": str(e)}

# endpoint de tradução
@app.get("/translate")
def get_translation():
    """
    Retorna o último resultado da tradução que foi armazenado.
    """
    return {"translation": current_result}

# endpoint raiz
@app.get("/")
def read_root():
    return {"Mensagem": "Servidor online. Envie frames para /frame e obtenha resultados em /translate."}