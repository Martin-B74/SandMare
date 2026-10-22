"""
Script de démonstration : Pipeline d'entraînement du modèle de Deep Learning SandMare.
"""

import tensorflow as tf
from sandmare import build_sequence_model, prepare_dataset
from sandmare.parser import SYSMON_VOCAB

def main():
    print("=== Démonstration du pipeline Deep Learning SandMare ===\n")
    
    # 1. Simulation de données textuelles
    # En situation réelle, ces listes seraient générées par extract_sequence("events.json")
    
    # Séquence malveillante typique (ex: comportement d'un Ransomware)
    malware_seq_1 = ["ProcessCreate", "FileCreate", "FileCreate", "RegKeyCreate", "RegValueSet", "ProcessTerminate"]
    malware_seq_2 = ["ProcessCreate", "CreateRemoteThread", "ProcessAccess", "NetworkConnect"]
    
    # Séquences bénignes typiques (ex: navigation web ou tâche de fond)
    benign_seq_1 = ["ProcessCreate", "ImageLoad", "ImageLoad", "NetworkConnect", "ProcessTerminate"]
    benign_seq_2 = ["ProcessCreate", "FileCreateTime", "RawAccessRead", "ProcessTerminate"]
    
    sequences = [malware_seq_1, malware_seq_2, benign_seq_1, benign_seq_2]
    labels = [1, 1, 0, 0]  # 1 = Malware, 0 = Bénin
    
    # 2. Préparation du Dataset TensorFlow
    print("[1/3] Préparation du Dataset NLP...")
    # On définit une longueur max courte pour la démo
    dataset = prepare_dataset(sequences, labels, max_len=10, batch_size=2)
    
    # 3. Création du Modèle Récurrent
    print("\n[2/3] Construction du modèle LSTM...")
    vocab_size = len(SYSMON_VOCAB)
    # Dimensions réduites pour que la démo tourne instantanément sur CPU
    model = build_sequence_model(vocab_size=vocab_size, embedding_dim=8, rnn_units=16)
    
    # Affichage de l'architecture du réseau
    model.summary()
    
    # 4. Entraînement du modèle
    print("\n[3/3] Lancement de l'entraînement...")
    model.fit(dataset, epochs=10)
    
    print("\n[✓] Entraînement de démonstration terminé avec succès !")

if __name__ == "__main__":
    main()