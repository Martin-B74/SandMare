import json

import tensorflow as tf

from sandmare.dataset import prepare_dataset
from sandmare.model import build_sequence_model
from sandmare.parser import extract_sequence


def test_extract_sequence_with_compression(tmp_path):
    """Teste l'extraction chronologique et la compression des boucles d'appels Sysmon."""
    # Création d'un faux fichier JSON Sysmon simulant un malware
    mock_events = [
        {
            "Id": 1,
            "TimeCreated": "2026-10-21T10:00:00Z",
            "Message": "ProcessId: 100\nParentProcessId: 4\nImage: C:\\malware.exe",
        },
        {"Id": 11, "TimeCreated": "2026-10-21T10:00:01Z", "Message": "ProcessId: 100"},
        {
            "Id": 11,
            "TimeCreated": "2026-10-21T10:00:02Z",
            "Message": "ProcessId: 100",
        },  # Répétition (boucle)
        {"Id": 5, "TimeCreated": "2026-10-21T10:00:03Z", "Message": "ProcessId: 100"},
    ]

    test_file = tmp_path / "malware.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(mock_events, f)

    # Test avec compression (par défaut)
    seq = extract_sequence(test_file, compress_loops=True)
    assert seq == ["ProcessCreate", "FileCreate", "ProcessTerminate"]

    # Test sans compression (cas limite)
    seq_no_compress = extract_sequence(test_file, compress_loops=False)
    assert seq_no_compress == [
        "ProcessCreate",
        "FileCreate",
        "FileCreate",
        "ProcessTerminate",
    ]


def test_prepare_dataset():
    """Teste la création du dataset TensorFlow, le padding et la tokenisation."""
    sequences = [
        ["ProcessCreate", "FileCreate"],
        ["ProcessCreate", "NetworkConnect", "ProcessTerminate"],
    ]
    labels = [1, 0]

    dataset = prepare_dataset(sequences, labels, max_len=4, batch_size=2)

    assert isinstance(dataset, tf.data.Dataset)

    for batch_x, batch_y in dataset.take(1):
        # Vérifie le shape => 2 séquences, padées de longueur 4
        assert batch_x.shape == (2, 4)
        # Vérifie le sahpe des labels
        assert batch_y.shape == (2,)


def test_build_sequence_model():
    """Teste la compilation et l'architecture du réseau récurrent."""
    vocab_size = 20
    model = build_sequence_model(vocab_size=vocab_size, embedding_dim=8, rnn_units=16)

    assert isinstance(model, tf.keras.Model)

    assert len(model.layers) == 3

    assert model.loss == "binary_crossentropy"
