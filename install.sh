#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Android ADB Admin - Installation automatique
# Linux Debian/Ubuntu/Mint/Kali + Termux
#
# Après installation :
#     python admin.py
#
# Le script :
# - détecte Linux/Termux
# - installe Python, pip, venv et ADB si nécessaire
# - crée .lib_venv
# - installe requirements.txt
# - crée admin.py comme lanceur du venv
# - vérifie la syntaxe du programme principal
# ============================================================

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

VENV_DIR="$PROJECT_DIR/.lib_venv"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

# Nom réel du programme principal.
# Le projet actuel utilise admin-adb.py.
MAIN_SCRIPT="$PROJECT_DIR/admin-adb.py"

# Le lanceur que l'utilisateur exécutera ensuite :
LAUNCHER="$PROJECT_DIR/admin.py"

info()  { printf '\033[1;36m[INFO]\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m[ OK ]\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
error() { printf '\033[1;31m[ERR ]\033[0m %s\n' "$*" >&2; }

trap 'error "Installation interrompue à la ligne $LINENO."' ERR

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_termux() {
    [[ -n "${TERMUX_VERSION:-}" ]] || [[ "${PREFIX:-}" == *"com.termux"* ]]
}

run_root() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
    elif command_exists sudo; then
        sudo "$@"
    else
        error "Cette opération nécessite les droits administrateur et sudo est absent."
        exit 1
    fi
}

install_termux() {
    info "Environnement Termux détecté."

    if ! command_exists pkg; then
        error "La commande pkg est introuvable."
        exit 1
    fi

    info "Mise à jour des dépôts Termux..."
    pkg update -y

    info "Installation de Python et ADB..."
    pkg install -y python android-tools

    # Sur Termux, le module venv est fourni avec Python.
    ok "Dépendances système Termux installées."
}

install_apt_linux() {
    info "Distribution Linux compatible apt détectée."

    if ! command_exists apt-get; then
        error "apt-get est introuvable. Distribution non prise en charge automatiquement."
        exit 1
    fi

    info "Mise à jour de l'index des paquets..."
    run_root apt-get update

    info "Installation de Python, pip, venv et ADB..."
    run_root apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        adb

    ok "Dépendances système Linux installées."
}

check_project_files() {
    if [[ ! -f "$MAIN_SCRIPT" ]]; then
        error "Fichier principal introuvable : $MAIN_SCRIPT"
        error "Place install.sh dans le même dossier que admin-adb.py."
        exit 1
    fi

    if [[ ! -f "$REQUIREMENTS" ]]; then
        warn "requirements.txt absent : création d'un fichier vide."
        : > "$REQUIREMENTS"
    fi
}

select_python() {
    if command_exists python3; then
        SYSTEM_PYTHON="$(command -v python3)"
    elif command_exists python; then
        SYSTEM_PYTHON="$(command -v python)"
    else
        error "Python n'est toujours pas disponible après installation."
        exit 1
    fi

    info "Python système : $SYSTEM_PYTHON"
    "$SYSTEM_PYTHON" --version
}

create_venv() {
    if [[ -x "$VENV_DIR/bin/python" ]]; then
        info "Environnement .lib_venv déjà présent."
    else
        info "Création de l'environnement Python .lib_venv..."
        "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
    fi

    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        error "Impossible de créer $VENV_DIR."
        exit 1
    fi

    VENV_PYTHON="$VENV_DIR/bin/python"
    ok "Environnement Python prêt."
}

install_python_requirements() {
    info "Mise à jour de pip dans .lib_venv..."
    "$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

    if [[ -s "$REQUIREMENTS" ]]; then
        info "Installation de requirements.txt..."
        "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS"
    else
        warn "requirements.txt est vide : aucune dépendance Python supplémentaire."
    fi

    ok "Dépendances Python installées."
}

create_launcher() {
    info "Création du lanceur admin.py..."

    cat > "$LAUNCHER" <<'PY'
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
PY

    chmod +x "$LAUNCHER"
    ok "admin.py créé."
}

verify_installation() {
    info "Vérification de la syntaxe Python..."

    "$VENV_PYTHON" -m py_compile "$MAIN_SCRIPT"
    "$VENV_PYTHON" -m py_compile "$LAUNCHER"

    ok "Syntaxe Python valide."

    if command_exists adb; then
        ok "ADB détecté : $(command -v adb)"
        adb version | head -n 1 || true
    else
        warn "ADB n'est pas présent dans le PATH."
    fi
}

print_finish() {
    printf '\n'
    printf '============================================================\n'
    printf ' Android ADB Admin - Installation terminée\n'
    printf '============================================================\n'
    printf '\n'
    printf 'Environnement : %s\n' "$VENV_DIR"
    printf 'Programme      : %s\n' "$MAIN_SCRIPT"
    printf 'Lanceur        : %s\n' "$LAUNCHER"
    printf '\n'
    printf 'À partir de maintenant, ne relance pas install.sh.\n'
    printf '\n'
    printf 'Lance simplement :\n'
    printf '\n'
    printf '    cd "%s"\n' "$PROJECT_DIR"
    printf '    python admin.py\n'
    printf '\n'

    if ! command_exists python && command_exists python3; then
        printf 'Sur ce système, la commande "python" n’existe pas.\n'
        printf 'Utilise alors :\n\n'
        printf '    python3 admin.py\n\n'
    fi
}

main() {
    printf '\n'
    printf '============================================================\n'
    printf ' Android ADB Admin - Installation\n'
    printf '============================================================\n\n'

    check_project_files

    if is_termux; then
        install_termux
    elif command_exists apt-get; then
        install_apt_linux
    else
        error "Système non reconnu automatiquement."
        error "Versions prises en charge par cet installateur :"
        error "  - Termux"
        error "  - Debian"
        error "  - Ubuntu"
        error "  - Linux Mint"
        error "  - Kali Linux"
        exit 1
    fi

    select_python
    create_venv
    install_python_requirements
    create_launcher
    verify_installation
    print_finish
}

main "$@"
