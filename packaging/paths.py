"""Percorsi condivisi, e distinzione fra i due binari che produciamo.

La distribuzione e' a due stadi, per una ragione di velocita' misurata:

 - l'INSTALLER e' un file unico (onefile), quello che si scarica dalle
   Release. Dentro si porta, come dato impacchettato, l'intera applicazione;

 - l'APPLICAZIONE e' in forma "onedir" (un exe + una cartella _internal) e
   viene estratta dall'installer in ~/.claude/hooks/dashboard-token/. E' la
   forma registrata negli hook di settings.json.

Perche' non usare l'installer onefile anche come applicazione: un binario
onefile si scompatta in una cartella temporanea a OGNI avvio, il che costa
~880 ms. L'hook PostToolUse scatta a ogni singola chiamata di strumento,
quindi quel costo si moltiplica per tutto il turno. La forma onedir parte in
~225 ms -- piu' veloce persino dell'installazione a script Python (~320 ms).

Chi installa scarica comunque un file solo: la complicazione resta tutta
interna al progetto.

[EN] Shared paths, and the distinction between the two binaries we produce.

Distribution is two-stage, for a measured speed reason:

 - the INSTALLER is a single file (onefile), the one downloaded from the
   Releases. It carries, as bundled data, the whole application;

 - the APPLICATION is in "onedir" form (an exe plus an _internal folder)
   and is extracted by the installer into ~/.claude/hooks/dashboard-token/.
   It is the form registered in the settings.json hooks.

Why not use the onefile installer as the application too: a onefile binary
unpacks itself into a temporary folder on EVERY start, which costs
~880 ms. The PostToolUse hook fires on every single tool call, so that
cost multiplies across the whole turn. The onedir form starts in ~225 ms
-- faster even than the Python-script installation (~320 ms).

Whoever installs it still downloads just one file: the complication stays
entirely inside the project.
"""
import os
import sys

HOME = os.path.expanduser("~")
CLAUDE_DIR = os.path.join(HOME, ".claude")
HOOKS_DIR = os.path.join(CLAUDE_DIR, "hooks")
SETTINGS_PATH = os.path.join(CLAUDE_DIR, "settings.json")

# Cartella in cui vive l'applicazione installata, e l'eseguibile dentro di
# essa. Sta sotto ~/.claude/hooks/ perche' e' scrivibile dall'utente senza
# diritti di amministratore -- condizione necessaria all'auto-update.
# [EN] Folder where the installed application lives, and the executable
# inside it. It sits under ~/.claude/hooks/ because the user can write
# there without administrator rights -- a necessary condition for the
# auto-update.
INSTALL_DIR = os.path.join(HOOKS_DIR, "dashboard-token")
APP_NAME = "dashboard-token.exe" if sys.platform == "win32" else "dashboard-token"
APP_EXE = os.path.join(INSTALL_DIR, APP_NAME)

# Nomi temporanei usati durante la sostituzione della cartella (vedi
# setup_hooks._install_app): si estrae in .new, si sposta la vecchia da
# parte, si mette la nuova al suo posto, si cancella quella vecchia.
# [EN] Temporary names used while swapping the folder (see
# setup_hooks._install_app): extract into .new, move the old one aside,
# put the new one in its place, delete the old one.
INSTALL_DIR_NEW = INSTALL_DIR + ".new"

# La cartella da rottamare prende un nome con un numero progressivo invece
# di un ".old" fisso: se la cancellazione fallisce (su Windows i file di un
# eseguibile appena uscito restano bloccati per qualche istante), il
# tentativo successivo non trova il nome gia' occupato e non si impianta.
# [EN] The folder to be scrapped gets a name with an increasing number
# instead of a fixed ".old": if deletion fails (on Windows the files of an
# executable that just exited stay locked for a few moments), the next
# attempt does not find the name already taken and does not get stuck.
INSTALL_DIR_OLD_PREFIX = INSTALL_DIR + ".old-"

# Diario dell'installazione. Serve perche' l'aggiornamento automatico gira
# in un processo staccato, con stdout e stderr su DEVNULL: senza un file su
# cui scrivere, un fallimento sarebbe completamente muto e l'utente
# resterebbe su una versione vecchia per sempre senza il minimo indizio.
# [EN] Installation journal. Needed because the automatic update runs in a
# detached process, with stdout and stderr on DEVNULL: without a file to
# write to, a failure would be completely silent and the user would stay
# on an old version forever without the slightest clue.
INSTALL_LOG = os.path.join(HOOKS_DIR, "dashboard-token-install.log")

# File-timbro dell'ultimo controllo aggiornamenti. Sta FUORI da INSTALL_DIR
# di proposito: dentro verrebbe spazzato via a ogni aggiornamento, e il
# controllo ripartirebbe da zero ogni volta.
# [EN] Stamp file of the last update check. It sits OUTSIDE INSTALL_DIR on
# purpose: inside it would get swept away at every update, and the check
# would start over from scratch every time.
UPDATE_STAMP = os.path.join(HOOKS_DIR, ".dashboard-token-update-check")

# Nome della cartella in cui l'installer si porta dentro l'applicazione.
# Deve combaciare con la destinazione dichiarata in packaging/installer.spec.
# [EN] Name of the folder in which the installer carries the application.
# Must match the destination declared in packaging/installer.spec.
_PAYLOAD_DIR_NAME = "payload"


def is_frozen():
    """True se stiamo girando dentro un eseguibile impacchettato.

    [EN] True if we are running inside a packaged executable."""
    return getattr(sys, "frozen", False)


def current_exe():
    """Percorso dell'eseguibile in esecuzione, o None se stiamo girando dai
    sorgenti Python (dove non c'e' nulla da installare o aggiornare).

    [EN] Path of the running executable, or None if we are running from
    the Python sources (where there is nothing to install or update)."""
    if is_frozen():
        return os.path.abspath(sys.executable)
    return None


def bundled_payload():
    """Percorso dell'applicazione impacchettata dentro questo binario, se
    c'e'; altrimenti None.

    E' cosi' che lo stesso cli.py distingue i due ruoli senza bisogno di due
    basi di codice separate: se il payload c'e', siamo l'installer; se non
    c'e', siamo l'applicazione installata.

    [EN] Path of the application bundled inside this binary, if any;
    otherwise None.

    This is how the same cli.py tells the two roles apart without needing
    two separate codebases: if the payload is there, we are the installer;
    if it is not, we are the installed application.
    """
    if not is_frozen():
        return None
    payload = os.path.join(sys._MEIPASS, _PAYLOAD_DIR_NAME)
    return payload if os.path.isdir(payload) else None


def is_installer():
    """True se questo binario e' l'installer (quello scaricato da GitHub).

    [EN] True if this binary is the installer (the one downloaded from
    GitHub)."""
    return bundled_payload() is not None
