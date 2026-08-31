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

# La lingua dei messaggi di questo script. Non passa dal dizionario Python
# del progetto, e non per pigrizia: quando questo script gira, Python
# potrebbe non esserci ancora -- e' anzi il caso che poco piu' sotto viene
# gestito esplicitamente, offrendosi di installarlo. Un installer che ha
# bisogno di Python per dire "Python non c'e'" non servirebbe a niente.
# Stessi indizi della catena in i18n.cli_lang(): la variabile d'ambiente per
# un singolo lancio, poi le variabili di locale del sistema, l'inglese per
# ultimo.
#
# NIENTE array associativi (declare -A): macOS spedisce ancora bash 3.2, che
# non li ha, ed e' proprio il sistema su cui questo script gira di piu'. Si
# usano quindi variabili con un prefisso di lingua e l'espansione indiretta
# ${!nome}, che bash 3.2 conosce.
#
# I messaggi che finiscono con i due punti vogliono un valore incollato dopo
# dal punto di chiamata: cosi' i percorsi restano fuori dai messaggi e chi
# traduce non deve sapere come si scrive un segnaposto in bash.
# [EN] The language of this script's messages. It does not go through the
# project's Python dictionary, and not out of laziness: when this script
# runs, Python may not be there yet -- that is in fact the case handled
# explicitly a little further down, by offering to install it. An installer
# that needs Python in order to say "Python is missing" would be of no use.
# Same clues as the chain in i18n.cli_lang(): the environment variable for a
# single run, then the system's locale variables, English last.
#
# NO associative arrays (declare -A): macOS still ships bash 3.2, which does
# not have them, and that is precisely the system this script runs on most.
# So we use variables with a language prefix and the indirect expansion
# ${!name}, which bash 3.2 does know.
#
# Messages ending in a colon want a value glued after them by the call site:
# this keeps paths out of the messages, and whoever translates need not know
# how a placeholder is written in bash.
case "${DASHBOARD_TOKEN_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    it*|IT*) L=IT ;;
    *)       L=EN ;;
esac

IT_title='== Installazione dashboard token usage per Claude Code =='
IT_pyMissing='ATTENZIONE: python3 non risulta funzionante su questo PC.'
IT_macHint1='Su macOS puo'\'' bastare lanciare '\''python3 --version'\'' una volta: se non e'\'''
IT_macHint2='installato, macOS offre di installare i Command Line Tools (che includono'
IT_macHint3='python3).'
IT_viaBrew='Installazione via Homebrew...'
IT_viaApt='Installazione via apt-get (potrebbe chiedere la password sudo)...'
IT_viaDnf='Installazione via dnf (potrebbe chiedere la password sudo)...'
IT_viaPacman='Installazione via pacman (potrebbe chiedere la password sudo)...'
IT_triggerClt='Lancio '\''python3 --version'\'' per innescare l'\''eventuale prompt dei Command Line Tools...'
IT_followDialog='Segui la finestra di dialogo (se compare), poi rilancia questo script.'
IT_noPkgMgr='Nessun gestore pacchetti noto trovato (brew/apt-get/dnf/pacman).'
IT_installManually='Installa Python 3 manualmente e rilancia questo script.'
IT_pyDeclined='Ok, installa Python 3 manualmente e rilancia questo script.'
IT_hooksCopied='Hook copiati in:'
IT_noPySettings1='python3 non e'\'' ancora disponibile: hook copiati, ma non posso registrarli'
IT_noPySettings2='in settings.json senza Python. Rilancia questo script dopo averlo installato.'
IT_hooksRegistered='Hook registrati in:'
IT_done='Fatto.'
IT_restart1='Riavvia Claude Code se era gia'\'' aperto (gli hook si applicano dalla'
IT_restart2='prossima sessione). Alla fine del primo turno successivo trovi la'
IT_dashboardIn='dashboard in:'
IT_optional='Personalizzazioni facoltative (create in'
IT_optOutDir='  - dashboard_config.json  { "out_dir": "/percorso/a/piacere" }'
IT_optLabels='  - account_labels.json    { "<uuid-account>": "etichetta leggibile" }'
IT_optLang='  - dashboard_config.json  { "lang": "en" }  (lingua dei messaggi a terminale)'
EN_title='== Installing the Claude Code token usage dashboard =='
EN_pyMissing='WARNING: python3 does not appear to work on this PC.'
EN_macHint1='On macOS running '\''python3 --version'\'' once may be enough: if it is not'
EN_macHint2='installed, macOS offers to install the Command Line Tools (which include'
EN_macHint3='python3).'
EN_viaBrew='Installing via Homebrew...'
EN_viaApt='Installing via apt-get (it may ask for the sudo password)...'
EN_viaDnf='Installing via dnf (it may ask for the sudo password)...'
EN_viaPacman='Installing via pacman (it may ask for the sudo password)...'
EN_triggerClt='Running '\''python3 --version'\'' to trigger the Command Line Tools prompt, if any...'
EN_followDialog='Follow the dialog (if it appears), then run this script again.'
EN_noPkgMgr='No known package manager found (brew/apt-get/dnf/pacman).'
EN_installManually='Install Python 3 by hand and run this script again.'
EN_pyDeclined='All right, install Python 3 by hand and run this script again.'
EN_hooksCopied='Hooks copied to:'
EN_noPySettings1='python3 is not available yet: hooks copied, but they cannot be registered'
EN_noPySettings2='in settings.json without Python. Run this script again once it is installed.'
EN_hooksRegistered='Hooks registered in:'
EN_done='Done.'
EN_restart1='Restart Claude Code if it was already open (the hooks apply from the'
EN_restart2='next session). At the end of the first turn after that you will find the'
EN_dashboardIn='dashboard in:'
EN_optional='Optional customisations (create them in'
EN_optOutDir='  - dashboard_config.json  { "out_dir": "/any/path/you/like" }'
EN_optLabels='  - account_labels.json    { "<account-uuid>": "readable label" }'
EN_optLang='  - dashboard_config.json  { "lang": "it" }  (language of the terminal messages)'

msg() {
    local __chiave="${L}_$1"
    printf '%s\n' "${!__chiave}"
}

msg title
echo

# --- 1. Prerequisito Python -------------------------------------------------
# [EN] --- 1. Python prerequisite ---
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

if [ -z "$PYTHON_BIN" ]; then
    msg pyMissing
    if [ "$(uname)" = "Darwin" ]; then
        msg macHint1
        msg macHint2
        msg macHint3
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
            msg viaBrew
            brew install python3 || true
        elif command -v apt-get >/dev/null 2>&1; then
            msg viaApt
            sudo apt-get update && sudo apt-get install -y python3 || true
        elif command -v dnf >/dev/null 2>&1; then
            msg viaDnf
            sudo dnf install -y python3 || true
        elif command -v pacman >/dev/null 2>&1; then
            msg viaPacman
            sudo pacman -Sy --noconfirm python3 || true
        elif [ "$(uname)" = "Darwin" ]; then
            msg triggerClt
            python3 --version || true
            msg followDialog
        else
            msg noPkgMgr
            msg installManually
        fi
    else
        msg pyDeclined
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
echo "$(msg hooksCopied) $HOOKS_DST"

# --- 3. Merge di settings.json (richiede python3) ---------------------------
# [EN] --- 3. Merge settings.json (requires python3) ---
if [ -z "$PYTHON_BIN" ]; then
    msg noPySettings1
    msg noPySettings2
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
    echo "$(msg hooksRegistered) $SETTINGS_PATH"
fi

# --- 4. Riepilogo -------------------------------------------------------------
# [EN] --- 4. Summary ---
echo
msg done
msg restart1
msg restart2
echo "$(msg dashboardIn) $CLAUDE_DIR/dashboard-token/dashboard.html"
echo
echo "$(msg optional) $HOOKS_DST):"
msg optOutDir
msg optLang
msg optLabels
