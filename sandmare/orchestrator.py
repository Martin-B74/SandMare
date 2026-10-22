import os
from pathlib import Path
import subprocess
import time
from dotenv import load_dotenv

# Charger les variables d'environnement (.env)
load_dotenv()

# --- Configuration VMware & Hôte ---
VMRUN = os.getenv(
    "VMRUN_PATH",
    r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe",
)
VMX = os.getenv("VMX_PATH", r"C:\VMs\Sandbox1.vmx")
SNAP = os.getenv("SNAPSHOT_NAME", "Clean_State_Sysmon")
VM_PASSWORD = os.getenv("VM_PASSWORD", "123456789")

# --- Identifiants du compte Windows invité ---
GUEST_USER = os.getenv("GUEST_USER", "alexandre")
GUEST_PASS = os.getenv("GUEST_PASSWORD", "invalide")

# --- Drapeaux d'authentification vmrun ---
VM_AUTH = ["-vp", VM_PASSWORD] if VM_PASSWORD else []
GUEST_AUTH = ["-gu", GUEST_USER, "-gp", GUEST_PASS]

# Chemin absolu de PowerShell dans l'OS invité (évite 'A file was not found')
GUEST_POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def vmrun(args: list[str], guest: bool = False, retries: int = 3, delay: int = 4) -> None:
    """
    Exécute une commande vmrun avec gestion de l'authentification
    et réessais en cas de verrou temporaire de la VM.
    """
    cmd = [VMRUN, "-T", "ws"] + VM_AUTH
    if guest:
        cmd += GUEST_AUTH
    cmd += args

    for attempt in range(1, retries + 1):
        try:
            subprocess.run(cmd, check=True)
            return
        except subprocess.CalledProcessError as e:
            if attempt < retries:
                time.sleep(delay)
            else:
                raise e


def wait_for_tools(timeout: int = 30) -> None:
    """Attend que les VMware Tools soient prêts dans la machine virtuelle."""
    cmd = [VMRUN, "-T", "ws"] + VM_AUTH + ["checkToolsState", VMX]
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if "running" in res.stdout.lower() or "installed" in res.stdout.lower():
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(2)


def detonate(sample_host_path: str, duration: int = 15) -> str:
    """
    Déploie et exécute un échantillon binaire dans la sandbox VMware,
    puis rapatrie les journaux Sysmon au format JSON.
    
    Retourne le chemin relatif du fichier JSON généré sur l'hôte.
    """
    sample_path = Path(sample_host_path)
    sample_name = sample_path.name
    sample_stem = sample_path.stem

    guest_sample = f"C:\\Users\\{GUEST_USER}\\Desktop\\{sample_name}"
    guest_json = f"C:\\Users\\{GUEST_USER}\\Desktop\\{sample_stem}.json"
    host_json = f"./{sample_stem}.json"

    # [1/5] Restauration du snapshot et démarrage
    print("[1/5] Restauration du snapshot...")
    vmrun(["revertToSnapshot", VMX, SNAP])
    time.sleep(2)  # Pause pour laisser VMware relâcher les verrous .lck
    
    vmrun(["start", VMX, "nogui"])
    wait_for_tools(timeout=25)

    # [2/5] Détonation de l'échantillon
    print("[2/5] Détonation de l'échantillon...")
    vmrun(["copyFileFromHostToGuest", VMX, str(sample_path.resolve()), guest_sample], guest=True)
    vmrun(
        [
            "runProgramInGuest",
            VMX,
            "-noWait",
            "-activeWindow",
            guest_sample,
        ],
        guest=True,
    )

    # [3/5] Collecte des traces
    print(f"[3/5] Collecte des traces ({duration}s)...")
    time.sleep(duration)

    # [4/5] Rapatriement des logs Sysmon
    print("[4/5] Rapatriement des logs...")
    ps_cmd = (
        f'Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 300 '
        f"| Select-Object Id, TimeCreated, Message "
        f"| ConvertTo-Json -Depth 3 "
        f'| Out-File -FilePath "{guest_json}" -Encoding utf8'
    )
    
    vmrun(
        [
            "runProgramInGuest",
            VMX,
            GUEST_POWERSHELL,
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_cmd,
        ],
        guest=True,
    )
    time.sleep(2)
    
    vmrun(["copyFileFromGuestToHost", VMX, guest_json, host_json], guest=True)

    # [5/5] Nettoyage et remise à zéro
    print("[5/5] Remise à zéro...")
    vmrun(["revertToSnapshot", VMX, SNAP])
    print("[✓] Terminé.")

    return host_json


if __name__ == "__main__":
    pass