import cv2
import mediapipe as mp
import tensorflow as tf
import numpy as np
import time
from config import *
from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

# Define screen regions
TOP_THRESHOLD = 0.33
BOTTOM_THRESHOLD = 0.66

# Initialize MediaPipe Hands and model interpreter globally
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
interpreter, input_details, output_details = None, None, None

def detect_hand_position_draw(frame, hands, mp_hands, mp_drawing):
    #Unmirror the frame
    frame = cv2.flip(frame, 1)
    # Convert BGR to RGB (MediaPipe requirement)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    positions = []
    if results.multi_hand_landmarks and results.multi_handedness:
        for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Extract x and y coords of all 21 hand landmarks
            x_vals = [lm.x for lm in hand_landmarks.landmark]
            y_vals = [lm.y for lm in hand_landmarks.landmark]

            # Get average hand position
            hand_x = np.mean(x_vals)
            hand_y = np.mean(y_vals)

            # Determine region
            position = "Middle"
            if hand_y < TOP_THRESHOLD:
                position = "Top"
            elif hand_y > BOTTOM_THRESHOLD:
                position = "Bottom"

            # Left hand position, then right hand position
            positions.append(position)

            # Get hand label (Left or Right)
            hand_label = handedness.classification[0].label  # "Left" or "Right"

            text = f"{hand_label} Hand: {position}"
            cv2.putText(frame, text, (50, 50 + idx * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    return frame, positions

def setup_model(tflite_save_path):
    interpreter = tf.lite.Interpreter(model_path=tflite_save_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    return interpreter, input_details, output_details

def detect_hand_position(frame, interpreter, hands, mp_hands, input_details, output_details, use_double=False):
    """
    Detect hand positions in a frame. For each hand, determine if it is in the top, middle, or bottom region of the screen.
    Call this function for base bongo hits. 
    """
    #Unmirror the frame
    frame = cv2.flip(frame, 1)
    # Convert BGR to RGB (MediaPipe requirement)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    positions = [None, None]

    # if results.multi_hand_landmarks and results.multi_handedness:
    temp = []
    if results.multi_hand_landmarks:
        for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):

            # Extract x and y coords of all 21 hand landmarks
            x = [lm.x for lm in hand_landmarks.landmark]
            y = [lm.y for lm in hand_landmarks.landmark]
            z = [lm.z for lm in hand_landmarks.landmark]
        
            landmark_info = np.hstack((x, y, z)) # Shape: (63,)
            input_data = np.array([landmark_info], dtype=np.float32)

            # Get the output
            if not use_double:
                # Run classifier
                interpreter.set_tensor(input_details[0]['index'], input_data)
                interpreter.invoke()
                output_data = interpreter.get_tensor(output_details[0]['index'])
                probabilities = np.squeeze(output_data)
                max_prob = np.max(probabilities)
                if max_prob < CONFIDENCE_THRESHOLD: output = None
                else: output = np.argmax(probabilities)
                positions[idx] = output
            else:
                temp.append(landmark_info)
    
    if use_double and len(temp) == 2:
        input_data = np.hstack(temp).astype(np.float32)
        input_data = np.expand_dims(input_data, axis=0)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        probabilities = np.squeeze(output_data)
        max_prob = np.max(probabilities)
        if max_prob < CONFIDENCE_THRESHOLD:
            output = None
        else:
            output = np.argmax(probabilities)
        positions[0] = output

    return positions

def test_hand_position_live(cap, hands, mp_hands, mp_drawing):
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame, positions = detect_hand_position_draw(frame, hands, mp_hands, mp_drawing)
        print(positions)
        # Show live video in a pop-out window
        cv2.imshow("Live Hand Tracking", frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def check_hand_position(octet_stream, hands, mp_hands, interpreter, input_details, output_details, use_double = False):
    """
    Given a .bin octet stream file, determine the most common hand position
    for left and right hands in the video.
    """
    with open("temp.mp4", "wb") as f:
        f.write(octet_stream)
    
    cap = cv2.VideoCapture("temp.mp4")
    all_positions = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break 
            
        all_positions.append(detect_hand_position(frame, interpreter, hands, mp_hands, input_details, output_details, use_double = use_double))
    
    gesture_counts_left = [0] * (len(SINGLE_LABEL_MAP)) if not use_double else [0] * (len(DOUBLE_LABEL_MAP))
    gesture_counts_right = [0] * (len(SINGLE_LABEL_MAP)) if not use_double else [0] * (len(DOUBLE_LABEL_MAP))

    for positions in all_positions:
        left_gesture = positions[0]
        if left_gesture is None: gesture_counts_left[-1] += 1
        else: gesture_counts_left[left_gesture] += 1
        # If we're dealing with a two-handed pose, everything we need is already in the left_gesture index
        if not use_double:
            right_gesture = positions[1]
            if right_gesture is None: gesture_counts_right[-1] += 1
            else: gesture_counts_right[right_gesture] += 1
    most_common_left = gesture_counts_left.index(max(gesture_counts_left))

    if not use_double:
        most_common_right = gesture_counts_right.index(max(gesture_counts_right))
        return SINGLE_ID_TO_GESTURE[most_common_left], SINGLE_ID_TO_GESTURE[most_common_right]

    return DOUBLE_ID_TO_GESTURE[most_common_left], 'none'

def check_hand_position_api(bin_file, mp_hands, hands, interpreter, input_details, output_details, use_double):
    with open(bin_file, "rb") as f:
        octet_stream = f.read()
    left, right = check_hand_position(octet_stream, hands, mp_hands, interpreter, input_details, output_details, use_double = use_double)
    return left, right


def main(use_double = False):
    # Open Webcam
    cap = cv2.VideoCapture(0)
    
    tflite_save_path = "./model/model_doubleTrue.tflite" if use_double else "./model/model_doubleFalse.tflite"
    interpreter, input_details, output_details = setup_model(tflite_save_path)
    # Test hand position
    # test_hand_position_live(cap, hands, mp_hands, mp_drawing)
    left, right = check_hand_position_api("test_double.bin", mp_hands, hands, interpreter, input_details, output_details, use_double = use_double)
    print(left, right)
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="run gesture recognizer")
    parser.add_argument('--use_double', action='store_true', help="detect hand gestures that involve both hands")
    args = parser.parse_args()
    use_double = args.use_double
    uvicorn.run(app, host="0.0.0.0", port=8000)