import csv
from pathlib import Path
import time
from sandmare import detonate, extract_features

# --- Configuration des dossiers ---
SAMPLES_DIR = Path("./samples_benign")
LOGS_DIR = Path("./logs_benign")
OUTPUT_CSV = Path("dataset_benign.csv")

LABEL = 0  # 0 = bénin (goodware), 1 = malware
DURATION_PER_SAMPLE = 15  # Durée d'observation dans la VM en secondes

def main():
    LOGS_DIR.mkdir(exist_ok=True)
    
    # 1. Récupération de tous les .exe
    exe_list = [f for f in SAMPLES_DIR.glob("*.exe") if f.name != "[.exe"]
    
    # 2. Limitation à 5 échantillons pour le test initial (APRES la déclaration)
    # exe_list = exe_list[:5]
    
    total = len(exe_list)
    print(f"[*] {total} exécutable(s) sélectionné(s) pour le test dans {SAMPLES_DIR}\n")

    records = []

    for index, exe_path in enumerate(exe_list, start=1):
        sample_stem = exe_path.stem
        raw_json_host = Path(f"./{sample_stem}.json")
        target_json = LOGS_DIR / f"{sample_stem}.json"

        # Éviter de ré-exécuter un échantillon déjà traité
        if target_json.exists():
            print(f"[{index}/{total}] Déjà analysé : {exe_path.name} -> Chargement")
            try:
                features = extract_features(target_json, label=LABEL)
                records.append(features)
            except Exception as e:
                print(f"    [-] Erreur lors du parsing existant : {e}")
            continue

        print(f"[{index}/{total}] Traitement de : {exe_path.name}")
        
        try:
            # 1. Détonation dans la VM Sandbox
            detonate(str(exe_path), duration=DURATION_PER_SAMPLE)

            # 2. Déplacement du fichier JSON produit vers logs_benign/
            if raw_json_host.exists():
                raw_json_host.replace(target_json)
                
                # 3. Extraction des features
                features = extract_features(target_json, label=LABEL)
                records.append(features)
                print(f"    [+] Features extraites avec succès pour {exe_path.name}")
            else:
                print(f"    [-] Avertissement : {raw_json_host.name} non trouvé après détonation.")

        except Exception as err:
            print(f"    [!] Échec sur {exe_path.name} : {err}")
            time.sleep(5)

    # 4. Sauvegarde finale dans le fichier CSV
    if records:
        fieldnames = list(records[0].keys())
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"\n[✓] Traitement terminé ! Dataset généré dans : {OUTPUT_CSV.resolve()}")
    else:
        print("\n[-] Aucune caractéristique n'a pu être extraite.")

if __name__ == "__main__":
    main()