import os
import cv2
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from wandb.integration.keras import WandbMetricsLogger 
import wandb

RANDOM_SEED = 42
DOUBLE_GESTURES = sorted(set(['holy', 'hand_heart2', 'xsign', 'timeout']))
SINGLE_GESTURES = sorted(set(['rock', 'peace', 'palm', 'middle_finger', 'ok', 'one']))

DOUBLE_GESTURES = sorted(set(['holy', 'hand_heart2', 'xsign', 'timeout']))
SINGLE_GESTURES = sorted(set(['rock', 'peace', 'palm', 'middle_finger', 'ok', 'one']))

SINGLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(SINGLE_GESTURES)}
DOUBLE_LABEL_MAP = {gesture: idx for idx, gesture in enumerate(DOUBLE_GESTURES)}

def load_data(dataset_path, double = False):
    usecols = list(range(1, 126 + 1)) if double else list(range(1, 63 + 1))
    inputs = np.loadtxt(dataset_path, delimiter=',', dtype='float32', usecols = usecols)
    outputs = np.loadtxt(dataset_path, delimiter=',', usecols=(0)).astype(np.int16)
    x_train, x_test, y_train, y_test = train_test_split(inputs, outputs, train_size=0.75, random_state=RANDOM_SEED)
    return x_train, x_test, y_train, y_test

def build_model(input_size, hidden_size, output_size, num_layers, dropout_rate):
    inputs = tf.keras.layers.Input(shape=(input_size,))
    x = inputs  # Start with input layer
    
    # Encoder - project to hidden dimension
    x = tf.keras.layers.Dense(hidden_size)(inputs)
    
    # Residual blocks
    for _ in range(num_layers):
        residual_connection = x
        x = tf.keras.layers.Dense(hidden_size)(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.Dropout(rate=dropout_rate)(x)
        x = tf.keras.layers.Add()([x, residual_connection])
    
    # Decoder
    outputs = tf.keras.layers.Dense(output_size, activation="softmax")(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    return model

class WandbCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        if logs is not None:
            wandb.log({"epoch": epoch + 1, **logs})

def train_gesture_recognizer(model, x_train, y_train, x_test, y_test, model_save_path, 
                             batch_size = 256, num_epochs = 500):
    # Clear previous session (helps avoid memory leaks)
    tf.keras.backend.clear_session()

    # Initialize W&B
    wandb.init(project="bongaloon")

    # Model checkpoint callback (saves best model)
    cp_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=model_save_path,
        monitor="val_loss",
        save_best_only=True,  # Saves only the best model based on validation loss
        verbose=1,
        save_weights_only=False
    )

    # Early stopping callback (stops if val_loss doesn't improve for 50 epochs)
    es_callback = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=50,
        verbose=1,
        restore_best_weights=True  # Restores the best weights after stopping
    )

    # Compile the model
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    # Train the model and log metrics
    history = model.fit(
        x_train,
        y_train,
        epochs=num_epochs,
        batch_size=batch_size,
        validation_data=(x_test, y_test),
        callbacks=[WandbMetricsLogger(), cp_callback, es_callback]
    )

    # Finish W&B logging
    wandb.finish()

    # Return history for further analysis
    return history

def evaluate_gesture_recognizer(model, x_test, y_test):
    loss, accuracy = model.evaluate(x_test, y_test, verbose=1)
    return loss, accuracy

def main(use_double=False):
    # Set paths
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "0"
    print(tf.config.list_physical_devices('GPU'))
    print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
    
    dataset_path = "hand_keypoints_doubleFalse.csv" if use_double else "hand_keypoints_doubleTrue.csv"
    model_dir = "../model/model.keras"
        
    # Load and preprocess data
    x_train, x_test, y_train, y_test = load_data(dataset_path, double=use_double)
    
    # Model parameters
    input_size = 63  
    hidden_size = 128
    output_size = len(SINGLE_GESTURES)  # Number of gesture classes
    num_layers = 3
    dropout_rate = 0.1
    
    # Build model
    model = build_model(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        num_layers=num_layers,
        dropout_rate=dropout_rate
    )
    
    # Train model
    history = train_gesture_recognizer(
        model=model,
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        model_save_path=model_dir
    )
    
    # Evaluate model
    loss, accuracy = evaluate_gesture_recognizer(model, x_test, y_test)
    print(f"\nFinal Test Loss: {loss:.4f}")
    print(f"Final Test Accuracy: {accuracy:.4f}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train gesture recognizer")
    parser.add_argument('--use_double', action='store_true', help="Use double dataset")
    args = parser.parse_args()
    main(use_double=args.use_double)