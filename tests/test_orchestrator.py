from unittest.mock import patch
from sandmare.orchestrator import vmrun, detonate

@patch("sandmare.orchestrator.subprocess.run")
def test_vmrun(mock_run):
    """Vérifie que la commande vmrun assemble correctement les arguments."""
    # Test d'une commande classique (sans authentification invitée)
    vmrun(["start", "C:\\VMs\\Sandbox1.vmx"])
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "-T" in args
    assert "start" in args

    mock_run.reset_mock()

    # Test d'une commande nécessitant l'authentification dans la VM (guest=True)
    vmrun(["runProgramInGuest"], guest=True)
    args_guest = mock_run.call_args[0][0]
    assert "-gu" in args_guest
    assert "runProgramInGuest" in args_guest

# On patch time.sleep pour éviter que le test ne dure 45 secondes
@patch("sandmare.orchestrator.time.sleep")
# On patch subprocess.run pour éviter de déclencher de vraies requêtes VMware
@patch("sandmare.orchestrator.subprocess.run")
def test_detonate(mock_run, mock_sleep):
    """Vérifie que la séquence de détonation effectue bien toutes les étapes attendues."""
    
    detonate("samples/malware.exe", duration=10)

    # Vérifie que les pauses ont bien été ordonnées (attente boot, attente détonation, attente rapatriement)
    assert mock_sleep.call_count == 3
    
    # L'orchestrateur effectue 7 appels système dans son cycle normal :
    # 1. revertToSnapshot, 2. start, 3. copy (guest), 4. runProgram (guest), 
    # 5. logs powershell (guest), 6. rapatriement logs, 7. revertToSnapshot
    assert mock_run.call_count == 7