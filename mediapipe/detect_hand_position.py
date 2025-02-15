import cv2
import mediapipe as mp
import numpy as np
import time



# Define screen regions
TOP_THRESHOLD = 0.33
BOTTOM_THRESHOLD = 0.66

def test_hand_position(cap, hands, mp_hands, mp_drawing):
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        # Convert BGR to RGB (MediaPipe requirement)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks and results.multi_handedness:
            for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Extract hand position
                x_vals = [lm.x for lm in hand_landmarks.landmark]
                y_vals = [lm.y for lm in hand_landmarks.landmark]
                hand_x = np.mean(x_vals)
                hand_y = np.mean(y_vals)

                # Determine region
                position = "Middle"
                if hand_y < TOP_THRESHOLD:
                    position = "Top"
                elif hand_y > BOTTOM_THRESHOLD:
                    position = "Bottom"

                # Get hand label (Left or Right)
                hand_label = handedness.classification[0].label  # "Left" or "Right"

                # Display position and hand label as text overlay
                text = f"{hand_label} Hand: {position}"
                print(text)
                cv2.putText(frame, text, (50, 50 + idx * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Show live video in a pop-out window
        cv2.imshow("Live Hand Tracking", frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def main():
    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

    # Open Webcam
    cap = cv2.VideoCapture(0)

    # Test hand position
    test_hand_position(cap, hands, mp_hands, mp_drawing)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()