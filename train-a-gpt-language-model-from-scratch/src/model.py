"""A minimal character transformer in Keras."""
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

tf.get_logger().setLevel("ERROR")

def make_sequences(text, characters, sequence_length):
    index_of = {character: index for index, character in enumerate(characters)}
    encoded = np.array([index_of[character] for character in text], dtype="int32")
    X, y = [], []
    for start in range(0, len(encoded) - sequence_length - 1):
        X.append(encoded[start:start + sequence_length])
        y.append(encoded[start + sequence_length])
    return np.asarray(X), np.asarray(y), index_of

def build_model(vocabulary_size, sequence_length, embedding=32):
    inputs = layers.Input((sequence_length,))
    x = layers.Embedding(vocabulary_size, embedding)(inputs)
    attention = layers.MultiHeadAttention(num_heads=2, key_dim=16)(x, x)
    x = layers.LayerNormalization()(x + attention)
    feed_forward = layers.Dense(64, activation="relu")(x)
    feed_forward = layers.Dense(32)(feed_forward)
    x = layers.LayerNormalization()(x + feed_forward)
    x = layers.Flatten()(x)
    outputs = layers.Dense(vocabulary_size)(x)
    return models.Model(inputs, outputs, name="tiny_char_transformer")

def sample(model, characters, index_of, seed_text, count=80, temperature=0.9):
    sequence_length = model.input_shape[1]
    text = seed_text
    for _ in range(count):
        window = text[-sequence_length:].rjust(sequence_length, " ")
        encoded = np.array([[index_of.get(character, 0) for character in window]])
        logits = model.predict(encoded, verbose=0)[0]
        logits = logits / max(0.1, temperature)
        probabilities = np.exp(logits - logits.max())
        probabilities = probabilities / probabilities.sum()
        text += characters[int(np.random.choice(len(characters), p=probabilities))]
    return text

def train(data, quick=False):
    tf.random.set_seed(2)
    np.random.seed(2)
    X, y, index_of = make_sequences(data["text"], data["characters"], data["sequence_length"])
    model = build_model(data["vocabulary_size"], data["sequence_length"])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    )
    history = model.fit(X, y, epochs=1 if quick else 8, batch_size=16, verbose=0)
    generated = sample(model, data["characters"], index_of, data["text"][:24], 100)
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/generated.txt").write_text(generated, encoding="utf-8")
    return model, {
        "loss": round(float(history.history["loss"][-1]), 4),
        "vocabulary_size": data["vocabulary_size"],
        "sequences": int(len(X)),
        "parameters": int(model.count_params()),
    }

def demo(data):
    print("Corpus preview:")
    print(data["text"][:280])
    print(f"\nVocabulary: {data['vocabulary_size']} characters, sequence length: {data['sequence_length']}")
    print("Run `python main.py train` to fit the transformer and write artifacts/generated.txt.")
