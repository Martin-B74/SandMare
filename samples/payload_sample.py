import subprocess
import time
import winreg

# 1. Simule la persistance (Event ID 13)
try:
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    winreg.SetValueEx(key, "TestPersistPoC", 0, winreg.REG_SZ, "calc.exe")
    winreg.CloseKey(key)
except OSError as e:
    print(f"Échec de la simulation de persistance : {e}")

# 2. Simule la création de fichier suspect (Event ID 11)
with open("poc_dropped.txt", "w") as f:
    f.write("Fichier cree pour test sandbox")

# 3. Simule un processus enfant (Event ID 1)
subprocess.Popen(["calc.exe"])

# Pause pour laisser le temps à Sysmon d'enregistrer
time.sleep(5)
