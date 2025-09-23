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

    # Corrigido: O índice do dedo mindinho é 3 na lista 'dedos_estendidos_sem_polegar'
    is_m = not polegar_estendido_lateralmente and \
           landmarks_mao.landmark[8].y > landmarks_mao.landmark[5].y and \
           landmarks_mao.landmark[12].y > landmarks_mao.landmark[9].y and \
           landmarks_mao.landmark[16].y > landmarks_mao.landmark[13].y and \
           not dedos_estendidos_sem_polegar[3]

    is_n = not polegar_estendido_lateralmente and \
           landmarks_mao.landmark[8].y > landmarks_mao.landmark[5].y and \
           landmarks_mao.landmark[12].y > landmarks_mao.landmark[9].y and \
           landmarks_mao.landmark[16].y < landmarks_mao.landmark[13].y and \
           not dedos_estendidos_sem_polegar[3]
           
    if is_m:
        return "M"
    if is_n:
        return "N"

    dedos_estendidos_com_polegar = [polegar_estendido_lateralmente] + dedos_estendidos_sem_polegar
    total_dedos_estendidos = dedos_estendidos_com_polegar.count(True)

    if total_dedos_estendidos == 4 and not dedos_estendidos_com_polegar[0]:
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
            index_tip_y = landmarks_mao.landmark[8].y
            index_mcp_y = landmarks_mao.landmark[5].y
            if index_tip_y < index_mcp_y:
                return "C"
            else:
                return "A"
        else:
            dist_thumb_index_knuckle = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[5])
            if dist_thumb_index_knuckle < 0.08:
                return "S"
            
            dist_thumb_middle_knuckle = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[9])
            if dist_thumb_middle_knuckle < 0.08:
                return "T"
            
            dist_all_fingers = get_distance(landmarks_mao.landmark[8], landmarks_mao.landmark[12]) + \
                               get_distance(landmarks_mao.landmark[12], landmarks_mao.landmark[16])
            if dist_all_fingers < 0.15:
                return "O"
            
            return "E"

    # ================================
    # LETRA H: Indicador e médio estendidos, juntos e alinhados horizontalmente
    # ================================
    if dedos_estendidos_com_polegar == [False, True, True, False, False]:
        y_index = landmarks_mao.landmark[8].y
        y_middle = landmarks_mao.landmark[12].y
        x_index = landmarks_mao.landmark[8].x
        x_middle = landmarks_mao.landmark[12].x

        # Dedos devem estar quase na mesma altura (Y)
        if abs(y_index - y_middle) < 0.03 and abs(x_index - x_middle) > 0.05:
            pulso_x = landmarks_mao.landmark[0].x
            if mao_rotulo == "Right":
                if x_index > pulso_x + 0.05:
                    return "H"
            else:  # Left
                if x_index < pulso_x - 0.05:
                    return "H"

    # ================================
    # LETRA J: Baseado em "I" (só mindinho), mas com curvatura para baixo/lado
    # ================================
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

    # ================================
    # LETRA P: Indicador e médio estendidos APONTANDO PARA BAIXO, palma para baixo
    # ================================
    if dedos_estendidos_com_polegar == [True, True, True, False, False]:
        index_tip = landmarks_mao.landmark[8]
        middle_tip = landmarks_mao.landmark[12]
        wrist = landmarks_mao.landmark[0]

        if index_tip.y > landmarks_mao.landmark[5].y and middle_tip.y > landmarks_mao.landmark[9].y:
            if wrist.y < index_tip.y - 0.1:
                dist_thumb_index = get_distance(landmarks_mao.landmark[4], landmarks_mao.landmark[8])
                if dist_thumb_index < 0.1:
                    return "P"

    # ================================
    # LETRA Z: Aproximação ESTÁTICA — Indicador estendido, formando ângulo com polegar
    # ================================
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