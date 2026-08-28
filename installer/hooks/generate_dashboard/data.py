"""Lettura dei log CSV scritti dagli hook (tokens.csv, operations.csv).

NOTA PER CHI NON CONOSCE PYTHON:
Un file CSV e' un file di testo con dati in tabella: una riga per record,
colonne separate da virgole, prima riga = intestazioni (i nomi delle
colonne). Il modulo "csv" della libreria standard di Python sa leggerlo per
noi: "csv.DictReader" legge ogni riga e la trasforma direttamente in un
dizionario {nome_colonna: valore}, usando la prima riga del file come nomi
delle chiavi -- cosi' non serve contare manualmente le colonne per indice.

[EN] Reading of the CSV logs written by the hooks (tokens.csv,
operations.csv).

NOTE FOR READERS NEW TO PYTHON:
A CSV file is a text file holding tabular data: one line per record,
columns separated by commas, first line = headers (the column names).
Python's standard-library "csv" module knows how to read it for us:
"csv.DictReader" reads each line and turns it directly into a
dictionary {column_name: value}, using the file's first line as the
key names -- so there is no need to count columns by index manually.
"""
import csv
import os

# "from . import config" importa il modulo config.py che sta nella STESSA
# cartella (package) di questo file -- il punto "." vuol dire "qui accanto,
# in questo package", a differenza di "import csv" che pesca dalla libreria
# standard di Python installata sul sistema.
# [EN] "from . import config" imports the config.py module that lives
# in the SAME folder (package) as this file -- the dot "." means
# "right here, in this package", unlike "import csv" which pulls from
# the Python standard library installed on the system.
from . import config
from . import pricing


def safe_int(v):
    """Converte v in un numero intero, o restituisce 0 se non e' possibile.

    Serve perche' i dati letti da un CSV sono sempre STRINGHE di testo
    (anche se "sembrano" numeri): "int(v)" prova a interpretarle come
    numero, ma fallisce (solleva un'eccezione) se v e' vuoto, None, o
    contiene testo non numerico -- casi realistici in un log scritto da un
    altro programma. Invece di far crollare tutta la generazione della
    dashboard per un valore mancante, qui si intercetta l'errore e si usa 0
    come valore neutro.

    [EN] Converts v to an integer, or returns 0 if that is not
    possible.

    Needed because data read from a CSV is always text STRINGS (even
    when they "look like" numbers): "int(v)" tries to interpret them
    as a number, but fails (raises an exception) if v is empty, None,
    or contains non-numeric text -- realistic cases in a log written
    by another program. Instead of bringing down the whole dashboard
    generation for a missing value, here the error is caught and 0 is
    used as a neutral value.
    """
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def read_tokens():
    """Un record per turno (hook Stop), da tokens.csv.

    Restituisce una LISTA di dizionari, uno per riga del CSV: ogni
    dizionario ha chiavi comode e gia' con i tipi giusti (numeri come int,
    non come stringhe) invece dei nomi di colonna grezzi del file.

    [EN] One record per turn (Stop hook), from tokens.csv.

    Returns a LIST of dictionaries, one per CSV row: each dictionary
    has convenient keys with the right types already applied (numbers
    as int, not as strings) instead of the file's raw column names.
    """
    # lista vuota: la riempiamo un elemento alla volta con .append()
    # [EN] empty list: we fill it one element at a time with .append()
    rows = []

    # Se il file non esiste ancora (prima sessione mai usata su questo PC),
    # non e' un errore: restituiamo semplicemente una lista vuota.
    # [EN] If the file does not exist yet (no session ever run on this
    # PC), it is not an error: we simply return an empty list.
    if not os.path.exists(config.TOKENS_CSV):
        return rows

    # "with open(...) as f:" apre il file e lo chiude automaticamente alla
    # fine del blocco, anche se dentro succede un errore.
    # encoding="utf-8": i file sono salvati con la codifica di testo
    # standard (supporta lettere accentate, emoji, ecc.).
    # errors="replace": se per qualche motivo un byte nel file non e'
    # valido UTF-8, lo sostituisce con un carattere segnaposto invece di
    # far crashare la lettura dell'intero file.
    # [EN] "with open(...) as f:" opens the file and closes it
    # automatically at the end of the block, even if an error happens
    # inside.
    # encoding="utf-8": the files are saved with the standard text
    # encoding (supports accented letters, emoji, etc.).
    # errors="replace": if for some reason a byte in the file is not
    # valid UTF-8, it is replaced with a placeholder character instead
    # of crashing the read of the whole file.
    with open(config.TOKENS_CSV, newline="", encoding="utf-8", errors="replace") as f:
        # csv.DictReader(f) legge il file riga per riga; il "for r in ...:"
        # scorre ogni riga una alla volta, e ad ogni giro "r" e' un
        # dizionario tipo {"timestamp": "...", "session_id": "...", ...}
        # con le chiavi prese dall'intestazione del CSV.
        # [EN] csv.DictReader(f) reads the file line by line; the
        # "for r in ...:" walks through each row one at a time, and on
        # every pass "r" is a dictionary like {"timestamp": "...",
        # "session_id": "...", ...} with keys taken from the CSV
        # header.
        for r in csv.DictReader(f):
            try:
                rows.append({
                    "timestamp": r["timestamp"],
                    "session_id": r["session_id"],
                    # "r["input_tokens"] or 0": se la cella e' una stringa
                    # vuota (falsy in Python), usa 0 al suo posto prima di
                    # passarlo a int(...) -- altrimenti int("") darebbe
                    # errore.
                    # [EN] "r["input_tokens"] or 0": if the cell is an
                    # empty string (falsy in Python), use 0 in its
                    # place before passing it to int(...) -- otherwise
                    # int("") would raise an error.
                    "input": int(r["input_tokens"] or 0),
                    "output": int(r["output_tokens"] or 0),
                    "cache_write": int(r["cache_write_tokens"] or 0),
                    "cache_read": int(r["cache_read_tokens"] or 0),
                    # Quota di cache write a TTL 1 ora (costa 2x invece di
                    # 1,25x). Con r.get(): sui log scritti prima che questa
                    # colonna esistesse vale 0, e tutto viene trattato come
                    # cache a 5 minuti -- il comportamento di allora.
                    # [EN] Share of cache writes with a 1-hour TTL
                    # (costs 2x instead of 1.25x). With r.get(): on
                    # logs written before this column existed it is 0,
                    # and everything is treated as 5-minute cache --
                    # the behavior of that time.
                    "cache_write_1h": int(r.get("cache_write_1h_tokens") or 0),
                    "total": int(r["total_tokens"] or 0),
                    # r.get("account") invece di r["account"]: get() non da'
                    # errore se la colonna non esiste in una riga (es. un
                    # log vecchio scritto prima che questa colonna fosse
                    # aggiunta), restituisce None -- da qui "or 'sconosciuto'"
                    # come ripiego.
                    # [EN] r.get("account") instead of r["account"]:
                    # get() does not raise if the column is missing
                    # from a row (e.g. an old log written before this
                    # column was added), it returns None -- hence
                    # "or 'sconosciuto'" as a fallback.
                    "account": r.get("account") or "sconosciuto",
                    "summary": r.get("summary") or "",
                    "model": r.get("model") or pricing.DEFAULT_MODEL_KEY,
                })
            except (ValueError, KeyError):
                # Una riga corrotta o con un numero non valido non deve far
                # perdere TUTTO il resto del file: la saltiamo con
                # "continue" (torna all'inizio del for, prossima riga) e
                # proseguiamo con le altre.
                # [EN] A corrupted row or one with an invalid number
                # must not lose EVERYTHING else in the file: we skip
                # it with "continue" (back to the top of the for, next
                # row) and carry on with the others.
                continue
    return rows


def read_ops():
    """Un record per tool call (hook PostToolUse), da operations.csv.

    [EN] One record per tool call (PostToolUse hook), from
    operations.csv."""
    rows = []
    if not os.path.exists(config.OPS_CSV):
        return rows
    # Il campo 'target' e' testo libero (comandi bash, path): puo' contenere
    # sequenze non-UTF8 valide se troncato o scritto con encoding diverso.
    # Non far fallire tutta la dashboard per una riga corrotta.
    # [EN] The 'target' field is free text (bash commands, paths): it
    # can contain invalid non-UTF8 sequences if truncated or written
    # with a different encoding. Do not let one corrupted row take
    # down the whole dashboard.
    with open(config.OPS_CSV, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            # Qui, a differenza di read_tokens(), i dizionari letti dal CSV
            # vengono tenuti COSI' COME SONO (tutte stringhe, chiavi
            # invariate): la conversione a numero viene fatta piu' tardi,
            # solo dove serve, da render_dashboard.py tramite safe_int().
            # [EN] Here, unlike read_tokens(), the dictionaries read
            # from the CSV are kept AS THEY ARE (all strings, keys
            # unchanged): conversion to numbers happens later, only
            # where needed, in render_dashboard.py via safe_int().
            rows.append(r)
    return rows
