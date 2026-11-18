#!/usr/bin/env python3
"""
Android ADB Admin - Lanceur

Permet de démarrer simplement le projet avec :

    python admin.py

même sans activer manuellement .lib_venv.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".lib_venv" / "bin" / "python"
MAIN_SCRIPT = BASE_DIR / "admin-adb.py"


def main() -> None:
    if not MAIN_SCRIPT.is_file():
        raise SystemExit(
            f"Erreur : programme principal introuvable : {MAIN_SCRIPT}"
        )

    if not VENV_PYTHON.is_file():
        raise SystemExit(
            "Erreur : .lib_venv est absent.\n"
            "Exécute d'abord : ./install.sh"
        )

    # Si admin.py a été lancé avec le Python système, on relance
    # automatiquement le vrai programme avec le Python du venv.
    current_python = Path(sys.executable).resolve()
    wanted_python = VENV_PYTHON.resolve()

    if current_python != wanted_python:
        os.execv(
            str(wanted_python),
            [str(wanted_python), str(MAIN_SCRIPT), *sys.argv[1:]],
        )

    # Cas où admin.py est déjà exécuté dans .lib_venv.
    os.execv(
        str(wanted_python),
        [str(wanted_python), str(MAIN_SCRIPT), *sys.argv[1:]],
    )


if __name__ == "__main__":
    main()
