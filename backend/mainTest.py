# main.py

from movimentTest import processar_imagem, identificar_movimento_libras

from collections import deque, Counter
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

app = FastAPI()

letter_buffer = deque(maxlen=15)
trajectory_buffer = deque(maxlen=30)
last_stable_result = "Aguardando..."

# Configurando o CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoFrame(BaseModel):
    frame: str

# ================================
# ENDPOINTS
# ================================

@app.post("/frame")
async def process_video_frame(data: VideoFrame):
    """
    Recebe um frame, o processa, e armazena o resultado e a trajetória nos buffers.
    """
    try:
        header, encoded = data.frame.split(",", 1)
        image_data = base64.b64decode(encoded)
        
        pil_image = Image.open(io.BytesIO(image_data))
        image_np = np.array(pil_image)
        image_cv2 = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        static_letter, landmarks = processar_imagem(image_cv2)
        
        if static_letter != "Nenhuma mao detectada":
            letter_buffer.append(static_letter)

        if landmarks:
            trajectory_buffer.append(landmarks)
        else:
            trajectory_buffer.clear()

        return {"status": "Sucesso"}

    except Exception as e:
        print(f"Erro: {e}")
        letter_buffer.clear()
        trajectory_buffer.clear()
        return {"status": "erro", "mensagem": str(e)}

@app.get("/translate")
def get_translation():
    """
    Analisa os buffers para identificar um gesto de movimento ou a letra estática mais estável.
    """
    global last_stable_result

        motion_gesture = identificar_movimento_libras(trajectory_buffer)
        if motion_gesture != "NAO IDENTIFICADO":
            last_stable_result = motion_gesture
            letter_buffer.clear()
            trajectory_buffer.clear()
            return {"translation": last_stable_result}

    if not letter_buffer:
        return {"translation": last_stable_result if last_stable_result != "Aguardando..." else "Analisando..."}

    counts = Counter(letter_buffer)
    most_common_letter, num_occurrences = counts.most_common(1)[0]

    if num_occurrences / len(letter_buffer) > 0.3:
        if most_common_letter != "NAO IDENTIFICADO":
            last_stable_result = most_common_letter
            trajectory_buffer.clear()
    
    return {"translation": last_stable_result}

@app.get("/")
def read_root():
    return {"Mensagem": "Servidor online."}