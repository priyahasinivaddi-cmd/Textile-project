"""Textile-safe training augmentation shared by model trainers."""


def build_augmentation():
    import tensorflow as tf

    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.04),
            tf.keras.layers.RandomZoom(0.08),
            tf.keras.layers.RandomContrast(0.10),
            tf.keras.layers.RandomBrightness(0.08, value_range=(0, 255)),
        ],
        name="textile_safe_augmentation",
    )
