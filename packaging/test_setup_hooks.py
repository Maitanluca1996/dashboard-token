"""Test del merge di ~/.claude/settings.json.

Si lancia senza dipendenze esterne (niente pytest):

    python packaging/test_setup_hooks.py

E' la parte piu' delicata dell'installazione, perche' modifica un file di
configurazione che appartiene all'utente e che puo' contenere hook di altri
strumenti. Un errore qui non da' un messaggio d'errore: da' un doppio
logging silenzioso, o l'hook di qualcun altro che sparisce. Per questo la
GitHub Action lo esegue prima di costruire qualunque binario.

Nessun test tocca il settings.json vero: si lavora su dizionari in memoria e,
per la sola parte di scrittura, su una cartella temporanea.

[EN] Tests of the ~/.claude/settings.json merge.

Runs with no external dependencies (no pytest):

    python packaging/test_setup_hooks.py

It is the most delicate part of the installation, because it modifies a
configuration file that belongs to the user and may contain hooks of other
tools. A mistake here does not give an error message: it gives silent
double logging, or someone else's hook disappearing. That is why the
GitHub Action runs it before building any binary.

No test touches the real settings.json: everything works on in-memory
dictionaries and, for the writing part only, on a temporary folder.
"""
import glob
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths
import setup_hooks

EXE = "C:/Users/tizio/.claude/hooks/dashboard-token/dashboard-token.exe"

# settings.json d'esempio con l'installazione a script Python gia'
# presente, piu' un hook ESTRANEO che deve sopravvivere intatto.
# [EN] Example settings.json with the Python-script
# installation already present, plus a FOREIGN hook that must survive
# intact.
LEGACY = {
    "hooks": {
        "Stop": [
            {"hooks": [{"type": "command", "command": "python3",
                        "args": ["C:/Users/tizio/.claude/hooks/log_tokens.py"],
                        "timeout": 15}]}
        ],
        "PostToolUse": [
            {"matcher": ".*",
             "hooks": [{"type": "command", "command": "python3",
                        "args": ["C:/Users/tizio/.claude/hooks/log_operation.py"],
                        "timeout": 15}]},
            {"matcher": "^(Edit|Write)$",
             "hooks": [{"type": "command", "command": "python3",
                        "args": ["C:/Users/tizio/.claude/hooks/altro_strumento.py"],
                        "timeout": 10}]},
        ],
    }
}

failures = []


def check(label, condition, detail=""):
    print("{} {}{}".format("OK  " if condition else "FAIL", label,
                           ("  -- " + detail) if detail and not condition else ""))
    if not condition:
        failures.append(label)


def merge(settings, exe=EXE):
    """Applica lo stesso merge che fa install(), senza toccare il disco.

    [EN] Applies the same merge install() does, without touching the disk."""
    root = settings.setdefault("hooks", {})
    stop = setup_hooks._set_exec_hook(root, "Stop", exe, "log-tokens", "log_tokens.py")
    post = setup_hooks._set_exec_hook(root, "PostToolUse", exe, "log-operation",
                                      "log_operation.py", matcher=".*")
    return settings, stop, post


def hooks_of(settings, event):
    out = []
    for group in settings["hooks"].get(event, []):
        out.extend(group.get("hooks", []))
    return out


def copy(obj):
    return json.loads(json.dumps(obj))


print("=== 1. Installazione pulita (settings.json inesistente o vuoto) ===")
s, stop, post = merge({})
check("Stop registrato", stop == "registrato", stop)
check("PostToolUse registrato", post == "registrato", post)
check("un solo hook Stop", len(hooks_of(s, "Stop")) == 1)
check("command punta all'applicazione", hooks_of(s, "Stop")[0]["command"] == EXE)
check("args = ['log-tokens']", hooks_of(s, "Stop")[0]["args"] == ["log-tokens"])
check("matcher .* sul PostToolUse", s["hooks"]["PostToolUse"][0].get("matcher") == ".*")

print("\n=== 2. Migrazione dall'installazione a script Python ===")
s, stop, post = merge(copy(LEGACY))
check("Stop aggiornato, non duplicato", stop == "aggiornato", stop)
check("PostToolUse aggiornato, non duplicato", post == "aggiornato", post)
check("resta un solo hook Stop", len(hooks_of(s, "Stop")) == 1,
      str(len(hooks_of(s, "Stop"))))
check("nessun residuo di python3 nello Stop",
      "python3" not in json.dumps(s["hooks"]["Stop"]))

post_hooks = hooks_of(s, "PostToolUse")
check("PostToolUse ha ancora 2 hook", len(post_hooks) == 2, str(len(post_hooks)))
foreign = [h for h in post_hooks
           if "altro_strumento.py" in json.dumps(h.get("args", []))]
check("hook estraneo preservato", len(foreign) == 1)
check("hook estraneo intatto",
      bool(foreign) and foreign[0]["command"] == "python3" and foreign[0]["timeout"] == 10)
check("matcher ^(Edit|Write)$ preservato",
      any(g.get("matcher") == "^(Edit|Write)$" for g in s["hooks"]["PostToolUse"]))

print("\n=== 3. Reinstallazione: deve essere idempotente ===")
s2, stop2, _ = merge(copy(s))
check("riconosciuto come gia' presente", stop2 == "aggiornato", stop2)
check("resta un solo hook Stop", len(hooks_of(s2, "Stop")) == 1)
check("restano 2 hook PostToolUse", len(hooks_of(s2, "PostToolUse")) == 2)
s3, _, _ = merge(copy(s2))
check("terza passata identica alla seconda",
      json.dumps(s3, sort_keys=True) == json.dumps(s2, sort_keys=True))

print("\n=== 4. Percorso cambiato (altro utente, altra home) ===")
moved, _, _ = merge(copy(s), exe="D:/altro/dashboard-token/dashboard-token.exe")
check("ripuntato al nuovo percorso",
      hooks_of(moved, "Stop")[0]["command"] == "D:/altro/dashboard-token/dashboard-token.exe")
check("senza duplicare", len(hooks_of(moved, "Stop")) == 1)

print("\n=== 5. Hook di altri strumenti sugli stessi eventi ===")
other = {"hooks": {
    "Stop": [{"hooks": [{"type": "command", "command": "notify.exe",
                         "args": ["--beep"], "timeout": 5}]}],
    "SessionStart": [{"hooks": [{"type": "command", "command": "altro.exe"}]}],
}}
s, _, _ = merge(other)
check("hook Stop estraneo preservato",
      any(h["command"] == "notify.exe" for h in hooks_of(s, "Stop")))
check("il nostro si aggiunge accanto", len(hooks_of(s, "Stop")) == 2)
check("evento non nostro intatto",
      s["hooks"]["SessionStart"][0]["hooks"][0]["command"] == "altro.exe")

print("\n=== 6. Lettura e scrittura su file ===")
tmpdir = tempfile.mkdtemp(prefix="dashboard-token-test-")
fake = os.path.join(tmpdir, "settings.json")
real = paths.SETTINGS_PATH
try:
    paths.SETTINGS_PATH = fake
    check("file assente -> dizionario vuoto", setup_hooks._load_settings() == {})
    setup_hooks._save_settings(s)
    check("scritto", os.path.exists(fake))
    check("riletto identico", setup_hooks._load_settings() == s)
    check("nessun .tmp lasciato indietro", not os.path.exists(fake + ".tmp"))
    with open(fake, "w", encoding="utf-8") as f:
        f.write("   \n")
    check("file vuoto -> dizionario vuoto", setup_hooks._load_settings() == {})
    with open(fake, "w", encoding="utf-8") as f:
        f.write("\ufeff{\"hooks\": {}}")
    check("BOM UTF-8 gestito", setup_hooks._load_settings() == {"hooks": {}})
finally:
    paths.SETTINGS_PATH = real
    shutil.rmtree(tmpdir, ignore_errors=True)

print("\n=== 7. Scambio della cartella: anche la seconda rinomina deve ritentare ===")
# Regressione: il retry copriva solo la prima rinomina (vecchia -> .old-*).
# La seconda (.new -> definitiva) abortiva al primo errore, annullando
# l'aggiornamento e lasciando indietro una cartella .new -- il tutto in
# silenzio, perche' l'auto-update gira staccato senza output.
# [EN] Regression: the retry only covered the first rename (old -> .old-*).
# The second (.new -> final) aborted at the first error, cancelling the
# update and leaving a .new folder behind -- all silently, because the
# auto-update runs detached with no output.
tmpdir = tempfile.mkdtemp(prefix="dashboard-token-swap-")
saved = (paths.HOOKS_DIR, paths.INSTALL_DIR, paths.INSTALL_DIR_NEW,
         paths.INSTALL_DIR_OLD_PREFIX, paths.APP_NAME,
         setup_hooks.SWAP_RETRY_DELAY)
real_rename = os.rename
try:
    paths.HOOKS_DIR = tmpdir
    paths.INSTALL_DIR = os.path.join(tmpdir, "dashboard-token")
    paths.INSTALL_DIR_NEW = paths.INSTALL_DIR + ".new"
    paths.INSTALL_DIR_OLD_PREFIX = paths.INSTALL_DIR + ".old-"
    paths.APP_NAME = "dashboard-token"
    # test veloce, la logica e' identica
    # [EN] fast test, the logic is identical
    setup_hooks.SWAP_RETRY_DELAY = 0

    # Un'installazione "esistente" da sostituire, e il payload della nuova.
    # [EN] An "existing" installation to replace, and the new one's payload.
    os.makedirs(paths.INSTALL_DIR)
    with open(os.path.join(paths.INSTALL_DIR, "marcatore.txt"), "w") as f:
        f.write("vecchia")
    payload = os.path.join(tmpdir, "payload")
    os.makedirs(payload)
    with open(os.path.join(payload, "dashboard-token"), "w") as f:
        f.write("nuova")

    # os.rename che fallisce le prime due volte sulla .new, come fa Windows
    # quando un antivirus sta ancora scandendo i file appena copiati.
    # [EN] An os.rename that fails the first two times on the .new folder,
    # as Windows does when an antivirus is still scanning the freshly
    # copied files.
    stubborn = {"rimasti": 2}

    def flaky_rename(src, dst):
        if src == paths.INSTALL_DIR_NEW and stubborn["rimasti"] > 0:
            stubborn["rimasti"] -= 1
            raise OSError(13, "Accesso negato (simulato)")
        return real_rename(src, dst)

    os.rename = flaky_rename
    messages = []
    setup_hooks._install_app(payload, messages.append)

    check("ha davvero ritentato", stubborn["rimasti"] == 0)
    check("ha segnalato i tentativi", any("riprovo" in m for m in messages),
          str(messages))
    check("la nuova versione e' al suo posto",
          os.path.exists(os.path.join(paths.INSTALL_DIR, "dashboard-token")))
    check("la vecchia e' sparita",
          not os.path.exists(os.path.join(paths.INSTALL_DIR, "marcatore.txt")))
    check("nessuna .new lasciata indietro",
          not os.path.exists(paths.INSTALL_DIR_NEW))
    check("nessuna .old-* lasciata indietro",
          not glob.glob(paths.INSTALL_DIR_OLD_PREFIX + "*"))
# un'eccezione qui E' il fallimento
# [EN] an exception here IS the failure
except Exception as exc:  # noqa: BLE001
    check("lo scambio va a buon fine nonostante gli errori", False, repr(exc))
finally:
    os.rename = real_rename
    (paths.HOOKS_DIR, paths.INSTALL_DIR, paths.INSTALL_DIR_NEW,
     paths.INSTALL_DIR_OLD_PREFIX, paths.APP_NAME,
     setup_hooks.SWAP_RETRY_DELAY) = saved
    shutil.rmtree(tmpdir, ignore_errors=True)

print("\n" + "=" * 52)
if failures:
    print("{} TEST FALLITI: {}".format(len(failures), ", ".join(failures)))
    sys.exit(1)
print("Tutti i test passati.")
