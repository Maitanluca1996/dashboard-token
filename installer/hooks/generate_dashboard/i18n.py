"""Meccanica della traduzione: registro delle lingue, ricerca delle chiavi,
payload per il browser, scelta della lingua per il terminale.

Qui dentro NON c'e' nessun testo da mostrare all'utente: i testi stanno in
lang_it.py e lang_en.py, uno per lingua. Questo modulo sa soltanto come
raggiungerli. E' una divisione voluta -- il file che si legge per capire
"come funziona" resta piccolo, e aggiungere una lingua non lo tocca.

--------------------------------------------------------------------
IL DISEGNO, TUTTO IN UN POSTO
--------------------------------------------------------------------
Chi legge un punto di chiamata (un data-i18n nel markup, una tr() nel
JavaScript, una T() in backfill.py) trova una riga corta e nessuna
spiegazione. La spiegazione e' questa, ed e' l'unica: da li' si torna
sempre qui.

1. PERCHE' UN MODULO PYTHON E NON UN FILE JSON.
   Sembrerebbe piu' naturale mettere le stringhe in strings/it.json. Non
   funzionerebbe, per due ragioni indipendenti che vanno nella stessa
   direzione. installer/sync-from-live.ps1 copia nel repository solo i
   file *.py della radice del package e i templates/*.html: un .json non
   verrebbe rispecchiato, e allargare quella lista e' vietato dalle
   regole del progetto. In parallelo packaging/app.spec imbarca
   nell'eseguibile unico solo la cartella templates/: un .json non
   finirebbe nel binario. Un file .py di radice supera entrambi i
   filtri senza dover cambiare nulla altrove.

2. COME LE STRINGHE ARRIVANO AL BROWSER.
   Le pagine si aprono da file:// (doppio clic, nessun server). Li'
   fetch() e' bloccato e i moduli ES non si caricano: l'unico modo di
   portare dati a una pagina e' uno <script src> classico. Quindi
   js_payload() qui sotto serializza i dizionari in "var I18N = {...}",
   main.py lo scrive in site-i18n.js, e le tre pagine lo caricano nel
   loro <head>. E' esattamente la strada che dashboard-data.js
   percorre gia' oggi per i dati delle sessioni.

   Nel payload finiscono TUTTE le lingue insieme, non solo quella
   scelta: lo switch deve poter cambiare lingua senza andare a
   prendere un secondo file, che da file:// non potrebbe fare.

   I messaggi del terminale (CLI) restano fuori dal payload: al
   browser non servono, e spedirli sarebbe peso morto su ogni pagina.

3. COSA SUCCEDE QUANDO SI CAMBIA LINGUA: LA PAGINA SI RICARICA.
   Non e' una rinuncia, e' la scelta giusta qui. Molte stringhe della
   dashboard sono cotte in costanti calcolate una sola volta all'avvio
   (le tabelle delle unita', dei periodi, delle schede statistiche) e
   poi finite dentro il DOM. Scambiarle a caldo vorrebbe dire
   trasformare ogni costante in funzione e rieseguire ogni disegno
   conservando filtri, ordinamento, pagina e riquadri aperti: tanto
   lavoro e una nuova classe di errori ("questo pannello non si e'
   ridisegnato"). Il ricaricamento invece riusa un meccanismo che la
   dashboard ha gia': salva i filtri, salta l'animazione d'entrata,
   ricarica. La pagina lo fa gia' da sola quando i dati invecchiano.
   Lo switch di lingua si usa una volta per utente: pagare un
   ricaricamento la' e' un affare.

4. PLURALI. Il valore di una chiave puo' essere un dizionario
   {"one": ..., "other": ...} invece di una stringa: chi chiama passa
   il numero e riceve la forma giusta, con {n} sostituito dal numero.
   Italiano e inglese hanno entrambe esattamente due forme, quindi qui
   il meccanismo e' completo, non un'approssimazione. Una lingua con
   piu' categorie (polacco, arabo) richiederebbe una funzione
   plural(n) per lingua che scelga il nome della categoria: e' un
   gancio da due righe, deliberatamente non costruito finche' non
   serve. Non si importa una libreria ICU per due lingue.

   Il genere NON ha un meccanismo. In italiano "Media altri" e "Media
   altre" concordano con un nome sottinteso diverso (altri progetti /
   altre sessioni): sono due frasi diverse, quindi due chiavi diverse.
   Costruire un sistema di genere per due stringhe sarebbe sproporzionato.

5. UNA CHIAVE MANCANTE RESTITUISCE LA CHIAVE STESSA, non una stringa
   vuota e non il testo italiano. Un "chart.avgOthersProjects" che
   compare nell'interfaccia e' una segnalazione di errore che chiunque
   riconosce; un ripiego silenzioso sull'italiano e' un errore che
   viene spedito senza che nessuno se ne accorga.

6. IL FUSO ORARIO NON SEGUE LA LINGUA. Il fuso risponde a "quando e'
   successo, rispetto a dove sono io", non a "in che lingua leggo":
   un italiano a Tokyo vuole le sue ore, non quelle di Roma. Inoltre
   timeutils.py calcola l'ora legale a mano, perche' la regola
   "nessuna dipendenza esterna" vieta tzdata su Windows: legare il
   fuso alla lingua vorrebbe dire scrivere a mano una seconda serie di
   regole per ogni lingua aggiunta. Le date in pagina si formattano
   nel fuso del browser, che le sa tutte e non costa niente.

--------------------------------------------------------------------

[EN] Translation machinery: language registry, key lookup, browser
payload, language choice for the terminal.

There is NO user-facing text in here: the texts live in lang_it.py and
lang_en.py, one per language. This module only knows how to reach
them. The split is deliberate -- the file you read to understand "how
it works" stays small, and adding a language does not touch it.

--------------------------------------------------------------------
THE DESIGN, ALL IN ONE PLACE
--------------------------------------------------------------------
Whoever reads a call site (a data-i18n in the markup, a tr() in the
JavaScript, a T() in backfill.py) finds a short line and no
explanation. This is the explanation, and it is the only one: from
there you always come back here.

1. WHY A PYTHON MODULE AND NOT A JSON FILE.
   Putting the strings in strings/it.json would seem more natural. It
   would not work, for two independent reasons pointing the same way.
   installer/sync-from-live.ps1 copies into the repository only the
   *.py files at the root of the package and templates/*.html: a
   .json would not be mirrored, and widening that list is forbidden by
   the project rules. In parallel packaging/app.spec ships inside the
   single executable only the templates/ folder: a .json would not
   make it into the binary. A root-level .py file clears both filters
   without changing anything elsewhere.

2. HOW THE STRINGS REACH THE BROWSER.
   The pages open from file:// (double click, no server). There
   fetch() is blocked and ES modules do not load: the only way to get
   data into a page is a classic <script src>. So js_payload() below
   serialises the dictionaries into "var I18N = {...}", main.py writes
   it to site-i18n.js, and the three pages load it in their <head>.
   It is exactly the road dashboard-data.js already travels for the
   session data.

   ALL languages go into the payload together, not just the chosen
   one: the switch must be able to change language without fetching a
   second file, which from file:// it could not do.

   The terminal (CLI) messages stay out of the payload: the browser
   does not need them, and shipping them would be dead weight on
   every page.

3. WHAT HAPPENS WHEN THE LANGUAGE CHANGES: THE PAGE RELOADS.
   Not a concession, the right choice here. Many dashboard strings are
   baked into constants computed once at startup (the tables of units,
   of periods, of stat cards) and then sunk into the DOM. Swapping
   them live would mean turning every constant into a function and
   re-running every draw while preserving filters, sorting, page and
   open panels: a lot of work and a new class of bugs ("this panel did
   not repaint"). The reload instead reuses a mechanism the dashboard
   already has: save the filters, skip the entrance animation, reload.
   The page already does it by itself when the data goes stale. The
   language switch is used once per user: paying a reload there is a
   bargain.

4. PLURALS. A key's value may be a dictionary {"one": ..., "other":
   ...} instead of a string: the caller passes the number and gets the
   right form back, with {n} replaced by the number. Italian and
   English both have exactly two forms, so the mechanism here is
   complete, not an approximation. A language with more categories
   (Polish, Arabic) would need a per-language plural(n) function
   picking the category name: a two-line hook, deliberately not built
   until needed. One does not import an ICU library for two languages.

   Gender has NO mechanism. In Italian "Media altri" and "Media altre"
   agree with a different elided noun (other projects / other
   sessions): they are two different sentences, hence two different
   keys. Building a gender system for two strings would be out of
   proportion.

5. A MISSING KEY RETURNS THE KEY ITSELF, not an empty string and not
   the Italian text. A "chart.avgOthersProjects" showing up in the
   interface is a bug report anyone recognises; a silent fallback to
   Italian is a bug that ships unnoticed.

6. THE TIME ZONE DOES NOT FOLLOW THE LANGUAGE. The zone answers "when
   did it happen, relative to where I am", not "what language do I
   read in": an Italian in Tokyo wants their own hours, not Rome's.
   Besides, timeutils.py computes daylight saving by hand, because the
   "no external dependencies" rule forbids tzdata on Windows: tying
   the zone to the language would mean hand-writing a second set of
   rules for every language added. Dates on the page are formatted in
   the browser's zone, which knows them all and costs nothing.
"""
import json
import locale
import os

from . import config
from . import lang_en
from . import lang_it

# ------------------------------------------------------------------
# Il registro. E' l'unico punto da toccare per aggiungere una lingua:
# si scrive lang_xx.py con le stesse chiavi, e lo si nomina qui.
# L'ordine di LANGS e' l'ordine in cui i bottoni compaiono nello switch.
# [EN] The registry. It is the only place to touch in order to add a
# language: write lang_xx.py with the same keys, and name it here. The
# order of LANGS is the order in which the buttons appear in the switch.
# ------------------------------------------------------------------
_MODULES = {
    "it": lang_it,
    "en": lang_en,
}

LANGS = ["it", "en"]

# Ripiego finale, quando nessun indizio dice altro. Inglese e non
# italiano perche' il progetto e' pubblico: chi non ha ne' una
# preferenza salvata ne' un sistema che dichiari una lingua e' con ogni
# probabilita' qualcuno che l'italiano non lo legge.
# [EN] Final fallback, when no clue says otherwise. English rather than
# Italian because the project is public: someone with neither a saved
# preference nor a system declaring a language is in all likelihood
# someone who does not read Italian.
DEFAULT = "en"

# Il nome di ogni lingua NELLA lingua stessa (endonimo). Non si traduce
# mai: nello switch un francese deve poter riconoscere "Francais" anche
# mentre la pagina e' in italiano -- se fosse tradotto leggerebbe
# "Francese", che a chi cerca la propria lingua non serve a niente.
# [EN] The name of each language IN that language (endonym). It is
# never translated: in the switch a French speaker must be able to
# recognise "Francais" even while the page is in Italian -- translated
# it would read "Francese", which is no help to someone looking for
# their own language.
ENDONYMS = {
    "it": "Italiano",
    "en": "English",
}

# La bandiera che accompagna ogni lingua nella combo. E' un'associazione
# imprecisa per natura -- una bandiera indica un paese, e una lingua non
# appartiene a un paese solo -- quindi non viaggia mai da sola: nella combo
# sta sempre accanto all'endonimo, che e' il dato che identifica davvero la
# lingua. La bandiera aiuta a trovarla con la coda dell'occhio, il nome dice
# quale sia.
#
# SVG e non emoji, e non per gusto: Windows non disegna le bandiere emoji,
# le mostra come la coppia di lettere che le compone dentro due riquadri
# (verificato misurando la larghezza resa). Su Windows una combo "con le
# bandiere" fatta di emoji non mostrerebbe nessuna bandiera.
#
# Il markup viene incollato nell'HTML da render_header al momento della
# generazione, quindi qui le entita' e i tag ci stanno: e' l'unico posto del
# registro in cui questo vale.
# [EN] The flag accompanying each language in the combo. It is an imprecise
# association by nature -- a flag denotes a country, and a language does not
# belong to a single country -- so it never travels alone: in the combo it
# always sits next to the endonym, which is the datum that really identifies
# the language. The flag helps to spot it out of the corner of the eye, the
# name says which one it is.
#
# SVG and not emoji, and not out of taste: Windows does not draw flag emoji,
# it shows them as the pair of letters composing them inside two boxes
# (verified by measuring the rendered width). On Windows a combo "with
# flags" made of emoji would show no flag at all.
#
# The markup is pasted into the HTML by render_header at generation time, so
# tags and entities belong here: it is the only place in the registry where
# that holds.
FLAGS = {
    "it": (
        '<svg class="lang-flag" viewBox="0 0 24 16" width="19" height="13" aria-hidden="true" focusable="false">'
        '<rect width="8" height="16" fill="#008C45"/>'
        '<rect x="8" width="8" height="16" fill="#F4F5F0"/>'
        '<rect x="16" width="8" height="16" fill="#CD212A"/>'
        '</svg>'
    ),
    "en": (
        '<svg class="lang-flag" viewBox="0 0 24 16" width="19" height="13" aria-hidden="true" focusable="false">'
        '<rect width="24" height="16" fill="#012169"/>'
        '<path d="M0,0 L24,16 M24,0 L0,16" stroke="#FFF" stroke-width="3.4"/>'
        '<path d="M0,0 L24,16 M24,0 L0,16" stroke="#C8102E" stroke-width="1.7"/>'
        '<path d="M12,0 V16 M0,8 H24" stroke="#FFF" stroke-width="5.4"/>'
        '<path d="M12,0 V16 M0,8 H24" stroke="#C8102E" stroke-width="3.2"/>'
        '</svg>'
    ),
}


def is_supported(code):
    """Dice se un codice di lingua e' fra quelli che sappiamo mostrare.

    [EN] Tells whether a language code is among those we can display.
    """
    return code in _MODULES


def normalize(tag):
    """Riduce un'etichetta di lingua ("it-IT", "en_US.UTF-8") al codice
    di due lettere che usiamo noi, oppure None se non la riconosciamo.

    Le etichette di lingua arrivano in forme molto diverse a seconda di
    chi le scrive: il browser dice "it-IT", il sistema operativo dice
    "it_IT" o "Italian_Italy.1252", una variabile d'ambiente puo' dire
    "en_US.UTF-8". Tutte queste cominciano con le due lettere che ci
    interessano, quindi si taglia tutto quello che viene dopo il primo
    separatore e si guarda se il resto e' una lingua che conosciamo.

    [EN] Reduces a language tag ("it-IT", "en_US.UTF-8") to the
    two-letter code we use, or None if we do not recognise it.

    Language tags arrive in very different shapes depending on who
    writes them: the browser says "it-IT", the operating system says
    "it_IT" or "Italian_Italy.1252", an environment variable may say
    "en_US.UTF-8". All of these start with the two letters we care
    about, so we cut everything after the first separator and check
    whether what is left is a language we know.
    """
    if not tag:
        return None
    # lower() perche' "IT" e "it" sono la stessa lingua; strip() perche'
    # una variabile d'ambiente puo' portarsi dietro spazi.
    # [EN] lower() because "IT" and "it" are the same language; strip()
    # because an environment variable may carry spaces along.
    code = str(tag).strip().lower()
    # Si taglia al primo separatore fra i tre possibili: "it-IT" -> "it",
    # "en_US.UTF-8" -> "en".
    # [EN] Cut at the first of the three possible separators: "it-IT" ->
    # "it", "en_US.UTF-8" -> "en".
    for sep in ("-", "_", "."):
        if sep in code:
            code = code.split(sep, 1)[0]
    if code in _MODULES:
        return code

    # Windows non dice "it_IT": dice "Italian_Italy.1252", cioe' il nome
    # della lingua per esteso e in inglese. Tagliato al primo separatore
    # resta "italian", che non e' un codice ISO e che quindi il controllo
    # qui sopra non riconosce -- ed e' il motivo per cui un PC italiano si
    # ritroverebbe i messaggi in inglese senza accorgersi del perche'.
    # locale.normalize() conosce quei nomi e li riporta alla forma "it_IT",
    # da cui si riprendono le due lettere. E' libreria standard, quindi non
    # rompe la regola "nessuna dipendenza esterna".
    # [EN] Windows does not say "it_IT": it says "Italian_Italy.1252", that
    # is the language name spelled out, in English. Cut at the first
    # separator it leaves "italian", which is not an ISO code and which the
    # check above therefore does not recognise -- and that is why an Italian
    # PC would end up with English messages without anyone seeing why.
    # locale.normalize() knows those names and brings them back to the
    # "it_IT" form, from which the two letters can be taken again. It is
    # standard library, so it does not break the "no external dependencies"
    # rule.
    try:
        esteso = locale.normalize(code)
    except (AttributeError, ValueError):
        return None
    if esteso and esteso != code:
        code = esteso.lower().split("_", 1)[0].split(".", 1)[0]
        if code in _MODULES:
            return code
    return None


def _bundle(lang, section):
    """Restituisce un dizionario di una lingua ("UI", "FMT" o "CLI").

    Se la lingua non esiste si ripiega su DEFAULT invece di sollevare
    un'eccezione: una lingua sconosciuta deve degradare in una pagina
    leggibile, non in una pagina rotta.

    [EN] Returns one of a language's dictionaries ("UI", "FMT" or "CLI").

    If the language does not exist we fall back to DEFAULT instead of
    raising: an unknown language must degrade into a readable page, not
    a broken one.
    """
    module = _MODULES.get(lang) or _MODULES[DEFAULT]
    return getattr(module, section)


def lookup(lang, key, section="UI"):
    """Cerca una chiave puntata ("header.updated") dentro i dizionari.

    Le chiavi sono puntate perche' i dizionari sono annidati per sezione
    ("header", "filters", "chart"...): raggrupparle evita un unico
    elenco piatto di centinaia di voci in cui non si trova piu' niente.
    Qui il punto viene usato per scendere un livello alla volta.

    Restituisce None se la chiave non c'e'. Chi chiama decide cosa
    farne -- vedi translator() e il punto 5 del docstring in cima.

    [EN] Looks up a dotted key ("header.updated") inside the dictionaries.

    Keys are dotted because the dictionaries are nested by section
    ("header", "filters", "chart"...): grouping them avoids a single
    flat list of hundreds of entries in which nothing can be found any
    more. Here the dot is used to descend one level at a time.

    Returns None if the key is absent. The caller decides what to do
    with that -- see translator() and point 5 of the docstring above.
    """
    node = _bundle(lang, section)
    for part in key.split("."):
        # isinstance(node, dict) protegge dal caso "la chiave e' troppo
        # lunga": se a meta' strada si trova una stringa invece di un
        # dizionario, non si puo' scendere oltre e la chiave e' sbagliata.
        # [EN] isinstance(node, dict) guards the "key is too long" case:
        # if halfway down we find a string instead of a dictionary, we
        # cannot descend further and the key is wrong.
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


class _Missing(dict):
    """Dizionario che, invece di sollevare KeyError su una chiave
    assente, restituisce il segnaposto cosi' com'era scritto.

    Serve a format_map in translator(): una traduzione che cita {conto}
    mentre chi chiama ha passato solo {totale} deve produrre una riga
    imperfetta ma leggibile, con un "{conto}" bene in vista, non far
    fallire il comando.

    [EN] Dictionary that, instead of raising KeyError on a missing key,
    returns the placeholder exactly as it was written.

    It serves format_map in translator(): a translation quoting {conto}
    while the caller only passed {totale} must produce an imperfect but
    readable line, with a "{conto}" in plain sight, rather than make
    the command fail.
    """

    def __missing__(self, key):
        return "{" + key + "}"


def translator(lang, section="CLI"):
    """Restituisce una funzione T(chiave, **valori) legata a una lingua.

    Si usa cosi', tipicamente una volta sola in cima a una funzione:

        T = i18n.translator(i18n.cli_lang())
        say(T("backfill.start"))
        say(T("backfill.done", sessioni=12))

    Legare la lingua una volta e poi chiamare T() dappertutto tiene
    corti i punti di chiamata: senza, ogni riga dovrebbe ripetere la
    lingua, e sarebbe rumore su rumore.

    I valori da inserire nel testo si passano come argomenti con nome e
    finiscono nei segnaposto {cosi'} dentro la stringa tradotta. Il
    segnaposto sta nel DIZIONARIO e non nel codice perche' l'ordine
    delle parole cambia da lingua a lingua: "12 sessioni recuperate" e
    "recovered 12 sessions" mettono il numero in posti diversi, e solo
    chi scrive la traduzione sa dove va.

    Per i plurali si passa n=... e il valore nel dizionario e' un
    dizionario {"one": ..., "other": ...} (vedi il punto 4 in cima).

    [EN] Returns a function T(key, **values) bound to one language.

    Used like this, typically once at the top of a function:

        T = i18n.translator(i18n.cli_lang())
        say(T("backfill.start"))
        say(T("backfill.done", sessioni=12))

    Binding the language once and then calling T() everywhere keeps the
    call sites short: without it every line would have to repeat the
    language, which would be noise upon noise.

    The values to insert into the text are passed as named arguments
    and land in the {like_this} placeholders inside the translated
    string. The placeholder lives in the DICTIONARY and not in the code
    because word order changes between languages: "12 sessioni
    recuperate" and "recovered 12 sessions" put the number in different
    places, and only whoever writes the translation knows where.

    For plurals pass n=... and let the dictionary value be a dictionary
    {"one": ..., "other": ...} (see point 4 above).
    """
    def T(key, **values):
        value = lookup(lang, key, section)
        # Chiave assente: si restituisce la chiave stessa, ben visibile.
        # [EN] Missing key: return the key itself, plainly visible.
        if value is None:
            return key
        # Valore a due forme: si sceglie con n. Se n non e' stato
        # passato non si puo' scegliere, e restituire la chiave segnala
        # l'errore invece di indovinare una forma a caso.
        # [EN] Two-form value: choose with n. If n was not passed we
        # cannot choose, and returning the key signals the mistake
        # instead of guessing a form at random.
        if isinstance(value, dict):
            if "n" not in values:
                return key
            value = value["one"] if values["n"] == 1 else value["other"]
        # format_map invece di format(**values): con format_map una
        # chiave che il testo non usa non e' un errore, e il dizionario
        # custom qui sotto restituisce il segnaposto intatto quando manca
        # il valore, cosi' si vede cosa manca invece di perdere la riga
        # in un'eccezione.
        # [EN] format_map instead of format(**values): with format_map a
        # key the text does not use is not an error, and the custom
        # dictionary below returns the placeholder untouched when a value
        # is missing, so you see what is missing instead of losing the
        # line to an exception.
        return str(value).format_map(_Missing(values))

    return T


def js_payload():
    """Costruisce il testo di site-i18n.js: "var I18N = {...};".

    Dentro ci vanno UI e FMT di TUTTE le lingue (il perche' e' al punto
    2 del docstring in cima), mai CLI.

    [EN] Builds the text of site-i18n.js: "var I18N = {...};".

    UI and FMT of ALL languages go in (why is at point 2 of the
    docstring above), never CLI.
    """
    payload = {
        "langs": LANGS,
        # Il ripiego viaggia col payload invece di essere cablato nel
        # JavaScript: e' una decisione, e le decisioni stanno in un posto
        # solo. Scritta due volte, prima o poi le due copie divergono.
        # [EN] The fallback travels with the payload instead of being
        # hardcoded in the JavaScript: it is a decision, and decisions live
        # in one place only. Written twice, sooner or later the two copies
        # diverge.
        "fallback": DEFAULT,
        "endonyms": ENDONYMS,
        "flags": FLAGS,
        "strings": {code: _bundle(code, "UI") for code in LANGS},
        "fmt": {code: _bundle(code, "FMT") for code in LANGS},
    }
    # ensure_ascii=False tiene accenti e simboli come caratteri veri
    # invece di sequenze \uXXXX: il file resta leggibile se qualcuno lo
    # apre, e pesa meno.
    # [EN] ensure_ascii=False keeps accents and symbols as real
    # characters instead of \uXXXX sequences: the file stays readable if
    # someone opens it, and weighs less.
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    # La sequenza "</" dentro una stringa JS chiuderebbe anticipatamente
    # il tag <script> che la contiene, se una traduzione contenesse per
    # esempio "</div>". Spezzarla con una barra rovescia e' invisibile a
    # JavaScript e innocuo per il parser HTML. Stessa protezione che usa
    # render_dashboard.py sul payload dei dati.
    # [EN] The sequence "</" inside a JS string would close the
    # containing <script> tag early, if a translation contained e.g.
    # "</div>". Breaking it with a backslash is invisible to JavaScript
    # and harmless to the HTML parser. Same guard render_dashboard.py
    # uses on the data payload.
    return "var I18N = " + text.replace("</", "<\\/") + ";\n"


def cli_lang():
    """Sceglie la lingua dei messaggi a terminale.

    Nel browser la lingua si sceglie leggendo navigator.language e la si
    puo' cambiare con lo switch. A terminale non c'e' ne' l'uno ne'
    l'altro, quindi si guardano quattro indizi in ordine, dal piu'
    esplicito al piu' generico:

      1. la variabile d'ambiente DASHBOARD_TOKEN_LANG, che e' il modo di
         dirlo una volta per un singolo comando ("DASHBOARD_TOKEN_LANG=en
         dashboard-token backfill") e l'unico che si presta agli script;
      2. la chiave "lang" in dashboard_config.json, che e' il modo di
         dirlo una volta per sempre su questa macchina;
      3. la lingua del sistema operativo, che e' l'indizio buono per chi
         non ha configurato niente;
      4. DEFAULT.

    La lingua scelta qui e quella scelta dal browser si calcolano in
    modo indipendente e possono NON coincidere. E' corretto: sono due
    superfici diverse con segnali diversi, e chi ha il browser in
    italiano su un sistema in inglese ha buone ragioni per entrambi.

    [EN] Chooses the language of the terminal messages.

    In the browser the language is chosen by reading navigator.language
    and can be changed with the switch. In a terminal there is neither,
    so we look at four clues in order, from the most explicit to the
    most generic:

      1. the DASHBOARD_TOKEN_LANG environment variable, which is the way
         to say it once for a single command ("DASHBOARD_TOKEN_LANG=en
         dashboard-token backfill") and the only one that suits scripts;
      2. the "lang" key in dashboard_config.json, which is the way to
         say it once and for all on this machine;
      3. the operating system language, the good clue for anyone who has
         configured nothing;
      4. DEFAULT.

    The language chosen here and the one chosen by the browser are
    computed independently and may NOT agree. That is correct: they are
    two different surfaces with different signals, and someone with an
    Italian browser on an English system has good reasons for both.
    """
    # 1. Variabile d'ambiente.
    # [EN] 1. Environment variable.
    code = normalize(os.environ.get("DASHBOARD_TOKEN_LANG"))
    if code:
        return code

    # 2. dashboard_config.json, gia' letto da config.py all'import.
    # [EN] 2. dashboard_config.json, already read by config.py at import.
    code = normalize(config.LANG)
    if code:
        return code

    # 3. Lingua del sistema. Tutto in try/except perche' le funzioni di
    #    locale possono sollevare eccezioni su configurazioni insolite, e
    #    non sapere la lingua del sistema non e' un motivo per fermare un
    #    comando: si scende semplicemente al ripiego.
    #    getlocale() e non getdefaultlocale(), che e' deprecata.
    # [EN] 3. System language. All in try/except because the locale
    # functions can raise on unusual configurations, and not knowing the
    # system language is no reason to stop a command: we simply fall
    # through to the fallback. getlocale() and not getdefaultlocale(),
    # which is deprecated.
    try:
        code = normalize(locale.getlocale()[0])
        if code:
            return code
    except (ValueError, TypeError):
        pass

    # Ultimo indizio prima del ripiego: le variabili d'ambiente che usano
    # i sistemi Unix. Su Windows non ci sono e il giro e' a vuoto.
    # [EN] Last clue before the fallback: the environment variables Unix
    # systems use. On Windows they are absent and the loop is a no-op.
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        code = normalize(os.environ.get(name))
        if code:
            return code

    # 4. Ripiego.
    # [EN] 4. Fallback.
    return DEFAULT
