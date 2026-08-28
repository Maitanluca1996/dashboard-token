"""Installazione: estrae l'applicazione in ~/.claude/hooks/dashboard-token/
e registra gli hook Stop / PostToolUse in ~/.claude/settings.json.

E' il porting in Python di installer/install.ps1, con tre differenze:

 - il comando registrato non e' piu' "python3 <percorso>/log_tokens.py" ma
   l'applicazione con un sottocomando ("<...>/dashboard-token.exe
   log-tokens"), quindi sulla macchina di destinazione non serve Python;

 - riconosce e MIGRA una vecchia installazione basata su Python, invece di
   affiancarsi ad essa (altrimenti ogni turno verrebbe loggato due volte);

 - installa una CARTELLA e non un singolo file, per la ragione di velocita'
   spiegata in paths.py.

Come install.ps1, il merge di settings.json e' non distruttivo: hook di
altri strumenti eventualmente presenti non vengono toccati, e rilanciare
l'installazione piu' volte aggiorna la definizione sul posto senza creare
doppioni.

Nota deliberata: l'installazione NON cancella i vecchi log_tokens.py /
log_operation.py / generate_dashboard/ eventualmente presenti in
~/.claude/hooks/. Sono inerti una volta che settings.json punta all'app, e
quella cartella puo' contenere una copia di lavoro dei sorgenti:
cancellarla distruggerebbe dati dell'utente.

[EN] Installation: extracts the application into
~/.claude/hooks/dashboard-token/ and registers the Stop / PostToolUse
hooks in ~/.claude/settings.json.

It is the Python port of installer/install.ps1, with three differences:

 - the registered command is no longer "python3 <path>/log_tokens.py" but
   the application with a subcommand ("<...>/dashboard-token.exe
   log-tokens"), so the target machine needs no Python at all;

 - it recognizes and MIGRATES an old Python-based installation, instead of
   sitting next to it (otherwise every turn would be logged twice);

 - it installs a FOLDER and not a single file, for the speed reason
   explained in paths.py.

As with install.ps1, the settings.json merge is non-destructive: hooks of
other tools that happen to be present are left untouched, and rerunning
the installation multiple times updates the definition in place without
creating duplicates.

Deliberate note: the installation does NOT delete the old log_tokens.py /
log_operation.py / generate_dashboard/ possibly present in
~/.claude/hooks/. They are inert once settings.json points to the app, and
that folder may hold a working copy of the sources: deleting it would
destroy the user's data.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

import paths
from version import GITHUB_REPO, VERSION

# Timeout (secondi) concesso da Claude Code a ciascun hook. Lo stesso valore
# usato da install.ps1.
# [EN] Timeout (seconds) that Claude Code grants each hook. The same value
# used by install.ps1.
HOOK_TIMEOUT = 15

# Quanto insistere nel sostituire la cartella dell'applicazione. Serve
# quando l'aggiornamento parte mentre un turno di Claude Code e' ancora in
# corso: finche' l'app installata gira, Windows non lascia rinominare la
# cartella che la contiene. Un turno lungo puo' durare parecchio, quindi si
# riprova con pazienza; se proprio non si riesce, l'aggiornamento salta e si
# ritenta il giorno dopo -- nessun danno.
# [EN] How persistently to try replacing the application folder. Needed
# when the update starts while a Claude Code turn is still in progress: as
# long as the installed app is running, Windows will not let the folder
# containing it be renamed. A long turn can last quite a while, so we
# retry patiently; if it really cannot be done, the update is skipped and
# retried the next day -- no harm done.
SWAP_TIMEOUT = 120
SWAP_RETRY_DELAY = 3


def _load_settings():
    """Legge settings.json restituendo un dizionario. Un file assente, vuoto
    o illeggibile da' semplicemente un dizionario vuoto: e' il caso di chi
    non ha mai configurato nulla.

    [EN] Reads settings.json returning a dictionary. A missing, empty or
    unreadable file simply yields an empty dictionary: that is the case of
    someone who has never configured anything."""
    try:
        with open(paths.SETTINGS_PATH, encoding="utf-8-sig") as f:
            raw = f.read()
    except OSError:
        return {}
    if not raw.strip():
        return {}
    return json.loads(raw)


def _save_settings(settings):
    """Scrive settings.json in modo atomico: prima su un file temporaneo,
    poi os.replace() che sostituisce l'originale in un'unica operazione
    indivisibile. Cosi' un'interruzione a meta' (crash, PC spento) non puo'
    lasciare il settings.json dell'utente troncato o corrotto.

    [EN] Writes settings.json atomically: first to a temporary file, then
    os.replace(), which swaps in the original in a single indivisible
    operation. This way an interruption halfway through (crash, PC powered
    off) cannot leave the user's settings.json truncated or corrupted."""
    tmp = paths.SETTINGS_PATH + ".tmp"
    text = json.dumps(settings, indent=2, ensure_ascii=False)
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    os.replace(tmp, paths.SETTINGS_PATH)


def _backup_settings():
    """Copia di sicurezza di settings.json prima di modificarlo. Sovrascrive
    il backup precedente: serve a rimediare subito a un'installazione andata
    male, non a tenere uno storico.

    [EN] Safety copy of settings.json before modifying it. Overwrites the
    previous backup: it is there to fix a botched installation right away,
    not to keep a history."""
    if os.path.exists(paths.SETTINGS_PATH):
        try:
            shutil.copy2(paths.SETTINGS_PATH, paths.SETTINGS_PATH + ".bak")
        except OSError:
            # non fatale: il backup e' un extra, non un requisito
            # [EN] not fatal: the backup is an extra, not a requirement
            pass


# Oltre questa dimensione il diario viene ripartito da zero: e' una
# diagnostica, non un archivio storico.
# [EN] Beyond this size the journal is restarted from scratch: it is a
# diagnostic aid, not a historical archive.
LOG_MAX_BYTES = 200 * 1024


def _make_logger():
    """Restituisce una funzione log() che stampa E scrive su INSTALL_LOG.

    La stampa serve a chi lancia l'installer col doppio click; il file serve
    a tutti gli altri casi, cioe' l'aggiornamento automatico, dove non c'e'
    nessuna console a cui parlare.

    [EN] Returns a log() function that prints AND writes to INSTALL_LOG.

    Printing serves whoever launches the installer with a double click; the
    file serves every other case, i.e. the automatic update, where there is
    no console to talk to.
    """
    try:
        os.makedirs(paths.HOOKS_DIR, exist_ok=True)
        if (os.path.exists(paths.INSTALL_LOG)
                and os.path.getsize(paths.INSTALL_LOG) > LOG_MAX_BYTES):
            os.remove(paths.INSTALL_LOG)
    except OSError:
        pass

    def log(message):
        print(message)
        try:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(paths.INSTALL_LOG, "a", encoding="utf-8") as f:
                f.write("{} {}\n".format(stamp, message))
        except OSError:
            # Se non riusciamo a scrivere il diario pazienza: non deve mai
            # essere il diario a far fallire un'installazione.
            # [EN] If we cannot write the journal, so be it: the journal
            # must never be what makes an installation fail.
            pass

    return log


def _remove_tree(path):
    """Cancella una cartella ignorando i fallimenti. Su Windows i file di un
    processo appena terminato possono restare bloccati per qualche istante:
    non e' un errore da propagare, al massimo si ritenta piu' tardi.

    [EN] Deletes a folder ignoring failures. On Windows the files of a
    process that just ended can stay locked for a few moments: not an error
    to propagate, at most we retry later."""
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


def sweep_old_installs():
    """Rimuove le cartelle .old-* rimaste da aggiornamenti precedenti.
    Chiamata all'avvio dell'applicazione, quando ormai nessuno le usa.

    [EN] Removes the .old-* folders left over by previous updates. Called
    at application startup, when nothing uses them any more."""
    for leftover in glob.glob(paths.INSTALL_DIR_OLD_PREFIX + "*"):
        _remove_tree(leftover)


def _rename_with_retry(src, dst, deadline, log, what):
    """Rinomina una cartella insistendo finche' non ci riesce o scade il tempo.

    Su Windows os.rename di una cartella fallisce con "accesso negato" se un
    file al suo interno e' ancora aperto da qualcuno -- l'applicazione in
    esecuzione dentro un turno di Claude Code, o l'antivirus che sta
    scandendo file appena scritti. In entrambi i casi e' una condizione
    passeggera: basta riprovare qualche secondo dopo.

    [EN] Renames a folder, insisting until it succeeds or time runs out.

    On Windows os.rename of a folder fails with "access denied" if a file
    inside it is still open by someone -- the application running inside a
    Claude Code turn, or the antivirus scanning freshly written files. In
    both cases it is a passing condition: just retry a few seconds later.
    """
    while True:
        try:
            os.rename(src, dst)
            return
        except OSError as exc:
            if time.time() >= deadline:
                raise RuntimeError("{} ({}).".format(what, exc))
            log("{}, riprovo fra {} secondi...".format(what, SWAP_RETRY_DELAY))
            time.sleep(SWAP_RETRY_DELAY)


def _install_app(payload, log):
    """Mette l'applicazione contenuta nell'installer al suo posto.

    Sequenza: si estrae la nuova versione accanto a quella vecchia, poi si
    scambiano i nomi. Cosi' l'installazione esistente resta intatta e
    funzionante fino all'ultimo istante, e se qualcosa va storto durante
    l'estrazione non si e' rotto nulla.

    [EN] Puts the application contained in the installer into place.

    Sequence: the new version is extracted next to the old one, then the
    names are swapped. This way the existing installation stays intact and
    working until the very last moment, and if something goes wrong during
    extraction nothing has been broken.
    """
    os.makedirs(paths.HOOKS_DIR, exist_ok=True)
    sweep_old_installs()
    _remove_tree(paths.INSTALL_DIR_NEW)

    shutil.copytree(payload, paths.INSTALL_DIR_NEW)
    if sys.platform != "win32":
        os.chmod(os.path.join(paths.INSTALL_DIR_NEW, paths.APP_NAME), 0o755)

    retired = paths.INSTALL_DIR_OLD_PREFIX + str(int(time.time()))
    deadline = time.time() + SWAP_TIMEOUT

    # ENTRAMBE le rinomine vanno ritentate, non solo la prima. Su Windows
    # una cartella non si lascia rinominare finche' qualcosa al suo interno
    # e' aperto, e questo vale sia per quella vecchia (l'app in esecuzione
    # dentro un turno) sia per quella nuova appena scritta (l'antivirus che
    # sta ancora scandendo i 22 MB copiati un istante fa). Con il retry solo
    # sulla prima, il secondo os.rename falliva al primo colpo e l'intero
    # aggiornamento veniva annullato -- in silenzio, perche' lanciato
    # staccato non ha nessun output dove lamentarsi.
    # [EN] BOTH renames must be retried, not just the first. On Windows a
    # folder cannot be renamed while something inside it is open, and this
    # holds both for the old one (the app running inside a turn) and for
    # the freshly written new one (the antivirus still scanning the 22 MB
    # copied a moment ago). With the retry only on the first, the second
    # os.rename failed at the first attempt and the whole update was
    # aborted -- silently, because launched detached it has no output to
    # complain to.
    if os.path.exists(paths.INSTALL_DIR):
        _rename_with_retry(
            paths.INSTALL_DIR, retired, deadline, log,
            "L'installazione esistente e' in uso",
        )

    try:
        _rename_with_retry(
            paths.INSTALL_DIR_NEW, paths.INSTALL_DIR, deadline, log,
            "La nuova installazione non e' ancora libera",
        )
    except (OSError, RuntimeError):
        # Non siamo riusciti a mettere la nuova al suo posto: rimettiamo la
        # vecchia dov'era, cosi' l'utente resta con qualcosa che funziona.
        # [EN] We could not put the new one in place: put the old one back
        # where it was, so the user is left with something that works.
        if os.path.isdir(retired) and not os.path.exists(paths.INSTALL_DIR):
            try:
                os.rename(retired, paths.INSTALL_DIR)
            except OSError:
                pass
        _remove_tree(paths.INSTALL_DIR_NEW)
        raise

    _remove_tree(retired)
    return paths.APP_EXE


def _looks_like_ours(hook, legacy_script, subcommand):
    """Questo hook gia' registrato e' uno dei nostri?

    Due forme possibili:
     - vecchia (installazione via install.cmd): command="python3",
       args=["<...>/log_tokens.py"] -- si riconosce dal nome del file;
     - nuova (applicazione): command="<...>/dashboard-token.exe",
       args=["log-tokens"] -- si riconosce dal sottocomando.

    Come in install.ps1 il riconoscimento NON usa la stringa di comando
    esatta, che cambia da una versione all'altra (e da utente a utente,
    visto che contiene la home): si basa sul nome file / sottocomando.

    [EN] Is this already-registered hook one of ours?

    Two possible forms:
     - old (installation via install.cmd): command="python3",
       args=["<...>/log_tokens.py"] -- recognized by the file name;
     - new (application): command="<...>/dashboard-token.exe",
       args=["log-tokens"] -- recognized by the subcommand.

    As in install.ps1, recognition does NOT use the exact command string,
    which changes from one version to the next (and from user to user,
    since it contains the home): it relies on the file name / subcommand.
    """
    args = hook.get("args") or []
    if not isinstance(args, list):
        args = [args]
    for a in args:
        if isinstance(a, str) and a.replace("\\", "/").endswith(legacy_script):
            return True
    command = hook.get("command") or ""
    if "dashboard-token" in command.replace("\\", "/") and subcommand in args:
        return True
    return False


def _set_exec_hook(hooks_root, event, exe, subcommand, legacy_script, matcher=None):
    """Registra (o aggiorna sul posto) l'hook di un evento in "exec form":
    command + args separati, senza shell di mezzo -- niente bash/Git for
    Windows richiesto, e nessun problema con gli spazi nei percorsi.

    [EN] Registers (or updates in place) the hook of an event in "exec
    form": command + args kept separate, no shell in between -- no
    bash/Git for Windows required, and no trouble with spaces in paths."""
    groups = hooks_root.get(event) or []
    if not isinstance(groups, list):
        groups = [groups]

    definition = {
        "type": "command",
        "command": exe,
        "args": [subcommand],
        "timeout": HOOK_TIMEOUT,
    }

    for group in groups:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks") or []:
            if isinstance(hook, dict) and _looks_like_ours(hook, legacy_script, subcommand):
                # Aggiornamento sul posto: sostituiamo i campi della
                # definizione esistente senza spostarla di gruppo, cosi' un
                # eventuale "matcher" gia' presente resta com'e'.
                # [EN] In-place update: we replace the fields of the
                # existing definition without moving it to another group,
                # so any "matcher" already present stays as it is.
                hook.clear()
                hook.update(definition)
                hooks_root[event] = groups
                return "aggiornato"

    new_group = {"hooks": [definition]}
    if matcher:
        new_group["matcher"] = matcher
    hooks_root[event] = groups + [new_group]
    return "registrato"


def register_hooks(app_exe):
    """Scrive gli hook in settings.json. Restituisce la coppia di esiti
    ("registrato"/"aggiornato") per Stop e PostToolUse.

    [EN] Writes the hooks into settings.json. Returns the pair of outcomes
    ("registrato"/"aggiornato") for Stop and PostToolUse."""
    # Percorso con gli slash in avanti, come gia' faceva install.ps1:
    # Windows li accetta senza problemi, ed evita che nel JSON ogni
    # backslash compaia raddoppiato ("C:\\Users\\...").
    # [EN] Path with forward slashes, as install.ps1 already did: Windows
    # accepts them just fine, and it avoids every backslash showing up
    # doubled in the JSON ("C:\\Users\\...").
    exe = app_exe.replace("\\", "/")

    _backup_settings()
    settings = _load_settings()
    hooks_root = settings.setdefault("hooks", {})
    if not isinstance(hooks_root, dict):
        raise RuntimeError(
            "la chiave hooks in settings.json non ha il formato atteso "
            "(dovrebbe essere un oggetto)"
        )

    stop = _set_exec_hook(hooks_root, "Stop", exe, "log-tokens", "log_tokens.py")
    post = _set_exec_hook(
        hooks_root, "PostToolUse", exe, "log-operation", "log_operation.py", matcher=".*"
    )
    _save_settings(settings)
    return stop, post


def _recupera_storico(app_exe, log):
    """Ricostruisce lo storico delle sessioni gia' aperte prima
    dell'installazione, mostrando una barra di avanzamento.

    Lo fa lanciando l'APPLICAZIONE appena installata come sottoprocesso,
    invece di importare il codice qui: l'installer e' volutamente magro e non
    si porta dentro il package generate_dashboard (vedi installer.spec), che
    invece nell'applicazione c'e'. Il sottoprocesso eredita la console, cosi'
    la barra si disegna nella stessa finestra.

    Un fallimento qui non e' un fallimento dell'installazione: gli hook sono
    gia' registrati e il monitoraggio da qui in avanti funziona comunque.

    [EN] Rebuilds the history of the sessions already open before the
    installation, showing a progress bar.

    It does so by launching the freshly installed APPLICATION as a
    subprocess, instead of importing the code here: the installer is
    deliberately lean and does not carry the generate_dashboard package
    (see installer.spec), which the application does have. The subprocess
    inherits the console, so the bar draws in the same window.

    A failure here is not a failure of the installation: the hooks are
    already registered and monitoring works from here on regardless.
    """
    try:
        subprocess.call([app_exe, "backfill", "--no-pause"])
    except OSError as exc:
        log("Recupero dello storico non riuscito: {}".format(exc))
        log("Puoi rilanciarlo quando vuoi con: {} backfill".format(app_exe))


def install(interactive=True):
    """Installazione completa, eseguita dall'installer scaricato da GitHub.
    Restituisce 0 se e' andata bene.

    [EN] Full installation, performed by the installer downloaded from
    GitHub. Returns 0 on success."""
    log = _make_logger()
    log("== Dashboard token usage per Claude Code -- installazione ==")
    log("   versione {}".format(VERSION))
    log("")

    payload = paths.bundled_payload()
    if payload is None:
        log("ERRORE: questo binario non contiene l'applicazione da installare.")
        log("Scarica l'installer dalle Release del progetto:")
        log("  https://github.com/{}/releases/latest".format(GITHUB_REPO))
        return 1

    try:
        app_exe = _install_app(payload, log)
    except (OSError, RuntimeError) as exc:
        log("ERRORE durante l'installazione: {}".format(exc))
        return 1
    log("Applicazione installata in: {}".format(paths.INSTALL_DIR))

    try:
        stop, post = register_hooks(app_exe)
    except (OSError, ValueError, RuntimeError) as exc:
        log("ERRORE nella scrittura di settings.json: {}".format(exc))
        log("Il file non e' stato modificato (backup in {}.bak).".format(paths.SETTINGS_PATH))
        return 1

    log("Hook Stop:        {} in {}".format(stop, paths.SETTINGS_PATH))
    log("Hook PostToolUse: {} in {}".format(post, paths.SETTINGS_PATH))
    log("")

    # Solo nell'installazione interattiva (il doppio click sull'installer),
    # NON a ogni aggiornamento automatico: quello rilancia "install
    # --no-pause" staccato e senza console (vedi updater._spawn_detached), e
    # rifare il recupero ogni volta significherebbe riscrivere i CSV alle
    # spalle di una sessione di Claude Code magari in corso. Chi volesse
    # rilanciarlo ha il sottocomando "backfill".
    # [EN] Only in the interactive installation (the double click on the
    # installer), NOT on every automatic update: that one relaunches
    # "install --no-pause" detached and without a console (see
    # updater._spawn_detached), and redoing the recovery every time would
    # mean rewriting the CSVs behind the back of a possibly ongoing Claude
    # Code session. Anyone wanting to rerun it has the "backfill"
    # subcommand.
    if interactive:
        _recupera_storico(app_exe, log)
        log("")

    log("Fatto.")
    log("Riavvia Claude Code se era gia' aperto (gli hook si applicano dalla")
    log("prossima sessione). La tua dashboard e' in:")
    log("  {}".format(os.path.join(paths.CLAUDE_DIR, "dashboard-token", "dashboard.html")))

    if interactive:
        log("")
        log("Lo storico delle sessioni gia' aperte prima d'ora e' stato recuperato")
        log("dai transcript di Claude Code. Per rifare il recupero in futuro (e'")
        log("innocuo: rilanciarlo non duplica nulla) il comando e':")
        log("  \"{}\" backfill".format(app_exe))

    log("")
    log("Da qui in avanti l'aggiornamento e' automatico: l'applicazione controlla")
    log("una volta al giorno se ne esiste una versione piu' recente e si aggiorna")
    log("da sola, in background. Non devi piu' scaricare nulla.")

    if interactive:
        log("")
        try:
            input("Premi INVIO per chiudere...")
        except (EOFError, KeyboardInterrupt):
            pass
    return 0
