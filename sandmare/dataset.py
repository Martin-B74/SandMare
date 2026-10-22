import tensorflow as tf

from .parser import SYSMON_VOCAB

# Création du dictionnaire inversé pour la tokenisation (Mot -> ID)
# ex: "ProcessCreate" -> 1, "FileCreate" -> 11
WORD_TO_ID = {word: key for key, word in SYSMON_VOCAB.items()}


def prepare_dataset(
    sequences: list[list[str]],
    labels: list[int],
    max_len: int = 100,
    batch_size: int = 32,
) -> tf.data.Dataset:
    """
    Convertit les séquences de mots en un Dataset TensorFlow prêt pour l'entraînement.

    Cette fonction applique la tokenisation (mot vers entier) et le padding
    (remplissage par des zéros) pour uniformiser la taille des séquences.

    Parameters
    ----------
    sequences : list of list of str
        Liste des séquences d'appels extraites (ex: [["ProcessCreate", ...], [...]]).
    labels : list of int
        Liste des étiquettes associées (1 pour malware, 0 pour bénin).
    max_len : int, default=100
        Longueur maximale d'une séquence. Les plus longues sont tronquées,
        les plus courtes sont complétées avec des zéros.
    batch_size : int, default=32
        Taille des lots (batches) pour l'entraînement du modèle.

    Returns
    -------
    tf.data.Dataset
        Dataset TensorFlow optimisé et batché.
    """
    numeric_seqs = []
    for seq in sequences:
        # Tokenisation : on traduit le mot en entier.
        # L'ID 0 est utilisé pour le padding ou les mots inconnus
        num_seq = [WORD_TO_ID.get(word, 0) for word in seq]
        numeric_seqs.append(num_seq)

    # Padding : uniformisation de la longueur des séquences en fin de liste
    padded_seqs = tf.keras.utils.pad_sequences(
        numeric_seqs, maxlen=max_len, padding="post", truncating="post"
    )

    # Création du pipeline de données TensorFlow
    dataset = tf.data.Dataset.from_tensor_slices((padded_seqs, labels))

    # Mélange les données pour éviter que le modèle n'apprenne l'ordre d'insertion
    dataset = dataset.shuffle(buffer_size=len(sequences) + 1 if sequences else 1000)
    dataset = dataset.batch(batch_size)

    # AUTOTUNE permet à TensorFlow de préparer le batch suivant pendant que le CPU/GPU calcule l'actuel
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset
