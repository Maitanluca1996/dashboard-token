"""Caricamento dei template HTML self-contained (CSS/JS inline, __PLACEHOLDER__
sostituiti con .replace() -- niente .format()/f-string sul template intero,
altrimenti le graffe del CSS andrebbero tutte scappate).

NOTA PER CHI NON CONOSCE PYTHON:
Un "template" qui e' semplicemente un file .html gia' completo e pronto,
tranne per alcuni segnaposto tipo __DATA_JSON__ o __GENERATED_AT__ scritti
apposta nel testo. I moduli render_*.py leggono questo testo, e con il
metodo .replace("__SEGNAPOSTO__", valore_vero) sostituiscono ogni segnaposto
con il dato calcolato, per poi salvare il risultato come pagina finale.
Si usa .replace() e non .format()/f-string (le due tecniche piu' comuni in
Python per costruire testo con "buchi" da riempire) perche' quelle
tecniche trattano le parentesi graffe { } come segnaposto speciali -- e un
file CSS ne e' pieno (es. ".classe { color: red; }"), quindi andrebbero
tutte "scappate" a mano scrivendole doppie ({{ }}), un lavoro inutile e
pieno di rischio di errore. .replace() invece cerca e sostituisce solo il
testo esatto __COSI__, senza toccare nient'altro nel file.

[EN] Loading of the self-contained HTML templates (inline CSS/JS,
__PLACEHOLDER__ replaced with .replace() -- no .format()/f-string on
the whole template, otherwise all the CSS braces would need escaping).

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
A "template" here is simply a .html file that is already complete and
ready, except for a few placeholders like __DATA_JSON__ or
__GENERATED_AT__ deliberately written into the text. The render_*.py
modules read this text and, with the .replace("__PLACEHOLDER__",
real_value) method, replace each placeholder with the computed value,
then save the result as the final page.
.replace() is used instead of .format()/f-strings (the two most common
techniques in Python for building text with "holes" to fill) because
those techniques treat curly braces { } as special placeholders -- and
a CSS file is full of them (e.g. ".class { color: red; }"), so they
would all have to be "escaped" by hand by doubling them ({{ }}), a
pointless job full of error risk. .replace() instead searches for and
replaces only the exact text __LIKE_THIS__, without touching anything
else in the file.
"""
import os
import sys

# from . import header: importa header.py (stesso package, vedi la nota nel
# suo docstring) per potergli "girare" le richieste di CSS/HTML
# dell'intestazione condivisa (vedi HEADER_CSS e render_header sotto):
# questo modulo fa da "sportello" verso il caricamento dei template in
# generale, header.py si occupa SOLO dell'intestazione -- responsabilita'
# separate, ma i render_*.py chiamano tutto passando sempre da qui, cosi'
# non devono sapere che l'intestazione vive in un file a parte.
# [EN] from . import header: imports header.py (same package, see the
# note in its docstring) so that requests for the shared header's
# CSS/HTML can be "forwarded" to it (see HEADER_CSS and render_header
# below): this module acts as the "front desk" for template loading in
# general, header.py deals ONLY with the header -- separate
# responsibilities, but the render_*.py call everything always through
# here, so they do not need to know the header lives in a separate
# file.
from . import header

# Dove sta la cartella templates/ dipende da come stiamo girando:
#
#  - Come script .py normali (sviluppo, o installazione "classica" via
#    install.cmd): templates/ e' una sottocartella accanto a questo file,
#    quindi si parte da __file__ (il percorso di questo modulo) e ci si
#    aggiunge "templates".
#
#  - Dentro l'eseguibile unico (dashboard-token.exe, costruito con
#    PyInstaller): non esistono file .py su disco, e' tutto impacchettato
#    dentro il binario. All'avvio PyInstaller scompatta il contenuto in una
#    cartella temporanea e ne mette il percorso in sys._MEIPASS; li' dentro
#    i template finiscono in "generate_dashboard/templates" (come dice la
#    riga "datas" del file .spec). In quel caso __file__ punterebbe a un
#    percorso finto che non esiste su disco, quindi va usato sys._MEIPASS.
#
# sys.frozen e' l'attributo che PyInstaller aggiunge a sys per segnalare
# "stai girando dentro un eseguibile impacchettato"; getattr(sys, "frozen",
# False) lo legge restituendo False se non esiste (invece di dare errore),
# che e' esattamente il caso "script .py normali".
# [EN] Where the templates/ folder lives depends on how we are running:
#
#  - As normal .py scripts (development, or "classic" installation via
#    install.cmd): templates/ is a subfolder next to this file, so we
#    start from __file__ (this module's path) and append "templates".
#
#  - Inside the single executable (dashboard-token.exe, built with
#    PyInstaller): no .py files exist on disk, everything is packed
#    inside the binary. At startup PyInstaller unpacks the content into
#    a temporary folder and puts its path in sys._MEIPASS; in there the
#    templates end up in "generate_dashboard/templates" (as the "datas"
#    line of the .spec file says). In that case __file__ would point to
#    a fake path that does not exist on disk, so sys._MEIPASS must be
#    used.
#
# sys.frozen is the attribute PyInstaller adds to sys to signal "you
# are running inside a packed executable"; getattr(sys, "frozen",
# False) reads it returning False if it does not exist (instead of
# raising an error), which is exactly the "normal .py scripts" case.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _TEMPLATES_DIR = os.path.join(sys._MEIPASS, "generate_dashboard", "templates")
else:
    _TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Alias: rende disponibile il CSS dell'intestazione anche come
# templating.HEADER_CSS (oltre che come header.HEADER_CSS), cosi' i
# render_*.py hanno un unico modulo da importare (templating) invece di
# doverne importare due.
# [EN] Alias: makes the header CSS available also as
# templating.HEADER_CSS (in addition to header.HEADER_CSS), so the
# render_*.py have a single module to import (templating) instead of
# having to import two.
HEADER_CSS = header.HEADER_CSS

# Stessi alias per i due frammenti dell'animazione di rivelazione allo
# scroll definiti in header.py: REVEAL_BOOT va nell'<head> della pagina
# (segnaposto __REVEAL_BOOT__), REVEAL_JS in fondo al <body> (segnaposto
# __REVEAL_JS__). Vedi i commenti estesi in header.py per il perche' di
# quella divisione in due pezzi.
# [EN] Same aliases for the two fragments of the reveal-on-scroll
# animation defined in header.py: REVEAL_BOOT goes into the page's
# <head> (placeholder __REVEAL_BOOT__), REVEAL_JS at the bottom of the
# <body> (placeholder __REVEAL_JS__). See the extended comments in
# header.py for why it is split in two pieces.
REVEAL_BOOT = header.REVEAL_BOOT
REVEAL_JS = header.REVEAL_JS

# Stessa cosa per i due frammenti della traduzione: I18N_BOOT
# nell'<head> (segnaposto __I18N_BOOT__), I18N_APPLY piu' avanti nella
# pagina (segnaposto __I18N_APPLY__). La posizione del secondo non e'
# libera e il perche' e' spiegato per esteso in header.py: in breve,
# deve girare quando il markup da tradurre esiste gia' ma il file dei
# dati non e' ancora stato chiesto.
# [EN] Same for the two translation fragments: I18N_BOOT in the
# <head> (placeholder __I18N_BOOT__), I18N_APPLY further down the page
# (placeholder __I18N_APPLY__). The position of the second one is not
# free and the reason is spelled out in header.py: in short, it must
# run when the markup to translate already exists but the data file
# has not been requested yet.
I18N_BOOT = header.I18N_BOOT
I18N_APPLY = header.I18N_APPLY


def load_template(filename):
    """Legge un file dentro templates/ (es. "dashboard.html") e ne
    restituisce il contenuto come una singola stringa di testo.

    [EN] Reads a file inside templates/ (e.g. "dashboard.html") and
    returns its content as a single text string."""
    with open(os.path.join(_TEMPLATES_DIR, filename), encoding="utf-8") as f:
        return f.read()


def render_header(active_id, refresh_control=False, currency_control=False):
    """Delega la generazione dell'intestazione e navbar al modulo header.

    E' solo un "passamano": chiama header.render_header(...) e ne
    restituisce il risultato cosi' com'e', senza fare altro. Serve per lo
    stesso motivo di HEADER_CSS sopra: chi genera una pagina importa un
    solo modulo (templating), non deve sapere che dietro le quinte
    l'intestazione e' calcolata da header.py. "refresh_control" (bottone
    "Aggiorna" accanto alla data) e "currency_control" (la combo della
    valuta accanto a quella della lingua) viaggiano insieme all'altro
    parametro.

    [EN] Delegates the generation of the header and navbar to the
    header module.

    It is just a "pass-through": it calls header.render_header(...)
    and returns its result as-is, doing nothing else. It exists for the
    same reason as HEADER_CSS above: whoever generates a page imports a
    single module (templating), without needing to know that behind the
    scenes the header is computed by header.py. "refresh_control" (the
    "Aggiorna" button next to the date) and "currency_control" (the
    currency combo next to the language one) travel along with the other
    parameter.
    """
    return header.render_header(active_id, refresh_control, currency_control)
