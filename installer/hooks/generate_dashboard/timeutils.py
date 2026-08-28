"""Conversione in ora italiana e formattazione delle date mostrate in pagina.

NOTA PER CHI NON CONOSCE PYTHON:
"datetime" e' il modulo standard di Python per lavorare con date e orari.
Un oggetto datetime rappresenta un istante preciso (anno, mese, giorno, ora,
minuto, secondo). "timedelta" rappresenta una DURATA (es. "2 ore", "1
giorno") che si puo' sommare o sottrarre a un datetime per ottenerne un
altro. Tutti gli orari salvati nei file CSV sono in UTC (l'ora "universale",
senza fuso orario, quella che usano i server): questo file serve solo a
convertirli in ora italiana per mostrarli in pagina.

[EN] Conversion to Italian time and formatting of the dates shown on
the page.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
"datetime" is Python's standard module for working with dates and
times. A datetime object represents a precise instant (year, month,
day, hour, minute, second). "timedelta" represents a DURATION (e.g. "2
hours", "1 day") that can be added to or subtracted from a datetime to
obtain another one. All the times saved in the CSV files are in UTC
(the "universal" time, without a time zone, the one servers use): this
file only serves to convert them to Italian time for display on the
page.
"""
from datetime import datetime, timedelta, timezone

# Lista dei mesi abbreviati in italiano. L'indice 0 e' "gen" (gennaio),
# indice 1 e' "feb", ecc. -- per questo in format_generated_at() sotto si
# scrive MONTHS_IT_SHORT[dt.month - 1] e non MONTHS_IT_SHORT[dt.month]: i
# mesi in un oggetto datetime vanno da 1 (gennaio) a 12 (dicembre), mentre
# gli indici di una lista Python partono sempre da 0.
# [EN] List of the abbreviated month names in Italian. Index 0 is "gen"
# (January), index 1 is "feb", etc. -- this is why in
# format_generated_at() below we write MONTHS_IT_SHORT[dt.month - 1]
# and not MONTHS_IT_SHORT[dt.month]: months in a datetime object go
# from 1 (January) to 12 (December), while the indexes of a Python list
# always start at 0.
MONTHS_IT_SHORT = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]


def _last_sunday_utc(year, month):
    """Datetime UTC (01:00) dell'ultima domenica del mese indicato.

    Il nome inizia con "_" (underscore): e' una convenzione Python per dire
    "funzione privata, usata solo dentro questo file, non pensata per
    essere chiamata da altri moduli" (Python non lo impedisce davvero, e'
    solo una segnalazione per chi legge il codice).

    [EN] UTC datetime (01:00) of the last Sunday of the given month.

    The name starts with "_" (underscore): it is a Python convention
    meaning "private function, used only inside this file, not meant to
    be called from other modules" (Python does not actually enforce it,
    it is just a signal for whoever reads the code).
    """
    # Trucco per trovare "l'ultimo giorno del mese" senza dover sapere se il
    # mese ha 28, 29, 30 o 31 giorni: si calcola il PRIMO giorno del mese
    # SUCCESSIVO, e si sottrae un giorno. Se il mese e' dicembre (12), il
    # "mese successivo" e' gennaio dell'anno dopo, da qui l'if/else.
    # [EN] Trick to find "the last day of the month" without having to
    # know whether the month has 28, 29, 30 or 31 days: compute the
    # FIRST day of the FOLLOWING month, and subtract one day. If the
    # month is December (12), the "following month" is January of the
    # next year, hence the if/else.
    first_of_next = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 \
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    last_day = first_of_next - timedelta(days=1)

    # weekday() restituisce il giorno della settimana come numero:
    # lunedi'=0, martedi'=1, ... domenica=6. Vogliamo sapere quanti giorni
    # indietro dobbiamo andare da last_day per arrivare alla domenica.
    # "% 7" (modulo, resto della divisione per 7) gestisce automaticamente
    # anche il caso in cui last_day sia gia' una domenica (differenza 0).
    # [EN] weekday() returns the day of the week as a number: Monday=0,
    # Tuesday=1, ... Sunday=6. We want to know how many days back we
    # must go from last_day to reach the Sunday. "% 7" (modulo, the
    # remainder of division by 7) also automatically handles the case
    # where last_day is already a Sunday (difference 0).
    # weekday(): lun=0 ... dom=6
    # [EN] weekday(): Mon=0 ... Sun=6
    days_since_sunday = (last_day.weekday() - 6) % 7

    # .replace(...) restituisce una COPIA del datetime con solo i campi
    # indicati cambiati (qui: forza l'ora a 01:00:00.000000 esatte) -- non
    # modifica l'originale, i datetime in Python sono "immutabili" (non si
    # possono cambiare dopo la creazione, si crea sempre un nuovo oggetto).
    # [EN] .replace(...) returns a COPY of the datetime with only the
    # given fields changed (here: it forces the time to exactly
    # 01:00:00.000000) -- it does not modify the original, datetimes in
    # Python are "immutable" (they cannot be changed after creation, a
    # new object is always created).
    return (last_day - timedelta(days=days_since_sunday)).replace(hour=1, minute=0, second=0, microsecond=0)


def from_italy_time(dt_local):
    """Inverso di to_italy_time: da ora italiana (CET/CEST) a UTC.

    Serve a backfill.py per leggere i log dell'app Claude, che sono scritti
    nell'ora locale della macchina mentre tutto il resto del progetto
    (tokens.csv, operations.csv) ragiona in UTC.

    L'offset si decide sulla data locale invece che sull'istante UTC: e' una
    semplificazione che sbaglia solo nell'ora esatta del cambio (dove non si
    puo' comunque distinguere, essendo un'ora che si ripete o che non
    esiste) -- irrilevante per attribuire un account a un turno.

    [EN] Inverse of to_italy_time: from Italian time (CET/CEST) to UTC.

    Needed by backfill.py to read the Claude app logs, which are written
    in the machine's local time while everything else in the project
    (tokens.csv, operations.csv) works in UTC.

    The offset is decided on the local date rather than on the UTC
    instant: it is a simplification that is only wrong in the exact hour
    of the switch (where no distinction is possible anyway, it being an
    hour that repeats or does not exist) -- irrelevant for attributing
    an account to a turn.
    """
    dst_start = _last_sunday_utc(dt_local.year, 3)
    dst_end = _last_sunday_utc(dt_local.year, 10)
    naive = dt_local.replace(tzinfo=timezone.utc)
    offset_hours = 2 if dst_start <= naive < dst_end else 1
    return (dt_local - timedelta(hours=offset_hours)).replace(tzinfo=timezone.utc)


def to_italy_time(dt_utc):
    """Converte un datetime UTC in ora italiana (CET/CEST). Stessa regola di
    cambio ora legale in tutta la UE (ultima domenica di marzo/ottobre, 01:00
    UTC) -- calcolata a mano invece di usare zoneinfo perche' su Windows
    zoneinfo.ZoneInfo('Europe/Rome') richiede il pacchetto 'tzdata' via pip
    (non nella stdlib li'), non garantito installato su tutte le
    installazioni Windows (fallisce con ZoneInfoNotFoundError se manca)
    -- va contro la filosofia "zero dipendenze
    extra" di questo progetto (vedi NOTES.md, sezione Distribuzione).

    [EN] Converts a UTC datetime to Italian time (CET/CEST). Same
    daylight-saving rule across the whole EU (last Sunday of
    March/October, 01:00 UTC) -- computed by hand instead of using
    zoneinfo because on Windows zoneinfo.ZoneInfo('Europe/Rome')
    requires the 'tzdata' package via pip (not in the stdlib there),
    not guaranteed to be installed on every Windows setup (it fails
    with ZoneInfoNotFoundError if missing) -- it goes against this
    project's "zero extra
    dependencies" philosophy (see NOTES.md, Distribution section)."""
    # L'Europa passa all'ora legale (CEST, UTC+2) l'ultima domenica di marzo
    # e torna all'ora solare (CET, UTC+1) l'ultima domenica di ottobre.
    # [EN] Europe switches to daylight-saving time (CEST, UTC+2) on the
    # last Sunday of March and back to standard time (CET, UTC+1) on
    # the last Sunday of October.
    # marzo
    # [EN] March
    dst_start = _last_sunday_utc(dt_utc.year, 3)
    # ottobre
    # [EN] October
    dst_end = _last_sunday_utc(dt_utc.year, 10)

    # Espressione condizionale in una riga ("X if condizione else Y"): e'
    # l'equivalente compatto di
    #     if dst_start <= dt_utc < dst_end:
    #         offset_hours = 2
    #     else:
    #         offset_hours = 1
    # "dst_start <= dt_utc < dst_end" e' un confronto "a catena": vero solo
    # se dt_utc cade tra le due date (ora legale attiva).
    # [EN] One-line conditional expression ("X if condition else Y"): it
    # is the compact equivalent of
    #     if dst_start <= dt_utc < dst_end:
    #         offset_hours = 2
    #     else:
    #         offset_hours = 1
    # "dst_start <= dt_utc < dst_end" is a "chained" comparison: true
    # only if dt_utc falls between the two dates (daylight-saving time
    # active).
    offset_hours = 2 if dst_start <= dt_utc < dst_end else 1
    return dt_utc + timedelta(hours=offset_hours)


def format_generated_at(dt):
    """"25 ago 2026, 10:40" invece di "2026-08-25 08:40:53 UTC" -- stesso
    stile sintetico delle date mostrate lato JS (fmtTs), niente secondi
    (rumore per un timestamp di generazione pagina, non un'interazione).
    Nessuna etichetta di fuso: dt e' gia' convertito in ora italiana da
    to_italy_time() prima di arrivare qui, coerente con come le altre ore
    della pagina (fmtTs lato JS) mostrano l'ora locale senza specificarla.

    [EN] "25 ago 2026, 10:40" instead of "2026-08-25 08:40:53 UTC" --
    same concise style as the dates shown on the JS side (fmtTs), no
    seconds (noise for a page-generation timestamp, not an
    interaction). No time-zone label: dt has already been converted to
    Italian time by to_italy_time() before getting here, consistent
    with how the other times on the page (fmtTs on the JS side) show
    local time without stating it."""
    # "{...}".format(...) e' un modo di costruire stringhe sostituendo dei
    # segnaposto {nome} con dei valori. "{h:02d}" vuol dire "numero intero,
    # sempre su 2 cifre, con lo zero davanti se serve" (es. 9 -> "09").
    # [EN] "{...}".format(...) is a way of building strings by replacing
    # {name} placeholders with values. "{h:02d}" means "integer number,
    # always on 2 digits, with a leading zero if needed" (e.g. 9 ->
    # "09").
    return "{d} {m} {y}, {h:02d}:{mi:02d}".format(
        d=dt.day, m=MONTHS_IT_SHORT[dt.month - 1], y=dt.year, h=dt.hour, mi=dt.minute
    )


def generated_at_now():
    """Timestamp di generazione pagina, gia' in ora italiana e formattato.

    Piccola scorciatoia per non dover scrivere, in ogni file che genera una
    pagina, la stessa sequenza di tre chiamate concatenate. "concatenate"
    vuol dire che il risultato di una funzione entra direttamente
    nell'altra: prima datetime.now(timezone.utc) prende l'istante attuale
    in UTC, poi to_italy_time() lo converte, poi format_generated_at() lo
    trasforma nel testo finale da mettere in pagina.

    [EN] Page-generation timestamp, already in Italian time and
    formatted.

    Small shortcut so that every file generating a page does not have
    to write the same sequence of three chained calls. "chained" means
    that the result of one function goes directly into the next: first
    datetime.now(timezone.utc) takes the current instant in UTC, then
    to_italy_time() converts it, then format_generated_at() turns it
    into the final text to put on the page.
    """
    return format_generated_at(to_italy_time(datetime.now(timezone.utc)))
