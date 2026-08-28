#!/usr/bin/env bash
# Installa la dashboard token usage di Claude Code sul PC corrente (macOS/Linux):
# - verifica/offre di installare python3 se manca o non funziona
# - copia gli hook (Python puro) in ~/.claude/hooks
# - registra gli hook Stop/PostToolUse in ~/.claude/settings.json in "exec form"
#   (command+args, nessuna shell coinvolta)
# - merge non distruttivo: non tocca hook estranei gia' presenti
#
# Rilanciabile piu' volte: se trova gia' un hook per questi script
# (riconosciuto dal nome file in "args", non dalla stringa comando esatta) ne
# aggiorna la definizione sul posto invece di duplicarla.
#
# Variabile INSTALL_PYTHON=1: salta il prompt e installa direttamente se
# manca (utile per lanci automatizzati/non interattivi).
#
# NOTA: script non testato su una macchina macOS/Linux reale (sviluppato e
# validato solo su Windows) -- verificare al primo utilizzo, specialmente i
# rami dei singoli package manager.
# [EN] Installs the Claude Code token usage dashboard on the current PC
# [EN] (macOS/Linux):
# [EN] - checks for / offers to install python3 if missing or not working
# [EN] - copies the hooks (pure Python) into ~/.claude/hooks
# [EN] - registers the Stop/PostToolUse hooks in ~/.claude/settings.json in
# [EN]   "exec form" (command+args, no shell involved)
# [EN] - non-destructive merge: does not touch unrelated hooks already
# [EN]   present
# [EN]
# [EN] Re-runnable multiple times: if it already finds a hook for these
# [EN] scripts (recognized by the file name in "args", not by the exact
# [EN] command string) it updates its definition in place instead of
# [EN] duplicating it.
# [EN]
# [EN] INSTALL_PYTHON=1 variable: skips the prompt and installs directly if
# [EN] missing (useful for automated/non-interactive runs).
# [EN]
# [EN] NOTE: script not tested on a real macOS/Linux machine (developed and
# [EN] validated only on Windows) -- verify on first use, especially the
# [EN] branches for the individual package managers.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="$SCRIPT_DIR/hooks"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DST="$CLAUDE_DIR/hooks"
SETTINGS_PATH="$CLAUDE_DIR/settings.json"

echo "== Installazione dashboard token usage per Claude Code =="
echo

# --- 1. Prerequisito Python -------------------------------------------------
# [EN] --- 1. Python prerequisite ---
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "ATTENZIONE: python3 non risulta funzionante su questo PC."
    if [ "$(uname)" = "Darwin" ]; then
        echo "Su macOS puo' bastare lanciare 'python3 --version' una volta: se non e'"
        echo "installato, macOS offre di installare i Command Line Tools (che includono"
        echo "python3)."
    fi
    echo

    reply=""
    if [ "${INSTALL_PYTHON:-}" = "1" ]; then
        reply="s"
    elif [ -t 0 ]; then
        read -r -p "Vuoi provare a installarlo ora? (S/n) " reply
    fi

    if [ -z "$reply" ] || [[ "$reply" =~ ^[Ss] ]]; then
        if command -v brew >/dev/null 2>&1; then
            echo "Installazione via Homebrew..."
            brew install python3 || true
        elif command -v apt-get >/dev/null 2>&1; then
            echo "Installazione via apt-get (potrebbe chiedere la password sudo)..."
            sudo apt-get update && sudo apt-get install -y python3 || true
        elif command -v dnf >/dev/null 2>&1; then
            echo "Installazione via dnf (potrebbe chiedere la password sudo)..."
            sudo dnf install -y python3 || true
        elif command -v pacman >/dev/null 2>&1; then
            echo "Installazione via pacman (potrebbe chiedere la password sudo)..."
            sudo pacman -Sy --noconfirm python3 || true
        elif [ "$(uname)" = "Darwin" ]; then
            echo "Lancio 'python3 --version' per innescare l'eventuale prompt dei Command Line Tools..."
            python3 --version || true
            echo "Segui la finestra di dialogo (se compare), poi rilancia questo script."
        else
            echo "Nessun gestore pacchetti noto trovato (brew/apt-get/dnf/pacman)."
            echo "Installa Python 3 manualmente e rilancia questo script."
        fi
    else
        echo "Ok, installa Python 3 manualmente e rilancia questo script."
    fi
    echo

    if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    fi
fi

# --- 2. Copia gli hook -------------------------------------------------------
# [EN] --- 2. Copy the hooks ---
mkdir -p "$HOOKS_DST"
cp "$HOOKS_SRC"/*.py "$HOOKS_DST/"
cp -r "$HOOKS_SRC"/generate_dashboard "$HOOKS_DST/"
# generate_dashboard.py (file singolo) e' stato sostituito da generate_dashboard/
# (package): se un'installazione precedente l'ha lasciato sul PC, va tolto --
# altrimenti resterebbe un modulo vecchio e inerte accanto al package nuovo.
# Non fatale (|| true): il package appena copiato ha comunque la precedenza
# sul file piatto nell'import di Python, quindi anche se questa pulizia
# fallisse l'installazione resta funzionante.
# [EN] generate_dashboard.py (single file) has been replaced by
# [EN] generate_dashboard/ (package): if a previous installation left it on
# [EN] the PC, it must be removed -- otherwise an old, inert module would
# [EN] remain next to the new package.
# [EN] Non-fatal (|| true): the just-copied package takes precedence over
# [EN] the flat file in Python's import anyway, so even if this cleanup
# [EN] failed the installation remains functional.
rm -f "$HOOKS_DST/generate_dashboard.py" || true
echo "Hook copiati in: $HOOKS_DST"

# --- 3. Merge di settings.json (richiede python3) ---------------------------
# [EN] --- 3. Merge settings.json (requires python3) ---
if [ -z "$PYTHON_BIN" ]; then
    echo "python3 non e' ancora disponibile: hook copiati, ma non posso registrarli"
    echo "in settings.json senza Python. Rilancia questo script dopo averlo installato."
else
    "$PYTHON_BIN" - "$SETTINGS_PATH" "$HOOKS_DST" <<'PYEOF'
import json
import os
import sys

settings_path, hooks_dst = sys.argv[1], sys.argv[2]

if os.path.exists(settings_path):
    with open(settings_path, encoding="utf-8") as f:
        raw = f.read().strip()
    settings = json.loads(raw) if raw else {}
else:
    settings = {}

settings.setdefault("hooks", {})


def set_exec_hook(event_name, script_filename, timeout, matcher=None):
    groups = settings["hooks"].setdefault(event_name, [])
    script_path = os.path.join(hooks_dst, script_filename)

    # Riconosce un hook gia' registrato per questo script dal nome file in
    # "args" (non dalla stringa comando esatta, che cambia da una versione
    # all'altra): se trovato lo aggiorna sul posto invece di duplicarlo.
    # [EN] Recognizes a hook already registered for this script by the file
    # [EN] name in "args" (not by the exact command string, which changes
    # [EN] from one version to the next): if found, it updates it in place
    # [EN] instead of duplicating it.
    for g in groups:
        for h in g.get("hooks", []):
            args = h.get("args") or []
            if any(a.endswith(script_filename) for a in args):
                h["command"] = "python3"
                h["args"] = [script_path]
                h["timeout"] = timeout
                return

    new_hook = {"type": "command", "command": "python3", "args": [script_path], "timeout": timeout}
    new_group = {"hooks": [new_hook]}
    if matcher:
        new_group["matcher"] = matcher
    groups.append(new_group)


set_exec_hook("Stop", "log_tokens.py", 15)
set_exec_hook("PostToolUse", "log_operation.py", 15, matcher=".*")

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
PYEOF
    echo "Hook registrati in: $SETTINGS_PATH"
fi

# --- 4. Riepilogo -------------------------------------------------------------
# [EN] --- 4. Summary ---
echo
echo "Fatto."
echo "Riavvia Claude Code se era gia' aperto (gli hook si applicano dalla"
echo "prossima sessione). Alla fine del primo turno successivo trovi la"
echo "dashboard in: $CLAUDE_DIR/dashboard-token/dashboard.html"
echo
echo "Personalizzazioni facoltative (create in $HOOKS_DST):"
echo '  - dashboard_config.json  { "out_dir": "/percorso/a/piacere" }'
echo '  - account_labels.json    { "<uuid-account>": "etichetta leggibile" }'
