"""Listino prezzi ufficiale Anthropic, $ per milione di token.

Unica fonte del prezzario: dashboard, pricing.html e guida-costi.html
leggono tutti da qui, cosi' un aggiornamento di listino si applica ovunque
alla rigenerazione successiva senza toccare i template.

NOTA PER CHI NON CONOSCE PYTHON:
MODEL_PRICING e' un "dizionario" (dict): una tabella chiave -> valore, come
un foglio Excel con due colonne. La chiave e' il nome tecnico del modello
(quello che appare nei log, es. "claude-sonnet-5"); il valore e' a sua volta
un altro dizionario piu' piccolo, con l'etichetta leggibile e i due prezzi.
Per leggere un prezzo altrove nel codice si scrive, ad esempio:
    pricing.MODEL_PRICING["claude-sonnet-5"]["input"]   # -> 2.00

[EN] Official Anthropic price list, $ per million tokens.

Single source of truth for the price list: dashboard, pricing.html and
guida-costi.html all read from here, so a price-list update applies
everywhere on the next regeneration without touching the templates.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
MODEL_PRICING is a "dictionary" (dict): a key -> value table, like an
Excel sheet with two columns. The key is the model's technical name
(the one appearing in the logs, e.g. "claude-sonnet-5"); the value is in
turn another, smaller dictionary, with the human-readable label and the
two prices. To read a price elsewhere in the code you write, for
example:
    pricing.MODEL_PRICING["claude-sonnet-5"]["input"]   # -> 2.00
"""

# Listino verificato il 2026-08-27 sulla pagina prezzi ufficiale.
# Moltiplicatori di cache, uguali per ogni modello: cache write 1,25x il
# prezzo input con TTL 5 minuti e 2x con TTL 1 ora, cache read 0,1x.
# Verificato nella stessa occasione, e NON implementato perche' non si
# applica a questi dati: il contesto da 1M non ha sovrapprezzo (una
# richiesta da 900k costa quanto una da 9k), la modalita' fast raddoppia il
# prezzo di Opus 5 ma nei log di Claude Code usage.speed risulta
# "standard", e inference_geo "us" varrebbe 1,1x ma non vi compare.
#
# Ogni riga qui sotto e' nella forma:
#   "chiave-tecnica": {"label": "Nome leggibile", "input": prezzo, "output": prezzo}
# "input" e "output" sono in dollari per MILIONE di token (non per singolo
# token: i prezzi reali sono minuscoli, tipo $0,000002 a token, per questo
# si usa sempre il milione come unita' di misura nel settore).
# [EN] Price list verified on 2026-08-27 on the official pricing page.
# Cache multipliers, identical for every model: cache write 1.25x the
# input price with a 5-minute TTL and 2x with a 1-hour TTL, cache read
# 0.1x. Verified on the same occasion, and NOT implemented because it
# does not apply to this data: the 1M context has no surcharge (a 900k
# request costs the same as a 9k one), fast mode doubles the price of
# Opus 5 but in Claude Code's logs usage.speed comes out "standard",
# and inference_geo "us" would be 1.1x but does not appear there.
#
# Each row below has the form:
#   "technical-key": {"label": "Readable name", "input": price, "output": price}
# "input" and "output" are in dollars per MILLION tokens (not per single
# token: the real prices are tiny, like $0.000002 per token, which is
# why the industry always uses the million as the unit of measure).
MODEL_PRICING = {
    "claude-fable-5": {"label": "Claude Fable 5", "input": 10.00, "output": 50.00},
    "claude-mythos-5": {"label": "Claude Mythos 5", "input": 10.00, "output": 50.00},
    "claude-opus-5": {"label": "Claude Opus 5", "input": 5.00, "output": 25.00},
    "claude-opus-4-8": {"label": "Claude Opus 4.8", "input": 5.00, "output": 25.00},
    "claude-opus-4-7": {"label": "Claude Opus 4.7", "input": 5.00, "output": 25.00},
    "claude-opus-4-6": {"label": "Claude Opus 4.6", "input": 5.00, "output": 25.00},
    # Questa voce ha anche una chiave "note", assente nelle altre: e' una
    # stringa mostrata in pricing.html/guida-costi.html per segnalare che il
    # prezzo e' temporaneo. render_guide.py controlla "note" con m.get("note", "")
    # (get con default: se la chiave non c'e', usa "" invece di dare errore)
    # per capire se mostrare l'avviso, quindi basta togliere questa riga
    # quando la promo finisce e l'avviso sparisce da solo, senza toccare
    # nessun altro file.
    # $2/$10 era annunciato come promo fino al 2026-08-31, ma e' diventato il
    # prezzo standard: l'aumento a $3/$15 previsto per il 2026-09-01 non ci
    # sara' (verificato sulla pagina prezzi ufficiale). Niente "note", quindi
    # nessun avviso di scadenza in pricing.html / guida-costi.html.
    # [EN] This entry also has a "note" key, absent in the others: it is
    # a string shown in pricing.html/guida-costi.html to flag that the
    # price is temporary. render_guide.py checks "note" with
    # m.get("note", "") (get with default: if the key is missing, use ""
    # instead of raising an error) to decide whether to show the notice,
    # so it is enough to remove this line when the promo ends and the
    # notice disappears on its own, without touching any other file.
    # $2/$10 was announced as a promo until 2026-08-31, but it became
    # the standard price: the increase to $3/$15 planned for 2026-09-01
    # will not happen (verified on the official pricing page). No
    # "note", hence no expiry notice in pricing.html / guida-costi.html.
    "claude-sonnet-5": {"label": "Claude Sonnet 5", "input": 2.00, "output": 10.00},
    "claude-sonnet-4-6": {"label": "Claude Sonnet 4.6", "input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"label": "Claude Haiku 4.5", "input": 1.00, "output": 5.00},
}

# Modello usato come riferimento quando un turno nei log non specifica un
# modello (log vecchi, o un caso limite non previsto).
# [EN] Model used as the reference when a turn in the logs does not
# specify a model (old logs, or an unforeseen edge case).
DEFAULT_MODEL_KEY = "claude-sonnet-5"

# Moltiplicatori standard Anthropic applicati al prezzo "input" di ciascun
# modello per ottenere il prezzo di scrittura/lettura della cache di
# contesto (stessi moltiplicatori per tutti i modelli, quindi vivono qui
# come costanti singole invece che ripetuti in ogni riga di MODEL_PRICING).
# [EN] Standard Anthropic multipliers applied to each model's "input"
# price to obtain the context-cache write/read price (same multipliers
# for all models, so they live here as single constants instead of
# being repeated on every MODEL_PRICING row).
# TTL 5 minuti
# [EN] 5-minute TTL
CACHE_WRITE_MULTIPLIER = 1.25
# La cache con TTL di UN'ORA costa il doppio dell'input, non 1,25x. Non e' un
# caso di nicchia: Claude Code usa proprio quella, quindi copre la quasi
# totalita' delle scritture di cache. Applicare 1,25x a tutto sottostima il
# costo del turno -- il moltiplicatore giusto si sceglie in base alla
# ripartizione registrata nel campo "cache_creation" del transcript.
# [EN] The ONE-HOUR TTL cache costs twice the input price, not 1.25x.
# It is not a niche case: Claude Code uses precisely that one, so it
# covers nearly all cache writes. Applying 1.25x to everything
# underestimates the turn's cost -- the right multiplier is
# chosen based on the split recorded in the transcript's
# "cache_creation" field.
CACHE_WRITE_1H_MULTIPLIER = 2.0
CACHE_READ_MULTIPLIER = 0.1


# --- Cambi dal dollaro -------------------------------------------------
# I prezzi Anthropic sono in dollari (sopra), e in dollari arrivano tutti i
# costi calcolati dalla dashboard. Chi legge pero' puo' scegliere in che
# valuta vederli: questa tabella dice quanto vale un dollaro in ciascuna
# delle valute offerte.
#
# Il dollaro sta nella tabella con cambio 1.0 anche se e' l'unita' di
# partenza. Non e' una riga inutile: rende la conversione un'operazione
# sola per tutte le valute -- si moltiplica sempre -- invece di un caso
# speciale ("se e' il dollaro non fare niente") ripetuto in ogni punto che
# formatta un importo.
#
# Le chiavi sono le stesse di i18n.CURRENCIES, e devono restarlo: una
# valuta offerta nella combo ma senza cambio qui verrebbe convertita a 1.0,
# cioe' mostrerebbe importi in dollari con un altro simbolo sopra -- un
# errore silenzioso e credibile, il tipo peggiore. Il selftest della CLI
# controlla che i due elenchi coincidano.
#
# ATTENZIONE: sono costanti scritte a mano, NON cambi aggiornati in tempo
# reale. La generazione della dashboard e' completamente offline (non fa
# nessuna chiamata di rete, vedi il blocco di aiuto in cima alla pagina:
# "token utilizzati: zero"), quindi non c'e' modo di interrogare un
# servizio di cambi -- e non lo vogliamo, perche' renderebbe la generazione
# dipendente da internet ad ogni singolo turno.
# Per aggiornarli: cambia i numeri qui sotto e la data, e alla rigenerazione
# successiva la dashboard usa i nuovi cambi ovunque. La pagina del
# tariffario li mostra insieme alla data, cosi' chi guarda sa quanto sono
# vecchi invece di doverli credere sulla parola.
# [EN] --- Rates from the dollar ---
# Anthropic prices are in dollars (above), and every cost the dashboard
# computes arrives in dollars. The reader, however, can choose which
# currency to see them in: this table says what a dollar is worth in each
# of the offered currencies.
#
# The dollar is in the table with a rate of 1.0 even though it is the
# starting unit. It is not a useless row: it makes conversion a single
# operation for every currency -- always a multiplication -- instead of a
# special case ("if it is the dollar, do nothing") repeated at every point
# that formats an amount.
#
# The keys are the same as i18n.CURRENCIES, and must stay so: a currency
# offered in the combo but with no rate here would be converted at 1.0,
# that is, it would show dollar amounts with another symbol on them -- a
# silent and believable error, the worst kind. The CLI selftest checks that
# the two lists match.
#
# WARNING: these are hand-written constants, NOT rates updated in real
# time. Dashboard generation is fully offline (it makes no network calls,
# see the help block at the top of the page: "tokens used: zero"), so there
# is no way to query an exchange-rate service -- and we do not want one,
# because it would make generation depend on the internet on every single
# turn.
# To update them: change the numbers below and the date, and on the next
# regeneration the dashboard uses the new rates everywhere. The price list
# page shows them together with the date, so whoever looks knows how old
# they are instead of having to take them on trust.
USD_RATES = {
    "usd": 1.0,
    "eur": 0.86,
    "gbp": 0.74,
}

USD_RATES_DATE = "2026-08-26"
