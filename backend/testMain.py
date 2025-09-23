#importando bibliotecas
# 1. Mediapipe
# 2. OpenCV

import cv2
import mediapipe as mp

mp_maos = mp.solutions.hands
mp_desenho = mp.solutions.drawing_utils
maos = mp_maos.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

while True:
    sucesso, imagem = cap.read()
    if not sucesso:
        print("Ignorando frame vazio da câmera.")
        continue

    imagem = cv2.flip(imagem, 1)
    imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)

    resultados = maos.process(imagem_rgb)

    imagem = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2BGR)

    if resultados.multi_hand_landmarks:
        for landmarks_mao in resultados.multi_hand_landmarks:
            mp_desenho.draw_landmarks(
                imagem,
                landmarks_mao,
                mp_maos.HAND_CONNECTIONS
            )

    cv2.imshow("Detector de Mãos - MediaPipe", imagem)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()