"""Auto-aggiornamento dalle Release di GitHub.

Idea generale: a fine turno l'hook guarda un file-timbro; se l'ultimo
controllo risale a piu' di 24 ore fa, lancia un processo STACCATO che fa il
lavoro vero e torna subito al proprio compito.

Perche' staccato e' importante: gli hook girano dentro il turno di Claude
Code con timeout 15 secondi. Se il controllo aggiornamenti fosse in linea,
una release lenta da scaricare farebbe scadere l'hook e il turno perderebbe
il log dei token. Il processo figlio invece sopravvive alla fine del turno e
non ha nessun limite di tempo addosso.

La catena completa dell'aggiornamento, con i tre processi coinvolti:

  1. l'hook (dashboard-token log-tokens) vede il timbro scaduto e lancia
     staccato "dashboard-token self-update", poi finisce il suo lavoro;
  2. self-update interroga l'API di GitHub; se c'e' una versione nuova
     scarica l'INSTALLER in %TEMP%, ne verifica il checksum, lo lancia
     staccato con "install --no-pause" e ESCE subito;
  3. l'installer, che gira da %TEMP% e quindi non sta dentro la cartella da
     sostituire, rimpiazza ~/.claude/hooks/dashboard-token/ e riscrive gli
     hook. Se l'applicazione e' ancora in esecuzione (turno in corso), la
     cartella e' bloccata e l'installer riprova finche' non si libera.

Il passaggio 3 e' il motivo per cui l'aggiornamento non lo fa direttamente
l'applicazione installata: nessun processo puo' cancellare la cartella da
cui sta girando.

[EN] Self-update from GitHub Releases.

General idea: at the end of a turn the hook looks at a stamp file; if the
last check is more than 24 hours old, it launches a DETACHED process that
does the real work and goes right back to its own job.

Why detached matters: hooks run inside the Claude Code turn with a
15-second timeout. If the update check were inline, a release slow to
download would time the hook out and the turn would lose the token log.
The child process instead outlives the end of the turn and has no time
limit on it.

The complete update chain, with the three processes involved:

  1. the hook (dashboard-token log-tokens) sees the stamp expired and
     launches "dashboard-token self-update" detached, then finishes its
     own work;
  2. self-update queries the GitHub API; if there is a new version it
     downloads the INSTALLER into %TEMP%, verifies its checksum, launches
     it detached with "install --no-pause" and EXITS immediately;
  3. the installer, which runs from %TEMP% and therefore does not sit
     inside the folder to be replaced, swaps out
     ~/.claude/hooks/dashboard-token/ and rewrites the hooks. If the
     application is still running (turn in progress), the folder is locked
     and the installer retries until it frees up.

Step 3 is the reason the installed application does not do the update
itself: no process can delete the folder it is running from.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import paths
import setup_hooks


def _T():
    """Il traduttore dei messaggi, legato alla lingua scelta per il terminale.

    Come in cli.py, l'import di generate_dashboard sta DENTRO la funzione:
    in cima al file il package non e' ancora nel percorso di ricerca. Il
    try/except copre il caso in cui non ci sia affatto -- l'aggiornatore
    gira anche dentro l'installer, che e' volutamente magro e il package non
    se lo porta dietro. Li' i messaggi restano quelli italiani scritti nel
    dizionario di ripiego qui sotto: meglio un messaggio nella lingua
    sbagliata che un aggiornamento che non parte.

    [EN] The message translator, bound to the language chosen for the
    terminal.

    As in cli.py, the generate_dashboard import lives INSIDE the function:
    at the top of the file the package is not on the search path yet. The
    try/except covers the case where it is not there at all -- the updater
    also runs inside the installer, which is deliberately lean and does not
    carry the package. There the messages stay the Italian ones written in
    the fallback below: better a message in the wrong language than an
    update that does not start.
    """
    try:
        from generate_dashboard import i18n
    except ImportError:
        return lambda key, **valori: key
    return i18n.translator(i18n.cli_lang())
import version

# Ogni quanto controllare (secondi). Una volta al giorno: gli aggiornamenti
# non sono urgenti e cosi' l'API pubblica di GitHub (60 chiamate/ora per
# indirizzo IP senza autenticazione) non viene mai avvicinata, nemmeno con
# piu' installazioni dietro lo stesso indirizzo IP.
# [EN] How often to check (seconds). Once a day: updates are not urgent,
# and this way the public GitHub API limit (60 calls/hour per IP address
# without authentication) is never even approached, not even with many
# installations behind the same IP address.
CHECK_INTERVAL = 24 * 60 * 60

# Timeout di rete generosi ma finiti: girando in un processo staccato non
# danno fastidio a nessuno, ma non vogliamo lasciare processi appesi per
# sempre se la rete inghiotte la connessione senza rispondere.
# [EN] Network timeouts generous but finite: running in a detached process
# they bother nobody, but we do not want to leave processes hanging
# forever if the network swallows the connection without
# answering.
API_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 180

# Prefisso dei file scaricati in %TEMP%, per poterli riconoscere e ripulire.
# [EN] Prefix of the files downloaded into %TEMP%, so they can be
# recognized and cleaned up.
_TEMP_PREFIX = "dashboard-token-installer-"

# L'API di GitHub rifiuta le richieste senza User-Agent.
# [EN] The GitHub API rejects requests without a User-Agent.
_HEADERS = {
    "User-Agent": "dashboard-token-updater/{}".format(version.VERSION),
    "Accept": "application/vnd.github+json",
}


def cleanup_stale():
    """Ripulisce quello che gli aggiornamenti precedenti hanno lasciato in
    giro: le vecchie cartelle di installazione e gli installer scaricati in
    %TEMP%. Va chiamata all'avvio, quando quei file non sono piu' in uso.

    [EN] Cleans up what previous updates left lying around: the old
    installation folders and the installers downloaded into %TEMP%. To be
    called at startup, when those files are no longer in use."""
    setup_hooks.sweep_old_installs()
    try:
        tmp = tempfile.gettempdir()
        for name in os.listdir(tmp):
            if not name.startswith(_TEMP_PREFIX):
                continue
            candidate = os.path.join(tmp, name)
            # Non tocchiamo l'installer della versione che stiamo girando
            # adesso: potrebbe essere ancora in esecuzione.
            # [EN] We do not touch the installer of the version we are
            # running right now: it might still be executing.
            if version.VERSION in name:
                continue
            try:
                os.remove(candidate)
            except OSError:
                pass
    except OSError:
        pass


def _stamp_age():
    """Secondi trascorsi dall'ultimo controllo. Restituisce None se non
    abbiamo mai controllato (file-timbro assente o illeggibile).

    [EN] Seconds elapsed since the last check. Returns None if we have
    never checked (stamp file missing or unreadable)."""
    try:
        with open(paths.UPDATE_STAMP, encoding="utf-8") as f:
            return time.time() - float(f.read().strip())
    except (OSError, ValueError):
        return None


def _touch_stamp():
    """Segna "controllato adesso". Viene scritto PRIMA di tentare
    l'aggiornamento, non dopo: cosi' se il controllo fallisce (rete assente,
    GitHub irraggiungibile) si riprova domani e non a ogni singolo turno.

    [EN] Marks "checked just now". Written BEFORE attempting the update,
    not after: this way, if the check fails (no network, GitHub
    unreachable), we retry tomorrow and not on every single turn."""
    try:
        os.makedirs(paths.HOOKS_DIR, exist_ok=True)
        with open(paths.UPDATE_STAMP, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except OSError:
        pass


def _spawn_detached(argv):
    """Lancia un processo che sopravvive alla morte di questo, senza console
    e senza legami di gruppo.

    [EN] Launches a process that survives the death of this one, without a
    console and without process-group ties."""
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform == "win32":
        # DETACHED_PROCESS: il figlio non eredita (ne' crea) una console,
        # quindi nessuna finestra nera lampeggia sullo schermo.
        # CREATE_NEW_PROCESS_GROUP: non muore se il gruppo del padre riceve
        # un Ctrl-C alla fine del turno.
        # [EN] DETACHED_PROCESS: the child does not inherit (nor create) a
        # console, so no black window flashes on screen.
        # CREATE_NEW_PROCESS_GROUP: it does not die if the parent's group
        # receives a Ctrl-C at the end of the turn.
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        # start_new_session: il figlio esce dal process group del padre,
        # equivalente POSIX dello stesso ragionamento.
        # [EN] start_new_session: the child leaves the parent's process
        # group, the POSIX equivalent of the same reasoning.
        kwargs["start_new_session"] = True
    subprocess.Popen(argv, **kwargs)


def maybe_trigger():
    """Chiamata dagli hook a fine lavoro. Se e' ora di controllare, lancia il
    processo staccato e torna subito. Non solleva mai eccezioni: un problema
    qui non deve mai far fallire il logging dei token.

    [EN] Called by the hooks when their work is done. If it is time to
    check, launches the detached process and returns immediately. Never
    raises: a problem here must never make the token logging fail."""
    try:
        exe = paths.current_exe()
        if exe is None:
            # in sviluppo non c'e' niente da aggiornare
            # [EN] in development there is nothing to update
            return

        # Aggiorniamo solo l'applicazione installata in ~/.claude/hooks/: se
        # il binario viene lanciato da un'altra cartella, l'aggiornamento
        # automatico non interviene.
        # [EN] We only update the application installed in
        # ~/.claude/hooks/: if the binary is launched from another folder,
        # the automatic update does not step in.
        if os.path.normcase(exe) != os.path.normcase(paths.APP_EXE):
            return

        age = _stamp_age()
        if age is not None and age < CHECK_INTERVAL:
            return

        _touch_stamp()
        _spawn_detached([exe, "self-update"])
    except Exception:
        pass


def _fetch(url, timeout):
    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _expected_digest(assets, filename):
    """Legge l'hash atteso dall'asset SHA256SUMS pubblicato dalla CI
    (formato standard di sha256sum: "<hash>  <nomefile>" per riga).
    Restituisce None se il file non c'e' o non contiene questo nome.

    [EN] Reads the expected hash from the SHA256SUMS asset published by
    the CI (standard sha256sum format: "<hash>  <filename>" per line).
    Returns None if the file is missing or does not contain this name."""
    entry = assets.get("SHA256SUMS")
    if entry is None:
        return None
    try:
        text = _fetch(entry["browser_download_url"], API_TIMEOUT).decode("utf-8")
    except Exception:
        return None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and os.path.basename(parts[1]) == filename:
            return parts[0].lower()
    return None


def check_latest(say):
    """Interroga l'API di GitHub e dice se c'e' qualcosa di nuovo.

    Restituisce (tag, entry, assets) se esiste una versione diversa da
    quella in esecuzione, altrimenti None. Separata da apply_update()
    perche' la modalita' interattiva ha bisogno di chiedere conferma
    all'utente fra il "c'e' una versione nuova" e lo scaricamento.

    [EN] Queries the GitHub API and reports whether there is anything new.

    Returns (tag, entry, assets) if a version different from the running
    one exists, otherwise None. Kept separate from apply_update() because
    the interactive mode needs to ask the user for confirmation between
    "there is a new version" and the download.
    """
    asset_name = version.asset_name()
    if asset_name is None:
        say(_T()("upd.noBinary", piattaforma=sys.platform))
        return None

    try:
        release = json.loads(_fetch(version.LATEST_RELEASE_API, API_TIMEOUT).decode("utf-8"))
    except Exception as exc:
        say(_T()("upd.checkFailed", errore=exc))
        return None

    tag = release.get("tag_name")
    if not tag:
        say(_T()("upd.noTag"))
        return None
    if tag == version.VERSION:
        say(_T()("upd.upToDate", versione=version.VERSION))
        return None

    assets = {a.get("name"): a for a in release.get("assets") or []}
    entry = assets.get(asset_name)
    if entry is None:
        say(_T()("upd.missingAsset", tag=tag, file=asset_name))
        return None

    return tag, entry, assets


def apply_update(tag, entry, assets, say):
    """Scarica l'installer, ne verifica l'integrita' e lo lancia staccato.

    Restituisce True se l'installer e' stato avviato. Da quel momento chi
    ha chiamato questa funzione deve USCIRE al piu' presto: finche' resta
    vivo, la cartella da cui gira e' bloccata e l'installer non puo'
    sostituirla.

    [EN] Downloads the installer, verifies its integrity and launches it
    detached.

    Returns True if the installer was started. From that moment on the
    caller of this function must EXIT as soon as possible: as long as it
    stays alive, the folder it runs from is locked and the installer
    cannot replace it.
    """
    asset_name = version.asset_name()
    expected = _expected_digest(assets, asset_name)
    try:
        payload = _fetch(entry["browser_download_url"], DOWNLOAD_TIMEOUT)
    except Exception as exc:
        say(_T()("upd.downloadFailed", errore=exc))
        return False

    # Verifica di integrita': il file scaricato deve corrispondere a quello
    # che la CI ha prodotto. Senza questo controllo un download troncato (o
    # una pagina di errore di un proxy salvata al posto del binario)
    # verrebbe eseguito come installer.
    # [EN] Integrity check: the downloaded file must match what the CI
    # produced. Without this check a truncated download (or a proxy error
    # page saved in place of the binary) would be executed as
    # the installer.
    expected_size = entry.get("size")
    if expected_size and len(payload) != expected_size:
        say(_T()("upd.badSize"))
        return False
    if expected:
        if hashlib.sha256(payload).hexdigest() != expected:
            say(_T()("upd.badChecksum"))
            return False
    else:
        say(_T()("upd.noChecksums"))

    # L'installer va scritto FUORI dalla cartella di installazione, che sta
    # per essere sostituita da lui stesso.
    # [EN] The installer must be written OUTSIDE the installation folder,
    # which is about to be replaced by the installer itself.
    suffix = ".exe" if sys.platform == "win32" else ""
    target = os.path.join(
        tempfile.gettempdir(), "{}{}{}".format(_TEMP_PREFIX, tag, suffix)
    )
    try:
        with open(target, "wb") as f:
            f.write(payload)
        if sys.platform != "win32":
            os.chmod(target, 0o755)
    except OSError as exc:
        say(_T()("upd.writeFailed", errore=exc))
        return False

    try:
        _spawn_detached([target, "install", "--no-pause"])
    except OSError as exc:
        say(_T()("upd.startFailed", errore=exc))
        return False

    return True


def run_update(verbose=False):
    """Il lavoro del passaggio 2 descritto in cima al modulo, eseguito nel
    processo staccato. Non restituisce mai un codice di errore: un
    aggiornamento mancato non e' un guasto, si riprova domani.

    [EN] The work of step 2 described at the top of the module, performed
    in the detached process. Never returns an error code: a missed update
    is not a breakage, we retry tomorrow."""
    def say(message):
        if verbose:
            print(message)

    cleanup_stale()

    if paths.current_exe() is None:
        say(_T()("upd.notPackaged"))
        return 0

    found = check_latest(say)
    if found is None:
        return 0

    tag, entry, assets = found
    say(_T()("upd.newVersion", nuova=tag, attuale=version.VERSION))
    if apply_update(tag, entry, assets, say):
        # Usciamo subito e di proposito, per la ragione spiegata in
        # apply_update().
        # [EN] We exit immediately and on purpose, for the reason explained
        # in apply_update().
        say(_T()("upd.updatingBg", tag=tag))
    return 0
