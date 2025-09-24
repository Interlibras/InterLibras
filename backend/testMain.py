import cv2
import mediapipe as mp
import math
import numpy as np
import os
from dtw import dtw

# ================================
# CONFIGURAÇÕES GERAIS
# ================================
DATA_DIR = "dataset_libras"
MAX_FRAMES = 30
LIMIAR_DTW = 5.0  # Ajuste conforme seus testes

# ================================
# INICIALIZAÇÃO MEDIAPIPE
# ================================
mp_maos = mp.solutions.hands
mp_desenho = mp.solutions.drawing_utils
maos = mp_maos.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)

# ================================
# WEBCAM
# ================================
cap = cv2.VideoCapture(0)

# ================================
# CARREGA DATASET DE SINAIS GRAVADOS
# ================================
dataset = []  # (sequencia, label)

if os.path.exists(DATA_DIR):
    for label in os.listdir(DATA_DIR):
        label_path = os.path.join(DATA_DIR, label)
        if os.path.isdir(label_path):
            for arquivo in os.listdir(label_path):
                if arquivo.endswith(".npy"):
                    caminho = os.path.join(label_path, arquivo)
                    sequencia = np.load(caminho)
                    dataset.append((sequencia, label))
    print(f"✅ Carregados {len(dataset)} sinais de {len(set(d[1] for d in dataset))} classes.")
else:
    print("⚠️ Nenhum dado gravado encontrado. Grave sinais primeiro com a tecla 'g'.")

# ================================
# VARIÁVEIS DE CONTROLE
# ================================
gravando = False
reconhecendo = False
buffer_gravacao = []
buffer_reconhecimento = []
classe_atual = ""
ultima_palavra_reconhecida = "Aguardando..."
ultima_distancia = ""
ultima_letra_estatica = "N/D"

# ================================
# FUNÇÕES AUXILIARES
# ================================

def get_distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def get_3d_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def identificar_letra_libras(landmarks_mao, mao_rotulo):
    dedos_estendidos_sem_polegar = []
    pontas_dedos_ids = [4, 8, 12, 16, 20]
    
    polegar_estendido_lateralmente = False
    if mao_rotulo == "Right":
        if landmarks_mao.landmark[pontas_dedos_ids[0]].x < landmarks_mao.landmark[pontas_dedos_ids[0] - 2].x:
            polegar_estendido_lateralmente = True
    elif mao_rotulo == "Left":
        if landmarks_mao.landmark[pontas_dedos_ids[0]].x > landmarks_mao.landmark[pontas_dedos_ids[0] - 2].x:
            polegar_estendido_lateralmente = True

    for id_ponta in pontas_dedos_ids[1:]:
        if landmarks_mao.landmark[id_ponta].y < landmarks_mao.landmark[id_ponta - 2].y:
            dedos_estendidos_sem_polegar.append(True)
        else:
            dedos_estendidos_sem_polegar.append(False)

    index_extended_down = landmarks_mao.landmark[8].y > landmarks_mao.landmark[7].y and landmarks_mao.landmark[7].y > landmarks_mao.landmark[6].y and landmarks_mao.landmark[6].y > landmarks_mao.landmark[5].y
    middle_extended_down = landmarks_mao.landmark[12].y > landmarks_mao.landmark[11].y and landmarks_mao.landmark[11].y > landmarks_mao.landmark[10].y and landmarks_mao.landmark[10].y > landmarks_mao.landmark[9].y
    ring_extended_down = landmarks_mao.landmark[16].y > landmarks_mao.landmark[15].y and landmarks_mao.landmark[15].y > landmarks_mao.landmark[14].y and landmarks_mao.landmark[14].y > landmarks_mao.landmark[13].y
    pinky_extended_down = landmarks_mao.landmark[20].y > landmarks_mao.landmark[19].y and landmarks_mao.landmark[19].y > landmarks_mao.landmark[18].y and landmarks_mao.landmark[18].y > landmarks_mao.landmark[17].y

    if not polegar_estendido_lateralmente:
        thumb_tucked_for_mn = landmarks_mao.landmark[4].y > landmarks_mao.landmark[9].y and landmarks_mao.landmark[4].y > landmarks_mao.landmark[13].y
        if thumb_tucked_for_mn:
            if index_extended_down and middle_extended_down and ring_extended_down and pinky_extended_down:
                return "M"
            if index_extended_down and middle_extended_down and not ring_extended_down and not pinky_extended_down:
                return "N"

    dedos_estendidos_com_polegar = [polegar_estendido_lateralmente] + dedos_estendidos_sem_polegar
    total_dedos_estendidos = dedos_estendidos_com_polegar.count(True)

    hand_ruler_distance = get_distance(landmarks_mao.landmark[0], landmarks_mao.landmark[9])
    dist_thumb_to_fingers = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[8])
    normalized_o_distance = dist_thumb_to_fingers / hand_ruler_distance

    thumb_is_over_fingers = landmarks_mao.landmark[4].y < landmarks_mao.landmark[5].y and landmarks_mao.landmark[4].y < landmarks_mao.landmark[8].y

    is_hand_closed = False
    if landmarks_mao:
        wrist = landmarks_mao.landmark[0]
        thumb_tip = landmarks_mao.landmark[4]
        thumb_mcp = landmarks_mao.landmark[2]
        index_tip = landmarks_mao.landmark[8]
        index_mcp = landmarks_mao.landmark[5]
        middle_tip = landmarks_mao.landmark[12]
        middle_mcp = landmarks_mao.landmark[9]
        ring_tip = landmarks_mao.landmark[16]
        ring_mcp = landmarks_mao.landmark[13]
        pinky_tip = landmarks_mao.landmark[20]
        pinky_mcp = landmarks_mao.landmark[17]

        thumb_is_curled = get_3d_distance(thumb_tip, wrist) < get_3d_distance(thumb_mcp, wrist)
        index_is_curled = get_3d_distance(index_tip, wrist) < get_3d_distance(index_mcp, wrist)
        middle_is_curled = get_3d_distance(middle_tip, wrist) < get_3d_distance(middle_mcp, wrist)
        ring_is_curled = get_3d_distance(ring_tip, wrist) < get_3d_distance(ring_mcp, wrist)
        pinky_is_curled = get_3d_distance(pinky_tip, wrist) < get_3d_distance(pinky_mcp, wrist)

        if thumb_is_curled and index_is_curled and middle_is_curled and ring_is_curled and pinky_is_curled:
            is_hand_closed = True

    if (normalized_o_distance < 0.5 and
        not any(dedos_estendidos_sem_polegar) and not
        thumb_is_over_fingers and not is_hand_closed):
        return "O"

    if total_dedos_estendidos == 4 and not polegar_estendido_lateralmente:
        return "B"
    
    if dedos_estendidos_com_polegar == [True, False, False, False, True]:
        return "Y"

    if dedos_estendidos_com_polegar == [False, True, True, True, False]:
        return "W"
        
    if dedos_estendidos_com_polegar == [True, True, False, False, False]:
        return "L"

    if dedos_estendidos_com_polegar == [False, False, False, False, True]:
        return "I"

    if dedos_estendidos_com_polegar == [False, True, True, False, False]:
        dist_index_middle = get_distance(landmarks_mao.landmark[8], landmarks_mao.landmark[12])
        dist_thumb_middle = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[12])

        if dist_thumb_middle < 0.07:
             return "K"

        if mao_rotulo == "Right" and landmarks_mao.landmark[8].x > landmarks_mao.landmark[12].x:
            return "R"
        if mao_rotulo == "Left" and landmarks_mao.landmark[8].x < landmarks_mao.landmark[12].x:
            return "R"

        if dist_index_middle > 0.07:
            return "V"
        else:
            return "U"
            
    if all(dedos_estendidos_sem_polegar[1:]) and not dedos_estendidos_sem_polegar[0]:
        dist_thumb_index = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[8])
        if dist_thumb_index < 0.07:
            return "F"

    if dedos_estendidos_com_polegar == [False, True, False, False, False]:
        index_tip = landmarks_mao.landmark[8]
        index_mcp = landmarks_mao.landmark[5]

        if abs(index_tip.x - index_mcp.x) > abs(index_tip.y - index_mcp.y):
            return "G"
        
        if index_tip.y > index_mcp.y:
            return "Q"
        
        dist_thumb_middle = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[12])
        if dist_thumb_middle < 0.1:
             return "D"
        
        if index_tip.y > landmarks_mao.landmark[6].y:
            return "X"

    if not any(dedos_estendidos_sem_polegar):
        if polegar_estendido_lateralmente:
            return "A"
        else:
            thumb_tip = landmarks_mao.landmark[4]
            index_pip = landmarks_mao.landmark[6]
            middle_pip = landmarks_mao.landmark[10]
            index_mcp = landmarks_mao.landmark[5]

            is_t = (thumb_tip.x > index_pip.x and thumb_tip.x < middle_pip.x) or \
                   (thumb_tip.x < index_pip.x and thumb_tip.x > middle_pip.x)
            if is_t:
                return "T"

            is_s = thumb_tip.y < index_pip.y and thumb_tip.y < middle_pip.y
            if is_s:
                return "S"

            return "E"

    # LETRA H
    if dedos_estendidos_com_polegar == [False, True, True, False, False]:
        y_index = landmarks_mao.landmark[8].y
        y_middle = landmarks_mao.landmark[12].y
        x_index = landmarks_mao.landmark[8].x
        x_middle = landmarks_mao.landmark[12].x

        if abs(y_index - y_middle) < 0.03 and abs(x_index - x_middle) > 0.05:
            pulso_x = landmarks_mao.landmark[0].x
            if mao_rotulo == "Right":
                if x_index > pulso_x + 0.05:
                    return "H"
            else:
                if x_index < pulso_x - 0.05:
                    return "H"

    # LETRA J
    if dedos_estendidos_com_polegar == [False, False, False, False, True]:
        tip_y = landmarks_mao.landmark[20].y
        pip_y = landmarks_mao.landmark[19].y
        tip_x = landmarks_mao.landmark[20].x
        pip_x = landmarks_mao.landmark[19].x

        if tip_y > pip_y + 0.02:
            return "J"

        if mao_rotulo == "Right" and tip_x < pip_x - 0.03:
            return "J"
        if mao_rotulo == "Left" and tip_x > pip_x + 0.03:
            return "J"

    # LETRA P
    if dedos_estendidos_com_polegar == [True, True, True, False, False]:
        index_tip = landmarks_mao.landmark[8]
        middle_tip = landmarks_mao.landmark[12]
        wrist = landmarks_mao.landmark[0]

        if index_tip.y > landmarks_mao.landmark[5].y and middle_tip.y > landmarks_mao.landmark[9].y:
            if wrist.y < index_tip.y - 0.1:
                dist_thumb_index = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[8])
                if dist_thumb_index < 0.1:
                    return "P"

    # LETRA Z
    if dedos_estendidos_com_polegar == [True, True, False, False, False] or \
       dedos_estendidos_com_polegar == [False, True, False, False, False]:

        index_tip = landmarks_mao.landmark[8]
        index_mcp = landmarks_mao.landmark[5]
        thumb_tip = landmarks_mao.landmark[4]

        dx = index_tip.x - index_mcp.x
        dy = index_tip.y - index_mcp.y

        if abs(dx) > 0.05 and abs(dy) > 0.05:
            dist_thumb_to_index_side = abs(thumb_tip.x - index_mcp.x) + abs(thumb_tip.y - index_tip.y)
            if dist_thumb_to_index_side < 0.15:
                return "Z"

    return "NAO IDENTIFICADO"

# ================================
# LOOP PRINCIPAL
# ================================
while True:
    sucesso, imagem = cap.read()
    if not sucesso:
        continue

    altura, largura, _ = imagem.shape
    imagem = cv2.flip(imagem, 1)
    imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
    resultados = maos.process(imagem_rgb)
    imagem = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2BGR)

    # Processa landmarks se detectados
    if resultados.multi_hand_landmarks:
        for mao_idx, landmarks_mao in enumerate(resultados.multi_hand_landmarks):
            mp_desenho.draw_landmarks(
                imagem,
                landmarks_mao,
                mp_maos.HAND_CONNECTIONS,
                mp_desenho.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=3),
                mp_desenho.DrawingSpec(color=(255,0,0), thickness=2)
            )

            # === RECONHECIMENTO ESTÁTICO (LETRAS) ===
            mao_rotulo = resultados.multi_handedness[mao_idx].classification[0].label
            letra_estatica = identificar_letra_libras(landmarks_mao, mao_rotulo)
            ultima_letra_estatica = letra_estatica

            # Mostra letra estática perto da mão
            pulso = landmarks_mao.landmark[0]
            pos_x = int(pulso.x * largura)
            pos_y = int(pulso.y * altura)
            cv2.putText(imagem, letra_estatica, (pos_x - 50, pos_y - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3, cv2.LINE_AA)

            # === EXTRAÇÃO PARA RECONHECIMENTO DINÂMICO ===
            wrist = landmarks_mao.landmark[0]
            frame_data = []
            for lm in landmarks_mao.landmark:
                frame_data.extend([
                    lm.x - wrist.x,
                    lm.y - wrist.y,
                    lm.z - wrist.z
                ])

            # Modo GRAVAÇÃO
            if gravando:
                buffer_gravacao.append(frame_data)
                if len(buffer_gravacao) >= MAX_FRAMES:
                    pasta_classe = os.path.join(DATA_DIR, classe_atual)
                    os.makedirs(pasta_classe, exist_ok=True)
                    nome_arquivo = f"{len(os.listdir(pasta_classe)) + 1}.npy"
                    caminho = os.path.join(pasta_classe, nome_arquivo)
                    np.save(caminho, np.array(buffer_gravacao))
                    print(f"💾 Salvo: {caminho}")
                    # Recarrega dataset
                    dataset = []
                    for label in os.listdir(DATA_DIR):
                        label_path = os.path.join(DATA_DIR, label)
                        if os.path.isdir(label_path):
                            for arquivo in os.listdir(label_path):
                                if arquivo.endswith(".npy"):
                                    caminho_load = os.path.join(label_path, arquivo)
                                    sequencia = np.load(caminho_load)
                                    dataset.append((sequencia, label))
                    print(f"🔁 Dataset recarregado: {len(dataset)} sinais.")
                    gravando = False
                    buffer_gravacao = []

            # Modo RECONHECIMENTO
            if reconhecendo:
                buffer_reconhecimento.append(frame_data)
                if len(buffer_reconhecimento) >= MAX_FRAMES:
                    sequencia_atual = np.array(buffer_reconhecimento)

                    melhor_distancia = float('inf')
                    melhor_label = "NENHUM"

                    for sequencia_treino, label in dataset:
                        if sequencia_treino.shape[1] != sequencia_atual.shape[1]:
                            continue
                        try:
                            distancia, _, _, _ = dtw(
                                sequencia_treino,
                                sequencia_atual,
                                dist=lambda x, y: np.linalg.norm(np.array(x) - np.array(y))
                            )
                            if distancia < melhor_distancia:
                                melhor_distancia = distancia
                                melhor_label = label
                        except Exception as e:
                            print("Erro no DTW:", e)
                            continue

                    if melhor_distancia < LIMIAR_DTW:
                        ultima_palavra_reconhecida = melhor_label
                        ultima_distancia = f"{melhor_distancia:.2f}"
                        print(f"✅ Reconhecido: {melhor_label} (dist: {melhor_distancia:.2f})")
                    else:
                        ultima_palavra_reconhecida = "Desconhecido"
                        ultima_distancia = f"{melhor_distancia:.2f}"
                        print(f"❌ Não reconhecido (dist: {melhor_distancia:.2f})")

                    reconhecendo = False
                    buffer_reconhecimento = []

    # Controles por teclado
    key = cv2.waitKey(1) & 0xFF

    if key == ord('g'):
        classe_atual = input("\n📝 Digite o nome do sinal a gravar (ex: OI, AGUA, TCHAU): ").strip()
        if classe_atual:
            buffer_gravacao = []
            gravando = True
            print(f"⏺️  Iniciando gravação de '{classe_atual}'... Faça o sinal lentamente.")

    if key == ord('r'):
        buffer_reconhecimento = []
        reconhecendo = True
        print("🔍 Iniciando reconhecimento... Faça o sinal.")

    if key == ord('c'):
        ultima_palavra_reconhecida = "Aguardando..."
        ultima_distancia = ""

    if key == ord('q'):
        break

    # Exibe interface
    cv2.rectangle(imagem, (10, 10), (600, 180), (50, 50, 50), -1)
    cv2.putText(imagem, f"Letra Estática: {ultima_letra_estatica}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(imagem, f"Sinal Dinâmico: {ultima_palavra_reconhecida}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if ultima_palavra_reconhecida != "Desconhecido" and ultima_palavra_reconhecida != "Aguardando..." else (0, 0, 255), 2)
    cv2.putText(imagem, f"Distância: {ultima_distancia}", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    status = ""
    if gravando:
        status = f"GRAVANDO: {classe_atual} ({len(buffer_gravacao)}/{MAX_FRAMES})"
        cv2.putText(imagem, status, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    elif reconhecendo:
        status = f"RECONHECENDO ({len(buffer_reconhecimento)}/{MAX_FRAMES})"
        cv2.putText(imagem, status, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.putText(imagem, "Teclas: G=Gravar sinal, R=Reconhecer sinal, C=Limpar, Q=Sair", (20, altura - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("Tradutor Híbrido de Libras (Estático + Dinâmico)", imagem)

# Libera recursos
cap.release()
cv2.destroyAllWindows()

#==========================================
#Execute:
#   bash
#   python tradutor_libras_hibrido.py
#
#   1
#   python tradutor_libras_hibrido.py
#   2 - Para soletrar → apenas mantenha as mãos em posições de letras. A letra aparecerá amarela perto da mão.
#   3 - Para gravar um sinal com movimento:
#   Pressione g
#   Digite o nome (ex: OI)
#   Faça o sinal completo (30 frames)
#   4 - Para reconhecer:
#   Pressione r
#
#   Faça o sinal → se reconhecido, aparece em verde; se não, em vermelho.
#=========================================
