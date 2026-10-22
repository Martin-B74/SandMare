import json
from pathlib import Path


def parse_message(msg_str: str) -> dict:
    """
    Transforme le texte brut du champ Message de Sysmon en dictionnaire clé/valeur.

    Parameters
    ----------
    msg_str : str
        Le contenu textuel brut de l'événement Sysmon.

    Returns
    -------
    dict
        Dictionnaire contenant les paires clé-valeur extraites.
    """
    data = {}
    for line in msg_str.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


# Dictionnaire traduisant les ID Sysmon en "mots" pour le NLP
SYSMON_VOCAB = {
    1: "ProcessCreate",
    2: "FileCreateTime",
    3: "NetworkConnect",
    5: "ProcessTerminate",
    7: "ImageLoad",
    8: "CreateRemoteThread",
    9: "RawAccessRead",
    10: "ProcessAccess",
    11: "FileCreate",
    12: "RegKeyCreate",
    13: "RegValueSet",
    14: "RegKeyRename",
    15: "FileCreateStreamHash",
    22: "DnsQuery",
}


def extract_sequence(json_path: str | Path, compress_loops: bool = True) -> list[str]:
    """
    Extrait la séquence chronologique des événements Sysmon sous forme de texte.

    Filtre le bruit de l'OS en ne gardant que l'arborescence du processus ciblé
    et compresse les boucles d'appels répétitifs pour le réseau récurrent.

    Parameters
    ----------
    json_path : str | Path
        Chemin vers le fichier JSON généré par la Sandbox.
    compress_loops : bool, default=True
        Si Vrai, supprime les événements consécutifs identiques (compression de boucles).

    Returns
    -------
    list of str
        Liste ordonnée représentant la séquence d'appels (ex: ["ProcessCreate", "FileCreate", ...]).
    """
    path = Path(json_path)
    sample_name = path.stem.lower()

    with open(path, "r", encoding="utf-8-sig") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = [raw]

    # Parsing initial et tri chronologique
    events = []
    for ev in raw:
        msg = parse_message(ev.get("Message", ""))
        events.append(
            {
                "id": ev.get("Id"),
                "time": ev.get("TimeCreated"),
                "pid": (
                    int(msg["ProcessId"])
                    if msg.get("ProcessId", "").isdigit()
                    else None
                ),
                "ppid": (
                    int(msg["ParentProcessId"])
                    if msg.get("ParentProcessId", "").isdigit()
                    else None
                ),
                "image": msg.get("Image", ""),
            }
        )

    # Trie par date de création
    events.sort(key=lambda x: x["time"] if x["time"] else "")

    # Filtrage du bruit de l'OS, isolation du sample et ses enfants
    pids = {
        e["pid"]
        for e in events
        if e["id"] == 1 and sample_name in Path(e["image"]).name.lower() and e["pid"]
    }
    for _ in range(5):  # Recherche sur 5 niveaux de profondeur
        children = {
            e["pid"] for e in events if e["id"] == 1 and e["ppid"] in pids and e["pid"]
        }
        if not children.issubset(pids):
            pids.update(children)
        else:
            break

    # Conserve uniquement les événements liés au malware (élimine le bruit Windows)
    sample_events = [e for e in events if e["pid"] in pids] if pids else events

    # Traduction en "mots" et compression des boucles
    sequence = []
    for e in sample_events:
        # Traduire l'ID en mot (ou "UnknownEvent_X" si non répertorié)
        word = SYSMON_VOCAB.get(e["id"], f"UnknownEvent_{e['id']}")

        # Compression des boucles, ignore le mot si identique au précédent
        if compress_loops and sequence and sequence[-1] == word:
            continue

        sequence.append(word)

    return sequence
