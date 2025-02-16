import numpy as np
import os
import cv2
import mediapipe as mp
from joblib import Parallel, delayed
import warnings

GESTURES = set([
    "call", "four", "hand_heart", "like", "mute", "one", "peace_inverted", "stop", "three",
    "three_gun", "timeout", "xsign", "dislike", "grabbing", "hand_heart2", "little_finger",
    "no_gesture", "palm", "point", "stop_inverted", "three2", "thumb_index", "two_up", "fist",
    "grip", "holy", "middle_finger", "ok", "peace", "rock", "take_picture", "three3",
    "thumb_index2", "two_up_inverted"
])

DOUBLE_GESTURES = set(['thumb_index_two', 'holy', 'hand_heart', 'hand_heart2', 'xsign', 'takephoto', 'timeout'])
SINGLE_GESTURES = set(['rock', 'peace', 'palm', 'middle_finger', 'ok', 'one'])

DOUBLE_GESTURES = sorted(DOUBLE_GESTURES)
SINGLE_GESTURES = sorted(SINGLE_GESTURES)

SINGLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(SINGLE_GESTURES)}
DOUBLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(DOUBLE_GESTURES)}

NUM_THREADS = 16

def process_image(hand_image_path, hand_class, double):
    """Process a single image and extract hand keypoints"""
    if "hands" not in globals():
        global hands
        hands = mp.solutions.hands.Hands(
            static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5
        )  # ✅ Initialize hands ONCE per worker process

    frame = cv2.imread(hand_image_path)
    frame = cv2.flip(frame, 1)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)  # ✅ Uses per-worker initialized hands instance

    tmp = []
    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            x = [lm.x for lm in hand_landmarks.landmark]
            y = [lm.y for lm in hand_landmarks.landmark]
            z = [lm.z for lm in hand_landmarks.landmark]

            label = SINGLE_LABEL_MAP[hand_class]
            landmark_info = np.hstack((x, y, z))  # Shape: (63,)

            if not double:
                row = np.concatenate(([label], landmark_info))
                print(f"{hand_class}: {hand_image_path}")
                return row  # Shape: (64,)
            else:
                tmp.append(landmark_info)

        if double and len(tmp) == 2:
            label = DOUBLE_LABEL_MAP[hand_class]
            row = np.concatenate(([label], np.hstack(tmp))) # Shape: (127,)
            return row  

    return None  # If no hands detected


def get_keypoint_csv(dataset_path, double=False):
    """Process all images in dataset in parallel and save extracted keypoints to CSV"""
    hand_classes = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
    image_paths = []

    for hand_class in hand_classes:
        hand_class_path = os.path.join(dataset_path, hand_class)
        images = [os.path.join(hand_class_path, img) for img in os.listdir(hand_class_path)]
        image_paths.extend([(img, hand_class, double) for img in images])

    print(f"Processing {len(image_paths)} images using {NUM_THREADS} cores...")

    # Use joblib with multiprocessing (loky backend ensures separate processes)
    results = Parallel(n_jobs=NUM_THREADS, backend="loky")(
        delayed(process_image)(img, hand_class, double) for img, hand_class, double in image_paths
    )

    results = [r for r in results if r is not None]  # Remove None values

    output_file = f"hand_keypoints_double{double}.csv"
    np.savetxt(output_file, results, delimiter=",", fmt="%f")
    print(f"Saved {len(results)} processed images to {output_file}")

def main():
    dataset_path = "../data/HaGRIDv2_dataset_512"
    
    # Run in parallel for both single and double hand keypoints
    get_keypoint_csv(dataset_path, double=False)
    get_keypoint_csv(dataset_path, double=True)

if __name__ == "__main__":
    main()