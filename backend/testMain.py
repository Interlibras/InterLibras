#importando bibliotecas
# 1. Mediapipe
# 2. OpenCV

import cv2
import mediapipe as mp
import numpy as np

mp_maos = mp.solutions.hands
mp_desenho = mp.solutions.drawing_utils
maos = mp_maos.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

def identificar_gesto(landmarks_mao):
    dedos_levantados = []
    pontas_dedos_ids = [4, 8, 12, 16, 20]

    if landmarks_mao.landmark[pontas_dedos_ids[0]].x < landmarks_mao.landmark[pontas_dedos_ids[0] - 1].x:
        dedos_levantados.append(True)
    else:
        dedos_levantados.append(False)

    for id_ponta in pontas_dedos_ids[1:]:
        if landmarks_mao.landmark[id_ponta].y < landmarks_mao.landmark[id_ponta - 2].y:
            dedos_levantados.append(True)
        else:
            dedos_levantados.append(False)

    total_dedos = dedos_levantados.count(True)

    if all(dedos_levantados):
        return "MAO ABERTA"
    elif not any(dedos_levantados):
        return "MAO FECHADA"
    elif dedos_levantados == [True, False, False, False, False]:
        return "JOINHA"
    elif dedos_levantados == [False, True, True, False, False]:
        return "PAZ E AMOR"
    else:
        return f"{total_dedos} DEDOS"


while True:
    sucesso, imagem = cap.read()
    if not sucesso:
        print("Ignorando frame vazio da câmera.")
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
                mp_maos.HAND_CONNECTIONS
            )

            gesto = identificar_gesto(landmarks_mao)

            pulso = landmarks_mao.landmark[0]
            pos_x = int(pulso.x * largura)
            pos_y = int(pulso.y * altura)

            cv2.putText(imagem, gesto, (pos_x - 50, pos_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("Detector de Gestos", imagem)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()