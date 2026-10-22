import tensorflow as tf


def build_sequence_model(
    vocab_size: int, embedding_dim: int = 32, rnn_units: int = 64
) -> tf.keras.Model:
    """
    Construit et compile le modèle de Deep Learning basé sur un réseau récurrent (LSTM).

    Ce modèle traite l'historique d'exécution comme une séquence de mots (NLP)
    pour repérer les enchaînements malveillants.

    Parameters
    ----------
    vocab_size : int
        La taille du vocabulaire (nombre d'appels système uniques connus).
    embedding_dim : int, default=32
        La dimension de l'espace vectoriel pour représenter chaque appel d'API.
    rnn_units : int, default=64
        Le nombre de neurones dans la couche récurrente LSTM.

    Returns
    -------
    tf.keras.Model
        Le modèle TensorFlow compilé, prêt pour l'entraînement.
    """
    model = tf.keras.Sequential(
        [
            # Vectorisation : transforme l'ID entier de chaque appel (le "mot") en vecteur dense
            tf.keras.layers.Embedding(
                input_dim=vocab_size + 1,
                output_dim=embedding_dim,
                mask_zero=True,  # ignore le padding des séquences plus courtes
                name="api_embedding",
            ),
            # Réseau Récurrent : analyse l'enchaînement chronologique pour repérer les comportements douteux
            tf.keras.layers.LSTM(rnn_units, name="sequence_analysis"),
            # Classification : prédit si la séquence est malveillante (proche de 1) ou légitime (proche de 0)
            tf.keras.layers.Dense(1, activation="sigmoid", name="malware_classifier"),
        ]
    )

    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

    return model
