import numpy as np
import os
import cv2
import mediapipe as mp
from joblib import Parallel, delayed
from joblib.externals.loky import get_reusable_executor
import tensorflow as tf

GESTURES = set([
    "call", "four", "hand_heart", "like", "mute", "one", "peace_inverted", "stop", "three",
    "three_gun", "timeout", "xsign", "dislike", "grabbing", "hand_heart2", "little_finger",
    "no_gesture", "palm", "point", "stop_inverted", "three2", "thumb_index", "two_up", "fist",
    "grip", "holy", "middle_finger", "ok", "peace", "rock", "take_picture", "three3",
    "thumb_index2", "two_up_inverted"
])

DOUBLE_GESTURES = sorted(set(['holy', 'hand_heart2', 'xsign', 'timeout']))
SINGLE_GESTURES = sorted(set(['rock', 'peace', 'palm', 'middle_finger', 'ok', 'one']))

SINGLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(SINGLE_GESTURES)}
DOUBLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(DOUBLE_GESTURES)}

NUM_THREADS = cv2.getNumThreads()  # Prints the number of threads OpenCV will use
IMAGES_PER_CLASS = 5000

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

            label = SINGLE_LABEL_MAP[hand_class] if not double else DOUBLE_LABEL_MAP[hand_class]
            landmark_info = np.hstack((x, y, z))  # Shape: (63,)

            if not double:
                row = np.concatenate(([label], landmark_info))
                # print(f"{hand_class}: {hand_image_path}")
                return row  # Shape: (64,)
            else:
                tmp.append(landmark_info)

        if double and len(tmp) == 2:
            label = DOUBLE_LABEL_MAP[hand_class]
            row = np.concatenate(([label], np.hstack(tmp))) # Shape: (127,)
            return row  

    return None  # If no hands detected


def get_keypoint_csv(dataset_path, multiprocess = True, double=False):
    """Process all images in dataset in parallel and save extracted keypoints to CSV"""
    gestures_set = DOUBLE_GESTURES if double else SINGLE_GESTURES
    hand_classes = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d)) and (d in gestures_set)]
    image_paths = []

    for hand_class in hand_classes:
        hand_class_path = os.path.join(dataset_path, hand_class)
        images = [os.path.join(hand_class_path, img) for img in os.listdir(hand_class_path)]
        # random.shuffle(images)
        image_paths.extend([(img, hand_class, double) for img in images[:IMAGES_PER_CLASS]])

    if multiprocess:
        print(f"Processing {len(image_paths)} images using {NUM_THREADS} cores...")

        # Use joblib with multiprocessing (loky backend ensures separate processes)
        results = Parallel(n_jobs=NUM_THREADS, backend="loky")(
            delayed(process_image)(img, hand_class, double) for img, hand_class, double in image_paths
        )

        results = [r for r in results if r is not None]  # Remove None values
        
    else:
        results = []
        for i, r in enumerate(image_paths):
            if r is not None: 
                img, hand_class, double = r
                row = process_image(img, hand_class, double)
                
                if row is not None: results.append(row)
            if i % 1000 == 1:
                print(f"Processed {i + 1} images")
    # results = np.array(results, dtype = np.float32)
    output_file = f"hand_keypoints_double{double}.csv"
    np.savetxt(output_file, results, delimiter=",", fmt="%f")
    print(f"Saved {len(results)} processed images to {output_file}")

def main():
    get_reusable_executor().shutdown(wait=True)
    dataset_path = "../data/HaGRIDv2_dataset_512"
    print(SINGLE_LABEL_MAP, DOUBLE_LABEL_MAP)

    # Run in parallel for both single and double hand keypoints
    get_keypoint_csv(dataset_path, multiprocess = False, double=False)
    get_keypoint_csv(dataset_path, multiprocess = False, double=True)

if __name__ == "__main__":
    main()