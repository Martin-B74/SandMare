# SandMare

SandMare est un outil d'analyse dynamique de logiciels malveillants intégrant un modèle d'apprentissage automatique[cite: 138]. Il capture les appels systèmes (API Win32 et Native) dans une Sandbox VMware et utilise le Deep Learning (réseaux récurrents) pour repérer les séquences d'exécution malveillantes[cite: 138].

## Fonctionnalités
- Orchestration automatisée de VM VMware pour la détonation de samples.
- Extraction et parsing des événements Sysmon au format JSON.
- Nettoyage des données et modélisation par Deep Learning des appels systèmes[cite: 138].

## Installation
1. Clonez le dépôt : `git clone https://github.com/votre-user/sandmare.git`
2. Installez les dépendances : `pip install .[dev]`
3. Copiez `.env.example` vers `.env` et remplissez vos chemins/mots de passe VMware.

## Utilisation
```python
from sandmare import detonate, extract_features

# Détoner un échantillon
detonate("samples/payload_sample.py", duration=30)

# Extraire les features pour le Machine Learning
features = extract_features("events.json")