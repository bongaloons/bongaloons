import numpy as np
import os
import cv2
import mediapipe as mp

GESTURES = set([
    "call", "four", "hand_heart", "like", "mute", "one", "peace_inverted", "stop", "three",
    "three_gun", "timeout", "xsign", "dislike", "grabbing", "hand_heart2", "little_finger",
    "no_gesture", "palm", "point", "stop_inverted", "three2", "thumb_index", "two_up", "fist",
    "grip", "holy", "middle_finger", "ok", "peace", "rock", "take_picture", "three3",
    "thumb_index2", "two_up_inverted"
])

DOUBLE_GESTURES = ['thumb_index_two', 'holy', 'hand_heart', 'hand_heart2', 'xsign', 'takephoto', 'timeout']
SINGLE_GESTURES = GESTURES - DOUBLE_GESTURES

SINGLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(SINGLE_GESTURES)}
DOUBLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(DOUBLE_GESTURES)}

def get_keypoint_csv(hands, mp_hands, mp_drawing, dataset_path, double = False):
    """
    Extract all hand keypoints from images in dataset and save to 
    """
    hand_classes = os.listdir(dataset_path)
    res = []
    for hand_class in hand_classes:
        hand_class_path = os.path.join(dataset_path, hand_class)
        hand_images = os.listdir(hand_class_path)
        for hand_image in hand_images:
            hand_image_path = os.path.join(hand_class_path, hand_image)
            frame = cv2.imread(hand_image_path)
        
            frame = cv2.flip(frame, 1)
            # Convert BGR to RGB (MediaPipe requirement)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            tmp = []
            for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Extract x and y coords of all 21 hand landmarks
                x = [lm.x for lm in hand_landmarks.landmark]
                y = [lm.y for lm in hand_landmarks.landmark]
                z = [lm.z for lm in hand_landmarks.landmark]

                label = SINGLE_LABEL_MAP[hand_class]

                landmark_info = np.vstack((x, y, z)).T.flatten() # 3 by 21 -> 63
                
                if not double: 
                    landmark_info = np.concatenate((label, landmark_info)) # 1 + 63 = 64
                    res.append(landmark_info)
                else: 
                    tmp.append(landmark_info)

            if double: 
                label = DOUBLE_LABEL_MAP[hand_class]
                res.append(np.concatenate(label, np.hstack(tmp))) # 1 + 63 * 2 = 127

    np.savetxt(f"hand_keypoints_double{double}.csv", res, delimiter = ",", fmt = "%f")

def main():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode = True, max_num_hands = 2, min_detection_confidence = 0.5)
    dataset_path = "single_gestures"
    get_keypoint_csv(hands, mp_hands, mp_drawing, dataset_path, double = False)
    get_keypoint_csv(hands, mp_hands, mp_drawing, dataset_path, double = True)

if __name__ == "__main__":
    main()