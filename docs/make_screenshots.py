"""Rifa' gli screenshot del README, da un dataset INVENTATO.

    python docs/make_screenshots.py

Scrive docs/dashboard-it.png e docs/dashboard-en.png. Non tocca ne' i log
veri (~/.claude/logs) ne' la dashboard installata: dataset, pagine generate
e profilo del browser vivono tutti in una cartella temporanea che viene
cancellata alla fine.

PERCHE' UN DATASET INVENTATO E NON UNO SCATTO VERO
Uno scatto di questa dashboard e' quasi interamente numeri sulla spesa di
qualcuno: importi, conteggi di token, titoli di sessione, percentuali. Non
basterebbe coprire i nomi dei progetti. Quindi le immagini del README
nascono da progetti finti, sessioni finte e importi finti, e il README lo
dichiara sotto le immagini.

COSA SERVE
Solo Python 3 e Google Chrome. Nessuna libreria da installare: il dialogo
col browser passa dal suo protocollo di debug (CDP), e il poco di
WebSocket che serve per parlarci sta qui sotto, scritto con la libreria
standard.

[EN] Rebuilds the README screenshots, from an INVENTED dataset.

    python docs/make_screenshots.py

Writes docs/dashboard-it.png and docs/dashboard-en.png. It touches neither
the real logs (~/.claude/logs) nor the installed dashboard: dataset,
generated pages and browser profile all live in a temporary folder that is
deleted at the end.

WHY AN INVENTED DATASET AND NOT A REAL SHOT
A shot of this dashboard is almost entirely numbers about someone's
spending: amounts, token counts, session titles, percentages. Painting
over the project names would not be enough. So the README's pictures come
from made-up projects, made-up sessions and made-up amounts, and the
README says so under them.

WHAT IT NEEDS
Only Python 3 and Google Chrome. No library to install: the conversation
with the browser goes through its debug protocol (CDP), and the little
WebSocket needed to hold it is written below with the standard library.
"""
import base64
import csv
import hashlib
import json
import os
import random
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "installer", "hooks")
DOCS = os.path.join(ROOT, "docs")

# L'inquadratura delle immagini gia' nel README: cambiarla significa
# cambiare anche quelle vecchie, o il README mostrera' due formati diversi.
# [EN] The framing of the pictures already in the README: changing it means
# changing the old ones too, or the README will show two different shapes.
WIDTH, HEIGHT = 1340, 2560

# Porta del protocollo di debug di Chrome. Alta e poco comune apposta: se e'
# gia' occupata da un browser aperto a mano, lo script se ne accorge e si
# ferma invece di fotografare la finestra sbagliata.
# [EN] Chrome's debug protocol port. Deliberately high and uncommon: if it
# is already taken by a hand-opened browser, the script notices and stops
# instead of photographing the wrong window.
PORT = 9333

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_chrome():
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    found = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")
    if found:
        return found
    raise SystemExit("Chrome non trovato. [EN] Chrome not found.")


# --- 1. Il dataset inventato --------------------------------------------------
# [EN] --- 1. The invented dataset ---

PROJECTS = ["acme-webshop", "acme-billing", "notes-cli"]
ACCOUNTS = ["work", "work", "work", "personal"]
# Un modello per sessione, pescato da questa urna: quasi sempre Sonnet, a
# volte Opus, di rado Haiku -- le proporzioni di un uso normale.
# [EN] One model per session, drawn from this urn: nearly always Sonnet,
# sometimes Opus, rarely Haiku -- the proportions of ordinary use.
MODELS = (["claude-sonnet-5"] * 12) + (["claude-opus-5"] * 4) + ["claude-haiku-4-5"]

TITLES = [
    "Warn on a stale lockfile", "Cache the currency rates", "Retry logic for the webhook",
    "Group the settings by scope", "Batch import: memory blowup", "Backfill the missing rows",
    "Speed up the nightly report", "Chart colours are unreadable", "Document the export format",
    "Rename the expiry column", "Split the checkout controller", "Empty cart shows a stale total",
    "Timezone drift in the digest", "Invoice PDF loses its footer", "Search ignores the accents",
    "Refunds land on the wrong day", "Trim the Docker image", "Flaky test in the queue worker",
    "Dark mode misses the tooltips", "Paginate the audit log",
]
PROMPTS = [
    "Handle the empty-state screen", "Split the settings module", "Batch import: memory blowup",
    "Trim the Docker image", "Timezone bug in the daily report", "Rewrite the changelog script",
    "Write tests for the discount rules", "Backfill the missing timestamps",
    "Drop the legacy CSV importer", "Why is the cache never hit?", "Add a retry with backoff",
    "Make the totals row sticky", "Explain this stack trace", "Extract the mailer into a service",
    "Round the amounts to two decimals", "The export skips the last page",
]
TOOLS = ["Read", "Edit", "Bash", "Grep", "Glob", "Write", "TodoWrite", "Task"]

SESSIONS = 112
DAYS_BACK = 143
# Quante delle sessioni finiscono nelle ultime 24 ore. Non e' un dettaglio
# estetico: senza attivita' di oggi la pagina mostra "Costo oggi 0,00 $" e
# il grafico dell'andamento, che parte proprio sulla finestra delle 24 ore,
# non ha niente da disegnare.
# [EN] How many of the sessions land in the last 24 hours. Not a cosmetic
# detail: with no activity today the page shows "Cost today $0.00" and the
# cost-over-time chart, which opens on the 24-hour window, has nothing to
# draw.
SESSIONS_TODAY = 9


def build_dataset(logs_dir):
    """Scrive tokens.csv, operations.csv e la cache dei titoli in logs_dir.

    [EN] Writes tokens.csv, operations.csv and the titles cache into
    logs_dir."""
    # Il seme fisso rende il dataset riproducibile: due esecuzioni danno gli
    # stessi progetti e le stesse cifre, e le due immagini (italiano e
    # inglese) mostrano la stessa dashboard invece di due diverse.
    # [EN] The fixed seed makes the dataset reproducible: two runs give the
    # same projects and the same figures, and the two pictures (Italian and
    # English) show the same dashboard instead of two different ones.
    random.seed(20260905)

    now = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=6)
    start = now - timedelta(days=DAYS_BACK)

    sessions = []
    for i in range(SESSIONS):
        # L'elevamento a potenza addensa le sessioni verso il presente: un
        # progetto vivo ne ha poche di vecchie e molte recenti.
        # [EN] The exponent crowds the sessions towards the present: a live
        # project has few old ones and many recent ones.
        frac = random.random() ** 0.6
        started = start + timedelta(seconds=frac * (now - start).total_seconds())
        if i >= SESSIONS - SESSIONS_TODAY:
            started = now - timedelta(hours=random.uniform(0.4, 23))
        sessions.append({
            "id": "%08x-0000-4000-8000-%012x" % (random.getrandbits(32), random.getrandbits(48)),
            "title": random.choice(TITLES),
            "project": random.choices(PROJECTS, weights=[5, 4, 2])[0],
            "account": random.choice(ACCOUNTS),
            "start": started,
            "turns": max(2, int(random.gauss(13, 7))),
        })
    # Ordinate per inizio, ma con le durate che si accavallano: le
    # interazioni recenti risultano cosi' di sessioni diverse, come in un
    # uso vero, invece che tutte dell'ultima.
    # [EN] Sorted by start, but with overlapping spans: the recent
    # interactions then belong to different sessions, as in real use,
    # instead of all to the last one.
    sessions.sort(key=lambda s: s["start"])

    turns, ops = [], []
    for s in sessions:
        t = s["start"]
        model = random.choice(MODELS)
        cache_read = 0
        for n in range(s["turns"]):
            t += timedelta(minutes=random.randint(2, 14))
            if t > now:
                break
            inp = random.randint(4, 60)
            out = random.randint(700, 4200)
            # Si riscrive la cache all'inizio del discorso e poi quasi piu':
            # da li' in poi la si rilegge soltanto.
            # [EN] The cache is written at the start of the conversation and
            # then hardly again: from there on it is only read back.
            cw = random.randint(2000, 26000) if n < 3 else random.randint(0, 9000)
            # La cache riletta cresce col discorso ma si ferma dove si ferma
            # la finestra di contesto: oltre quella non c'e' piu' niente da
            # rileggere.
            # [EN] The cache read back grows with the conversation but stops
            # where the context window stops: past that there is nothing
            # left to read.
            cache_read = min(cache_read + random.randint(9000, 30000), 178000)
            cr = cache_read + random.randint(-4000, 4000)
            turns.append({
                "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "session_id": s["id"],
                "input_tokens": inp,
                "output_tokens": out,
                "cache_write_tokens": cw,
                "cache_read_tokens": cr,
                "total_tokens": inp + out + cw + cr,
                "account": s["account"],
                "summary": random.choice(PROMPTS),
                "model": model,
                "origine": "hook",
                "cache_write_1h_tokens": cw if random.random() < 0.25 else 0,
            })
            for _ in range(random.randint(0, 4)):
                t += timedelta(seconds=random.randint(20, 200))
                ops.append({
                    "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "session_id": s["id"],
                    "tool": random.choice(TOOLS),
                    "target": "",
                    "input_tokens": random.randint(2, 40),
                    "output_tokens": random.randint(60, 900),
                    "cache_write_tokens": random.randint(0, 5000),
                    "cache_read_tokens": random.randint(8000, 40000),
                    "model": model,
                })

    for name, rows in (("tokens.csv", turns), ("operations.csv", ops)):
        with open(os.path.join(logs_dir, name), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # La cache dei titoli e' l'unico posto da cui la dashboard ricava titolo
    # e progetto di una sessione: riempiendola qui non serve inventare anche
    # dei transcript da cui farli leggere.
    # [EN] The titles cache is the only place the dashboard gets a session's
    # title and project from: filling it here saves inventing transcripts to
    # have them read out of.
    cache = {s["id"]: {"title": s["title"], "project": s["project"], "v": 2} for s in sessions}
    with open(os.path.join(logs_dir, "session_titles_cache.json"), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

    return len(sessions), len(turns), len(ops)


def build_pages(logs_dir, out_dir):
    """Genera le pagine dal dataset finto, con OGNI percorso dirottato.

    [EN] Generates the pages from the fake dataset, with EVERY path
    diverted."""
    sys.path.insert(0, HOOKS)
    from generate_dashboard import config

    config.LOG_DIR = logs_dir
    config.TOKENS_CSV = os.path.join(logs_dir, "tokens.csv")
    config.OPS_CSV = os.path.join(logs_dir, "operations.csv")
    config.CACHE_FILE = os.path.join(logs_dir, "session_titles_cache.json")
    config.OUT_DIR = out_dir
    # Dirottare OUT_DIR non basta: gli altri percorsi sono stati calcolati a
    # partire da lui quando config e' stato importato, e puntano ancora alla
    # cartella vera. Dimenticarne uno non da' errore -- la pagina si apre e
    # resta vuota, perche' le manca un file che e' finito altrove.
    # [EN] Diverting OUT_DIR is not enough: the other paths were computed
    # from it when config was imported, and still point at the real folder.
    # Forgetting one raises nothing -- the page opens and stays blank,
    # because a file it needs went somewhere else.
    for name in ("OUT_HTML", "OUT_PRICING_HTML", "OUT_GUIDE_HTML", "OUT_GUIDE_HTML_EN",
                 "OUT_DATA_JS", "OUT_META_JS", "OUT_I18N_JS"):
        setattr(config, name, os.path.join(out_dir, os.path.basename(getattr(config, name))))

    import generate_dashboard
    generate_dashboard.main()
    return config.OUT_HTML


# --- 2. Il minimo di WebSocket per parlare con Chrome -------------------------
# [EN] --- 2. The minimum WebSocket needed to talk to Chrome ---

class CDP:
    """Una conversazione col protocollo di debug di Chrome.

    Il protocollo viaggia su WebSocket, di cui qui serve pochissimo: aprire
    la connessione con la stretta di mano prevista, mandare un comando in
    JSON, leggere le risposte finche' non arriva quella con l'id giusto. E'
    scritto a mano per non aggiungere una dipendenza a un progetto che non
    ne ha nessuna.

    [EN] A conversation with Chrome's debug protocol.

    The protocol travels over WebSocket, of which very little is needed
    here: open the connection with the prescribed handshake, send a command
    as JSON, read the answers until the one with the right id arrives. It is
    written by hand so as not to add a dependency to a project that has
    none."""

    def __init__(self, ws_url):
        # ws://127.0.0.1:9333/devtools/page/<id> -> host, porta, percorso
        # [EN] ws://127.0.0.1:9333/devtools/page/<id> -> host, port, path
        rest = ws_url.split("://", 1)[1]
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=60)
        self.buf = b""
        self.seq = 0

        # La chiave e' un numero casuale in base64: il server risponde con il
        # suo hash, ed e' cosi' che si distingue una vera accettazione da una
        # risposta HTTP qualsiasi.
        # [EN] The key is a random number in base64: the server replies with
        # its hash, and that is how a real acceptance is told apart from any
        # other HTTP reply.
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            "GET /%s HTTP/1.1\r\n"
            "Host: %s:%s\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n" % (path, host, port, key)
        )
        self.sock.sendall(handshake.encode())

        while b"\r\n\r\n" not in self.buf:
            self.buf += self.sock.recv(4096)
        head, self.buf = self.buf.split(b"\r\n\r\n", 1)
        if b"101" not in head.split(b"\r\n")[0]:
            raise SystemExit("Chrome ha rifiutato la connessione di debug:\n" + head.decode())
        expected = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if expected.lower() not in head.decode().lower():
            raise SystemExit("Stretta di mano WebSocket non valida.")

    def _recv_exactly(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise SystemExit("Chrome ha chiuso la connessione.")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _recv_message(self):
        """Un messaggio intero, anche se arriva spezzato in piu' frammenti.

        [EN] One whole message, even when it arrives split into several
        fragments."""
        payload = b""
        while True:
            b1, b2 = self._recv_exactly(2)
            fin = b1 & 0x80
            length = b2 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._recv_exactly(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._recv_exactly(8))[0]
            # I frame che vengono dal server non sono mascherati: si legge
            # il contenuto cosi' com'e'.
            # [EN] Frames coming from the server are not masked: the content
            # is read as it is.
            payload += self._recv_exactly(length)
            if fin:
                return payload.decode("utf-8")

    def send(self, method, **params):
        """Manda un comando e restituisce il suo risultato.

        [EN] Sends a command and returns its result."""
        self.seq += 1
        data = json.dumps({"id": self.seq, "method": method, "params": params}).encode()

        # I frame che vanno verso il server DEVONO essere mascherati con
        # quattro byte casuali, ripetuti in XOR sul contenuto.
        # [EN] Frames going towards the server MUST be masked with four
        # random bytes, XORed repeatedly over the content.
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        header = bytes([0x81])
        if len(data) < 126:
            header += bytes([0x80 | len(data)])
        elif len(data) < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", len(data))
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", len(data))
        self.sock.sendall(header + mask + masked)

        while True:
            message = json.loads(self._recv_message())
            if message.get("id") == self.seq:
                if "error" in message:
                    raise SystemExit("%s: %s" % (method, message["error"]))
                return message.get("result", {})

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


# --- 3. Lo scatto -------------------------------------------------------------
# [EN] --- 3. The shot ---

def shoot(chrome, url, lang, out_png, profile_dir):
    """Apre la pagina nella lingua chiesta e ne salva l'immagine.

    [EN] Opens the page in the requested language and saves its picture."""
    proc = subprocess.Popen([
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
        "--remote-debugging-port=%d" % PORT, "--remote-allow-origins=*",
        "--user-data-dir=%s" % profile_dir,
        "--window-size=%d,%d" % (WIDTH, HEIGHT),
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws_url = None
        for _ in range(60):
            try:
                targets = json.loads(urllib.request.urlopen(
                    "http://127.0.0.1:%d/json" % PORT, timeout=1).read().decode())
                pages = [t for t in targets if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ws_url:
            raise SystemExit("Chrome non ha aperto la porta %d." % PORT)

        cdp = CDP(ws_url)
        cdp.send("Page.enable")
        cdp.send("Emulation.setDeviceMetricsOverride",
                 width=WIDTH, height=HEIGHT, deviceScaleFactor=1, mobile=False)

        # Due caricamenti e non uno: la lingua viene letta da localStorage
        # all'avvio della pagina, quindi il primo giro serve solo ad avere
        # un'origine su cui scriverla, e il secondo e' quello fotografato.
        # [EN] Two loads and not one: the language is read from localStorage
        # when the page starts, so the first round only serves to have an
        # origin to write it on, and the second is the one photographed.
        cdp.send("Page.navigate", url=url)
        time.sleep(2)
        cdp.send("Runtime.evaluate", expression=(
            "localStorage.setItem('dashboardLang', %s);"
            "localStorage.setItem('dashboardCurrency', 'USD');" % json.dumps(lang)))
        cdp.send("Page.navigate", url=url)

        # L'attesa e' generosa apposta: i grafici si disegnano dopo il
        # caricamento e i riquadri entrano in dissolvenza. Fotografare
        # troppo presto da' una pagina mezza trasparente e senza grafici,
        # che e' un difetto difficile da notare in un'immagine sola.
        # [EN] The wait is deliberately generous: the charts draw after the
        # load and the panels fade in. Shooting too early gives a half
        # transparent, chartless page, a flaw hard to spot in a single
        # picture.
        time.sleep(6)

        shot = cdp.send("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                        clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT, "scale": 1})
        with open(out_png, "wb") as f:
            f.write(base64.b64decode(shot["data"]))
        cdp.close()
    finally:
        proc.terminate()


def main():
    chrome = find_chrome()
    work = tempfile.mkdtemp(prefix="dashboard-token-shots-")
    logs = os.path.join(work, "logs")
    out = os.path.join(work, "out")
    os.makedirs(logs)
    os.makedirs(out)

    try:
        sessions, turns, ops = build_dataset(logs)
        print("dataset inventato: %d sessioni, %d turni, %d operazioni"
              % (sessions, turns, ops))

        html = build_pages(logs, out)
        url = "file:///" + html.replace("\\", "/")

        for lang in ("it", "en"):
            target = os.path.join(DOCS, "dashboard-%s.png" % lang)
            shoot(chrome, url, lang, target, os.path.join(work, "profile-" + lang))
            print("scritto %s (%d byte)" % (target, os.path.getsize(target)))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
