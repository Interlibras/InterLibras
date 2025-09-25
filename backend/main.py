# main.py

import base64
import io
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from datetime import datetime

# diretório para salvar os frames que são recebidos
if not os.path.exists("output_frames"):
    os.makedirs("output_frames")

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

# endpoint para o envio do video da câmera do usuário
@app.post("/frame")
async def process_video_frame(data: VideoFrame):
    """
    Recebe um frame em base64 e o salva
    """
    try:
        header, encoded = data.frame.split(",", 1)
        dados_imagem = base64.b64decode(encoded)

        imagem = Image.open(io.BytesIO(dados_imagem))

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        caminho_do_arquivo = f"output_frames/frame_{timestamp}.png"
        imagem.save(caminho_do_arquivo, "PNG")

        print(f"Frame salvo em {caminho_do_arquivo}")

        return {
            "status": "Sucesso",
            "mensagem": f"Frame salvo em {caminho_do_arquivo}",
            "tamanho_imagem": imagem.size,
        }

    except Exception as e:
        print(f"Erro: {e}")
        return {"status": "erro", "mensagem": str(e)}

# endpoint de tradução (mock)
@app.get("/translate")
def get_translation():
    return {"translation": "By the way"}

# endpoint raiz
@app.get("/")
def read_root():
    return {"Mensagem": "Servidor online"}
