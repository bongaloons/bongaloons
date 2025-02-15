import os
from mediapipe_model_maker import gesture_recognizer
import cv2
import mediapipe as mp
import numpy as np

def load_data(dataset_path):
    data = gesture_recognizer.Dataset.from_folder(
        dirname=dataset_path,
        hparams=gesture_recognizer.HandDataPreprocessingParams()
    )
    train_data, rest_data = data.split(0.8)
    validation_data, test_data = rest_data.split(0.5)

    return train_data, validation_data, test_data

def train_gesture_recognizer(train_data, validation_data, model_dir, hidden_layer_dims, lr = 0.003, shuffle = True):
    hparams = gesture_recognizer.HParams(learning_rate = lr, shuffle = True, export_dir = model_dir)
    model_options = gesture_recognizer.ModelOptions(hidden_layer_dims = hidden_layer_dims)
    options = gesture_recognizer.GestureRecognizerOptions(hparams = hparams)
    model = gesture_recognizer.create(
            train_data = train_data,
            validation_data = validation_data,
            options = options
    )

    return model

def evaluate_gesture_recognizer(model, test_data):
    return model.evaluate(test_data)

def main():
    dataset_path = "single_gestures"
    model_dir = "model"
    hidden_layer_dims = [128, 128, 64]
    
    train_data, validation_data, test_data = load_data(dataset_path)
    model = train_gesture_recognizer(train_data, validation_data, model_dir, hidden_layer_dims)
    loss, accuracy = evaluate_gesture_recognizer(model, test_data)
    print(f"Loss: {loss}, Accuracy: {accuracy}")
    model.export_model()

if __name__ == "__main__":
    main()