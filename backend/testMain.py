import cv2
import mediapipe as mp
import math

mp_maos = mp.solutions.hands
mp_desenho = mp.solutions.drawing_utils
maos = mp_maos.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

def get_distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

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

    if normalized_o_distance < 0.5 and not any(dedos_estendidos_sem_polegar):
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

    return "NAO IDENTIFICADO"

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
                mp_maos.HAND_CONNECTIONS
            )

            mao_rotulo = resultados.multi_handedness[mao_idx].classification[0].label
            letra = identificar_letra_libras(landmarks_mao, mao_rotulo)

            pulso = landmarks_mao.landmark[0]
            pos_x = int(pulso.x * largura)
            pos_y = int(pulso.y * altura)

            cv2.putText(imagem, letra, (pos_x - 50, pos_y - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)

    cv2.imshow("Tradutor de Libras (Alfabeto)", imagem)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()