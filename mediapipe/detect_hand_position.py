import cv2
import mediapipe as mp
import numpy as np
import time

# Define screen regions
TOP_THRESHOLD = 0.33
BOTTOM_THRESHOLD = 0.66

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

def detect_hand_position(frame, hands, mp_hands, mp_drawing):
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
    print(f"Multi hand landmarks: {results.multi_hand_landmarks}")

    for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):

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
        positions[idx] = position

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

def check_hand_position(octet_stream, hands, mp_hands, mp_drawing):
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
            
        all_positions.append(detect_hand_position(frame, hands, mp_hands, mp_drawing))
    
    top_count, middle_count, bottom_count = 0, 0, 0
    for _, y in all_positions:
        if y == "Top": top_count += 1
        elif y == "Middle": middle_count += 1
        else: bottom_count += 1
    
    counts = {"top": top_count, "middle": middle_count, "bottom": bottom_count}
    most_common_region = max(counts, key=counts.get)

    return most_common_region

def test_check_hand_position(bin_file):
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
    with open(bin_file, "rb") as f:
        octet_stream = f.read()
    region = check_hand_position(octet_stream, hands, mp_hands, mp_drawing)
    print(region)
    
def main():
    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

    # Open Webcam
    cap = cv2.VideoCapture(0)

    # Test hand position
    # test_hand_position_live(cap, hands, mp_hands, mp_drawing)
    test_check_hand_position("test.bin")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()