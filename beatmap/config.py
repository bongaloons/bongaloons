DOUBLE_GESTURES = sorted(set(['holy', 'hand_heart2', 'xsign', 'timeout']))
SINGLE_GESTURES = sorted(set(['rock', 'peace', 'palm', 'middle_finger', 'ok', 'one']))

SINGLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(SINGLE_GESTURES)}
SINGLE_LABEL_MAP['none'] = len(SINGLE_GESTURES)
SINGLE_ID_TO_GESTURE = {idx: gesture for idx, gesture in enumerate(SINGLE_GESTURES)}
DOUBLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(DOUBLE_GESTURES)}
DOUBLE_LABEL_MAP['none'] = len(DOUBLE_GESTURES)
DOUBLE_ID_TO_GESTURE = {idx: gesture for idx, gesture in enumerate(DOUBLE_GESTURES)}

CONFIDENCE_THRESHOLD = 0.5