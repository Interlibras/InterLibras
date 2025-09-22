# main.py

#depois podemos fazer com que mais de um usuário possa usar ao mesmo tempo

import base64
import io
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from datetime import datetime

# diretorio para salvar os frames que são recebidos
if not os.path.exists("output_frames"):
    os.makedirs("output_frames")

# fast api é tipo o express
app = FastAPI()

# configurando o cors para deixar o backend se comunicar com o frontend
# as origens
origins = [
    "http://localhost",
    "http://localhost:3000",
]
# o cors adicionado
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# define o modelo que o frontend deve mandar é um json com um atributo frame que tem uma string (que no nosso caso seria uma imagem encodificada em base64)
class VideoFrame(BaseModel):
    frame: str

# o endpoint post para o envio do video da camera do usuário
@app.post("/frame")
async def process_video_frame(data: VideoFrame):
    """
    Recebe um frame em base64 e o salva
    """
    try:
        # isso pega só a parte relevante
        header, encoded = data.frame.split(",", 1)
        
        # transforma em bytes para pode salvar como imagem mesmo
        dados_imagem = base64.b64decode(encoded)
        
        # cria a imagem usando a biblioteca pillow
        imagem = Image.open(io.BytesIO(dados_imagem))
        
        # salva a imagem e por enquanto coloca o nome como o tempo em que foi tirada
        # depois poderiamos colocar um sistema de login para vários usuários poderem usar ao mesmo tempo ou algum outro sistema tipo pedir o id da maquina ou algum tipo de id para diferenciar os usuários.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        caminho_do_arquivo = f"output_frames/frame_{timestamp}.png"
        imagem.save(caminho_do_arquivo, "PNG")

        print(f"Frame salvo em {caminho_do_arquivo}")

        return {
            "status": "Successo",
            "mensagem": f"Frame salvo em {caminho_do_arquivo}",
            "tamanho_imagem": imagem.size
        }
        
    except Exception as e:
        print(f"Erro: {e}")
        return {"status": "erro", "mensagem": str(e)}

@app.get("/")
def read_root():
    return {"Mensagem":"Servidor online"}