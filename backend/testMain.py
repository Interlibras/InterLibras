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
cap = cv2.VideoCapture(1)

#procura cameras disponiveis:
def list_cameras():
    index = 1
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(index)
        cap.release()
        index += 1
    return arr

print("Câmeras detectadas:", list_cameras())

# Substitua pelo IP e porta do seu celular (veja no app do Oriun/DroidCam)
url = "http://192.168.0.10:4747/video"  # <-- ajustavel
cap = cv2.VideoCapture(url)

if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        cv2.imshow('Câmera do celular', frame)
        cv2.waitKey(0)
else:
    print("Não foi possível conectar à câmera via rede.")

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
    #variaveis
    pontas_dedos_ids = [4, 8, 12, 16, 20]

    wrist = landmarks_mao.landmark[0]
    thumb_mcp = landmarks_mao.landmark[2]
    thumb_pip = landmarks_mao.landmark[3]
    thumb_tip = landmarks_mao.landmark[4]
    index_mcp = landmarks_mao.landmark[5]
    index_pip = landmarks_mao.landmark[6]
    index_dip = landmarks_mao.landmark[7]
    index_tip = landmarks_mao.landmark[8]
    middle_mcp = landmarks_mao.landmark[9]
    middle_pip = landmarks_mao.landmark[10]
    middle_dip = landmarks_mao.landmark[11]
    middle_tip = landmarks_mao.landmark[12]
    ring_mcp = landmarks_mao.landmark[13]
    ring_pip = landmarks_mao.landmark[14]
    ring_dip = landmarks_mao.landmark[15]
    ring_tip = landmarks_mao.landmark[16]
    pinky_mcp = landmarks_mao.landmark[17]
    pinky_pip = landmarks_mao.landmark[18]
    pinky_dip = landmarks_mao.landmark[19]
    pinky_tip = landmarks_mao.landmark[20]

    pulso_x = wrist.x
    x_index = index_tip.x
    y_index = index_tip.y
    x_middle = middle_tip.x
    y_middle = middle_tip.y
    pinky_tip_x = pinky_tip.x
    pinky_tip_y = pinky_tip.y
    pinky_pip_x = pinky_pip.x
    pinky_pip_y = pinky_pip.y
    #variaveis

    is_hand_upside_down = middle_mcp.y > wrist.y

    dedos_estendidos_sem_polegar = []
    for id_ponta in pontas_dedos_ids[1:]:
        tip = landmarks_mao.landmark[id_ponta]
        pip_joint = landmarks_mao.landmark[id_ponta - 2]
        
        is_extended = False
        if is_hand_upside_down:
            is_extended = tip.y > pip_joint.y
        else:
            is_extended = tip.y < pip_joint.y
        dedos_estendidos_sem_polegar.append(is_extended)

    polegar_estendido_lateralmente = False
    if mao_rotulo == "Right":
        if thumb_tip.x < thumb_pip.x:
            polegar_estendido_lateralmente = True
    elif mao_rotulo == "Left":
        if thumb_tip.x > thumb_pip.x:
            polegar_estendido_lateralmente = True

    index_is_down = index_tip.y > index_pip.y
    middle_is_down = middle_tip.y > middle_pip.y
    ring_is_down = ring_tip.y > ring_pip.y


    dedos_estendidos_com_polegar = [polegar_estendido_lateralmente] + dedos_estendidos_sem_polegar
    total_dedos_estendidos = dedos_estendidos_com_polegar.count(True)

    hand_ruler_distance = get_distance(wrist, middle_mcp)
    dist_thumb_to_fingers = get_distance(thumb_tip, index_tip)
    normalized_o_distance = dist_thumb_to_fingers / hand_ruler_distance if hand_ruler_distance > 0 else 0

    thumb_is_over_fingers = thumb_tip.y < index_mcp.y and thumb_tip.y < index_tip.y

    thumb_is_curled = get_3d_distance(thumb_tip, wrist) < get_3d_distance(thumb_mcp, wrist)
    index_is_curled = get_3d_distance(index_tip, wrist) < get_3d_distance(index_mcp, wrist)
    middle_is_curled = get_3d_distance(middle_tip, wrist) < get_3d_distance(middle_mcp, wrist)
    ring_is_curled = get_3d_distance(ring_tip, wrist) < get_3d_distance(ring_mcp, wrist)
    pinky_is_curled = get_3d_distance(pinky_tip, wrist) < get_3d_distance(pinky_mcp, wrist)

    is_hand_closed = thumb_is_curled and index_is_curled and middle_is_curled and ring_is_curled and pinky_is_curled

    four_fingers_are_curved = (index_tip.y > index_mcp.y and
                               middle_tip.y > middle_mcp.y and
                               ring_tip.y > ring_mcp.y and
                               pinky_tip.y > pinky_mcp.y)

    thumb_is_curved = thumb_tip.y > thumb_pip.y and thumb_tip.x < thumb_pip.x if mao_rotulo == 'Right' else thumb_tip.x > thumb_pip.x

    knuckles_x_span = abs(index_mcp.x - pinky_mcp.x)
    middle_mcp_wrist_distance = get_distance(middle_mcp, wrist)
    is_sideways = (knuckles_x_span / middle_mcp_wrist_distance) < 0.35 if middle_mcp_wrist_distance > 0 else False

    no_fingers_extended = not any(dedos_estendidos_sem_polegar)

    dist_thumb_to_index = get_distance(thumb_tip, index_tip)
    normalized_o_c_dist = dist_thumb_to_index / hand_ruler_distance if hand_ruler_distance > 0 else 0

    is_curved_shape = (not any(dedos_estendidos_sem_polegar) and
                       not thumb_is_over_fingers and
                       not is_hand_closed)

    hand_is_upside_down = middle_mcp.y > wrist.y

    if hand_is_upside_down:
        index_points_down = index_tip.y > index_pip.y
        middle_points_down = middle_tip.y > middle_pip.y
        pinky_is_curled = pinky_tip.y < pinky_pip.y
        thumb_is_tucked = thumb_tip.y > index_mcp.y and not polegar_estendido_lateralmente

        if index_points_down and middle_points_down and pinky_is_curled and thumb_is_tucked:
            ring_points_down = ring_tip.y > ring_pip.y
            
            if ring_points_down:
                return "M"
            else:
                return "N"

    dist_index_mcp_tip = get_distance(index_mcp, index_tip)
    normalized_dist_index_mcp_tip = dist_index_mcp_tip / hand_ruler_distance if hand_ruler_distance > 0 else 0

    if is_curved_shape and normalized_dist_index_mcp_tip > 0.2 and is_sideways == True:
        if normalized_o_c_dist > 0.35:
            return "C"
        elif normalized_o_c_dist < 0.35:
            return "O"

    dist_thumb_to_index_mcp = get_distance(thumb_tip, index_mcp)
        
    normalized_thumb_dist = dist_thumb_to_index_mcp / hand_ruler_distance if hand_ruler_distance > 0 else 0

    dist_index_tip_to_base = get_distance(index_tip, index_mcp)
    index_is_partially_foreshortened = dist_index_tip_to_base < (hand_ruler_distance * 0.8)
    middle_points_down = middle_tip.y > middle_pip.y
    fist_is_formed = (ring_tip.y > ring_mcp.y) and (pinky_tip.y > pinky_mcp.y)
    dist_thumb_to_middle_knuckle = get_distance(thumb_tip, middle_pip)
    thumb_is_locked = dist_thumb_to_middle_knuckle < (hand_ruler_distance * 0.65)
    middle_is_lowest = middle_tip.y > index_tip.y and middle_tip.y > ring_tip.y

    if index_is_partially_foreshortened and middle_points_down and fist_is_formed and thumb_is_locked and middle_is_lowest:
        return "P"

    is_Y_finger_pattern = (dedos_estendidos_com_polegar == [True, False, False, False, True])
    if is_Y_finger_pattern:
        middle_is_curled_in_fist = middle_tip.y > middle_mcp.y
        if middle_is_curled_in_fist:
            return "Y"

    if total_dedos_estendidos == 4 and not polegar_estendido_lateralmente and not is_hand_upside_down:
        return "B"

    if dedos_estendidos_com_polegar == [False, True, True, True, False]:
        return "W"
    
    if dedos_estendidos_com_polegar == [True, True, False, False, False] and normalized_thumb_dist > 0.4 and not is_sideways:
        return "L"

    if dedos_estendidos_com_polegar == [True, True, False, False, False] and normalized_thumb_dist < 0.4 and not is_sideways and not is_hand_upside_down:
        return "G"

    is_only_pinky_up = (dedos_estendidos_sem_polegar == [False, False, False, True])
    index_curled_tight = index_tip.y > index_mcp.y
    middle_curled_tight = middle_tip.y > middle_mcp.y
    ring_curled_tight = ring_tip.y > ring_mcp.y
    thumb_is_tucked = not polegar_estendido_lateralmente

    if is_only_pinky_up and index_curled_tight and middle_curled_tight and ring_curled_tight and thumb_is_tucked:
        return "I"

    if dedos_estendidos_com_polegar == [False, True, True, False, False]:
        dist_index_middle = get_distance(index_tip, middle_tip)
        dist_thumb_middle = get_distance(thumb_tip, middle_tip)

        if dist_thumb_middle < 0.07:
             return "K"

        if mao_rotulo == "Right" and x_index > x_middle:
            return "R"
        if mao_rotulo == "Left" and x_index < x_middle:
            return "R"

        if dist_index_middle > 0.07:
            return "V"
        else:
            return "U"
            
    three_fingers_up = dedos_estendidos_sem_polegar[1] and dedos_estendidos_sem_polegar[2] and dedos_estendidos_sem_polegar[3]
    if mao_rotulo == "Right": 
        thumb_left_index = thumb_pip.x < index_tip.x
    else:
        thumb_left_index = thumb_pip.x > index_tip.x

    if three_fingers_up and thumb_left_index and not dedos_estendidos_sem_polegar[0]:
        return "F"

    if dedos_estendidos_com_polegar == [False, True, False, False, False]:
        dist_thumb_middle = get_distance(middle_tip, thumb_tip)
        if dist_thumb_middle < 0.1 and not is_hand_upside_down:
             return "D"

        if index_tip.y > index_mcp.y and is_hand_upside_down:
            return "Q"

    if not any(dedos_estendidos_sem_polegar):
        if polegar_estendido_lateralmente:
            is_upright = wrist.y > middle_mcp.y
            is_facing_forward = False
            if mao_rotulo == 'Right':
                is_facing_forward = index_mcp.x < pinky_mcp.x
            else:
                is_facing_forward = index_mcp.x > pinky_mcp.x
            if is_upright and is_facing_forward:
                return "A"
        else:
            thumb_is_between_fingers = (thumb_tip.x > index_mcp.x)
            thumb_is_tucked = thumb_tip.y > index_pip.y

            thumb_is_over_fingers = thumb_tip.y < index_pip.y + (0.02 / hand_ruler_distance if hand_ruler_distance > 0 else 0)
            if thumb_is_over_fingers and index_curled_tight:
                return "S"
            
            all_fingers_are_curled = (index_tip.y > index_pip.y and
                                      middle_tip.y > middle_pip.y and
                                      ring_tip.y > ring_pip.y and
                                      pinky_tip.y > pinky_pip.y)
            if all_fingers_are_curled:
                return "E"

    three_fingers_up = dedos_estendidos_sem_polegar[1] and dedos_estendidos_sem_polegar[2] and dedos_estendidos_sem_polegar[3]
    if mao_rotulo == "Right": 
        thumb_left_index = thumb_pip.x > index_tip.x
    else:
        thumb_left_index = thumb_pip.x < index_tip.x

    if three_fingers_up and thumb_left_index and not dedos_estendidos_sem_polegar[0]:
        return "T"

    if dedos_estendidos_com_polegar == [False, True, True, False, False]:
        if abs(y_index - y_middle) < 0.03 and abs(x_index - x_middle) > 0.05:
            if mao_rotulo == "Right":
                if x_index > pulso_x + 0.05:
                    return "H"
            else:
                if x_index < pulso_x - 0.05:
                    return "H"

    if dedos_estendidos_com_polegar == [False, False, False, False, True]:
        if pinky_tip_y > pinky_pip_y + 0.02:
            return "J"
        if mao_rotulo == "Right" and pinky_tip_x < pinky_pip_x - 0.03:
            return "J"
        if mao_rotulo == "Left" and pinky_tip_x > pinky_pip_x + 0.03:
            return "J"

    if dedos_estendidos_com_polegar == [True, True, False, False, False] or \
       dedos_estendidos_com_polegar == [False, True, False, False, False]:
        dx = x_index - index_mcp.x
        dy = y_index - index_mcp.y

        if abs(dx) > 0.05 and abs(dy) > 0.05:
            dist_thumb_to_index_side = abs(thumb_tip.x - index_mcp.x) + abs(thumb_tip.y - y_index)
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

    if resultados.multi_hand_landmarks:
        for mao_idx, landmarks_mao in enumerate(resultados.multi_hand_landmarks):
            mp_desenho.draw_landmarks(
                imagem,
                landmarks_mao,
                mp_maos.HAND_CONNECTIONS,
                mp_desenho.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=3),
                mp_desenho.DrawingSpec(color=(255,0,0), thickness=2)
            )

            mao_rotulo = resultados.multi_handedness[mao_idx].classification[0].label
            letra_estatica = identificar_letra_libras(landmarks_mao, mao_rotulo)
            ultima_letra_estatica = letra_estatica

            pulso = landmarks_mao.landmark[0]
            pos_x = int(pulso.x * largura)
            pos_y = int(pulso.y * altura)
            cv2.putText(imagem, letra_estatica, (pos_x - 50, pos_y - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3, cv2.LINE_AA)

            wrist_lm = landmarks_mao.landmark[0]
            frame_data = []
            for lm in landmarks_mao.landmark:
                frame_data.extend([
                    lm.x - wrist_lm.x,
                    lm.y - wrist_lm.y,
                    lm.z - wrist_lm.z
                ])

            if gravando:
                buffer_gravacao.append(frame_data)
                if len(buffer_gravacao) >= MAX_FRAMES:
                    pasta_classe = os.path.join(DATA_DIR, classe_atual)
                    os.makedirs(pasta_classe, exist_ok=True)
                    nome_arquivo = f"{len(os.listdir(pasta_classe)) + 1}.npy"
                    caminho = os.path.join(pasta_classe, nome_arquivo)
                    np.save(caminho, np.array(buffer_gravacao))
                    print(f"💾 Salvo: {caminho}")
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

cap.release()
cv2.destroyAllWindows()