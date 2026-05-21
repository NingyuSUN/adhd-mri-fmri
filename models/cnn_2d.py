"""
models/cnn_2d.py
Small 2D CNN for ROI-guided T1w slice classification.
"""

import tensorflow as tf
from tensorflow.keras import layers, models


def build_small_cnn(img_size: int = 128, lr: float = 1e-3) -> tf.keras.Model:
    """
    Lightweight 2D CNN for binary classification of ROI-selected T1w slices.

    Architecture:
        Input (img_size × img_size × 1)
        → Conv2D(16) + MaxPool
        → Conv2D(32) + MaxPool
        → Conv2D(64) + GlobalAvgPool
        → Dropout(0.2)
        → Dense(1, sigmoid)

    Args:
        img_size: height and width of input slices (default 128).
        lr: Adam learning rate.

    Returns:
        Compiled Keras model.
    """
    inp = layers.Input(shape=(img_size, img_size, 1))
    x = layers.Conv2D(16, 3, padding="same", activation="relu")(inp)
    x = layers.MaxPool2D()(x)
    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
    x = layers.MaxPool2D()(x)
    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    out = layers.Dense(1, activation="sigmoid")(x)

    model = models.Model(inp, out)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(lr),
        loss="binary_crossentropy",
    )
    return model
