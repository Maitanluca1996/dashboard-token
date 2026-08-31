"""Testi inglesi: interfaccia (UI), formattazione (FMT), terminale (CLI).

Gemello di lang_it.py, con le stesse identiche chiavi. Le convenzioni (solo
dati, niente entita' HTML, dove va ogni dizionario) sono spiegate nel
docstring di lang_it.py; il disegno complessivo in quello di i18n.py.

Quando si aggiunge una chiave, la si aggiunge in ENTRAMBI i file. Se manca
qui, la pagina inglese mostrera' il nome della chiave: e' voluto, perche' si
veda subito.

[EN] English texts: interface (UI), formatting (FMT), terminal (CLI).

Twin of lang_it.py, with exactly the same keys. The conventions (data
only, no HTML entities, where each dictionary goes) are explained in
lang_it.py's docstring; the overall design in i18n.py's.

When adding a key, add it to BOTH files. If it is missing here, the
English page will show the key name: that is deliberate, so it is
noticed immediately.
"""

# ------------------------------------------------------------------
# UI -- tutto cio' che si vede nelle tre pagine.
# [EN] UI -- everything visible on the three pages.
# ------------------------------------------------------------------
UI = {
    "page": {
        "dashboard": "Claude Code — Token usage",
        "pricing": "Price list — Claude Code",
        "guide": "Cost optimisation guide — Claude Code",
    },

    "header": {
        "brandTag": "Token & Cost Monitoring",
        "updatedTitle": "Date and time of the last update",
        "updated": "Updated",
        "refreshTitle": "Reload the data keeping the chosen filters",
        "refresh": "Refresh",
        "nav": "Main navigation",
        "langSwitch": "Page language",
    },

    "dash": {
        "h1": "Token usage — Claude Code",
        "desc": "Detailed monitoring of usage, estimated costs and "
                "interactions per session",
    },

    # Vedi lang_it.py: questi tre paragrafi viaggiano su data-i18n-html,
    # quindi il markup e le entita' HTML qui dentro sono voluti.
    # [EN] See lang_it.py: these three paragraphs travel on data-i18n-html,
    # so the markup and the HTML entities in here are intended.
    "help": {
        "summary": "How many tokens does this monitoring system use?",
        "p1": "The logging (the hooks writing <code>tokens.csv</code> and "
              "<code>operations.csv</code>, plus the regeneration of this "
              "page) never calls the Claude API: it only reads files already "
              "saved locally and writes local files. <strong>Tokens used: "
              "zero.</strong>",
        "p2": "The hooks never return messages that end up in the "
              "conversation context (no <code>systemMessage</code> or "
              "<code>additionalContext</code>), so they do not add a single "
              "token to future turns, neither in this session nor in later "
              "ones.",
        "p3": "The only cost is local and not monetary: at every tool call "
              "and at the end of every turn the scripts re-read the session "
              "transcript to compute the usage deltas. It grows slightly with "
              "the length of the session, but stays in the order of "
              "milliseconds &mdash; an imperceptible wait, not a dent in your "
              "wallet.",
    },

    "side": {
        "filters": "Filters",
        "unit": "Unit",
    },

    "filters": {
        "projects": "Projects:",
        "session": "Session:",
        "account": "Account:",
        "period": "Period:",
        "model": "Model:",
        "search": "Search in the request:",
        "searchPlaceholder": "Request text…",
        "searchClear": "Clear the search",
    },

    "unit": {
        "usd": "Dollars",
        "eur": "Euros",
        "tokens": "Tokens",
    },

    "chart": {
        "groupBy": "Group by:",
        "byDay": "By day",
        "byMonth": "By month",
        "bySession": "By session",
        "byProject": "By project",
        "byModel": "By model",
        "aggregate": "Aggregate",
        "mode": "Mode:",
        "scale": "Scale:",
        "linear": "Linear",
        "log": "Log",
        "period": "Period:",
        "rangeAria": "Width of the time window",
    },

    "turns": {
        "recent": "Recent interactions",
        "colTs": "Date and time",
        "colSession": "Session",
        "colRequest": "Request",
        "colModel": "Model",
        "colTotal": "Total",
        "colCost": "Cost",
        "paginationAria": "Interactions pagination",
        "emptyFiltered": "No interaction matches the chosen filters.",
        "emptyNone": "No interaction recorded yet.",
        "pageInfo": "{from}–{to} of {total}",
        "pageOf": "  ·  page {page} of {total}",
        "prevPage": "Previous page",
        "nextPage": "Next page",
        "actTimestamp": "Timestamp",
        "actTool": "Tool",
        "actTarget": "Target",
        "actCost": "Cost",
        "noActions": "No action recorded for this interaction.",
        "filterOnSession": "Filter on this session",
        "rows": "Rows:",
    },

    # Vedi lang_it.py: i quattro nomi delle voci di consumo non si traducono.
    # [EN] See lang_it.py: the four usage entry names are not translated.
    "stats": {
        "input": "Input",
        "output": "Output",
        "cacheWrite": "Cache write",
        "cacheRead": "Cache read",
        "estCost": "Estimated cost",
        "freshTokens": "Fresh tokens (input+output)",
        "costToday": "Cost today",
        "tokensToday": "Tokens today",
        "turns": "Interactions recorded",
        "sessions": "Sessions",
        "avgFresh": "Average fresh/interaction",
        "totalTokens": "Total tokens (with cache)",
    },

    "unitMode": {
        "barUsd": "Total cost",
        "lineUsd": "Cost over time",
        "ariaUsd": "Estimated cost in dollars",
        "barEur": "Total cost in euros",
        "lineEur": "Cost in euros over time",
        "ariaEur": "Estimated cost in euros",
        "barTokens": "Total tokens",
        "lineTokens": "Tokens over time",
        "ariaTokens": "Total tokens",
    },

    # Vedi lang_it.py: il numero e' un parametro, e le quattro forme
    # separate servono all'accordo italiano. In inglese "Last" non cambia,
    # ma le chiavi restano quattro perche' i due file devono avere le
    # stesse chiavi.
    # [EN] See lang_it.py: the number is a parameter, and the four separate
    # forms serve Italian agreement. In English "Last" does not change, but
    # the keys stay four because the two files must carry the same keys.
    "range": {
        "lastHours": "Last {n} hours",
        "lastDays": "Last {n} days",
        "lastMonths": "Last {n} months",
        "lastYear": "Last year",
        "all": "All history",
        "shortHours": "{n} h",
        "shortDays": "{n} d",
        "shortMonths": "{n} mo",
        "shortYear": "1 y",
        "shortAll": "all",
    },

    "chip": {
        "project": "Project",
        "session": "Session",
        "account": "Account",
        "period": "Period",
        "model": "Model",
        "remove": "Remove this filter",
        "removeAria": "Remove the {kind} filter",
        "clearAll": "Clear all",
    },

    "dd": {
        "allSessions": "All sessions",
        "shortSessions": "Sessions",
        "sessionCount": {"one": "{n} session", "other": "{n} sessions"},
        "allPeriods": "All periods",
        "shortPeriods": "Periods",
        "allModels": "All models",
        "shortModels": "Models",
        "allAccounts": "All accounts",
        "shortAccounts": "Accounts",
        "noProject": "No project",
        "allProjects": "All projects",
        "excludeProject": "Always exclude this project",
        "restoreProject": "Put this project back among the visible ones",
        "excludeAria": "Always exclude {name}",
        "restoreAria": "Put {name} back",
    },

    "common": {
        "turns": {"one": "{n} interaction", "other": "{n} interactions"},
        "sessions": {"one": "{n} session", "other": "{n} sessions"},
        "tokensStr": "{n} tokens",
        "sessionFallback": "Session {id}",
        "noProject": "(no project)",
    },

    "tt": {
        "filterOn": "Filter on {what}",
        "unfilterOn": "Remove the filter on {what}",
        "dismiss": "Click outside or press Esc to close.",
        "showIterations": "Show the iterations",
        "hideIterations": "Hide the iterations",
        "noRequest": "(no request recorded)",
        "sessionId": "Session: ",
        "subAgentCost": "Cost cannot be determined: this action was carried "
                        "out by a delegated sub-agent (Task/Agent). Its token "
                        "usage does not appear in the main session's "
                        "transcript, so it cannot be estimated here -- it is "
                        "not zero, it is unknown.",
        "windowNote": "In the period shown ({period}): {cost} out of {turns}.",
        "span": "from {from} to {to}",
    },

    # Vedi lang_it.py: le due chiavi avgOthers* dicono la stessa cosa in
    # inglese ma non in italiano, e restano due perche' i due file devono
    # avere le stesse chiavi.
    # [EN] See lang_it.py: the two avgOthers* keys say the same thing in
    # English but not in Italian, and stay two because the two files must
    # carry the same keys.
    "bar": {
        "perDay": "per day",
        "perMonth": "per month",
        "perProject": "per project",
        "perSession": "per session",
        "lastDays": "last {n} days",
        "lastMonths": "last {n} months",
        "topProjects": "top {n} projects",
        "topSessions": "top {n} sessions",
        "allHistory": "all history",
        "avgOthersProjects": "Others avg ({n})",
        "avgOthersSessions": "Others avg ({n})",
        "otherProjects": "other projects",
        "otherSessions": "other sessions",
        "legendOtherProjects": "{n} other projects",
        "legendOtherSessions": "{n} other sessions",
        "legendOtherModels": "{n} other models",
        "legendOtherGeneric": "{n} others",
        "avgOf": "Average of {n} {noun}",
        "inTotal": "In total: ",
        "singleBar": "With this filter every grouping would give a single "
                     "bar: the total is in the cards at the top of the page.",
        "noData": "No data yet.",
    },

    "line": {
        "scopeSession": "Total for the whole session",
        "scopeAll": "Grand total",
        "scopeModel": "Total for this model",
        "scopeProject": "Total for the whole project",
        "scopeTail": "Total in the period shown",
        "thisSession": "this session",
        "thisModel": "this model",
        "thisProject": "this project",
        "ariaOverTime": "{what} over time",
        "notEnough": "Not enough interactions for the chart",
    },

    "period": {
        "today": "Today",
        "week": "This week",
        "weekShort": "Week",
        "month": "This month",
        "monthShort": "Month",
        "year": "This year",
        "yearShort": "Year",
    },

    "misc": {
        "stale": "These numbers are the ones read at the time shown: there "
                 "may be new ones by now. Press {refresh} to read them "
                 "again.",
    },

    # Vedi lang_it.py. "hint" viaggia su data-i18n-html: il markup e le
    # entita' qui dentro sono voluti.
    # [EN] See lang_it.py. "hint" travels on data-i18n-html: the markup and
    # the entities in here are intended.
    "pricingPage": {
        "h1": "Price list — Claude Code",
        "desc": "Anthropic list prices as configured in the local price "
                "table, in $ per million tokens (input, output, cache)",
        "colModel": "Model",
        "colIdNote": "ID / notes",
        "hint": "Cache write = 1.25&times; the input price with a 5-minute "
                "TTL, <strong>2&times; with a 1-hour TTL</strong> (the one "
                "Claude Code uses, and therefore almost every cache write) "
                "&middot; cache read = 0.1&times; the input price &mdash; "
                "standard Anthropic multipliers, the same for every model."
                "<br>These are the official pay-as-you-go API prices: if the "
                "account is on a flat-rate Pro/Team plan there is no "
                "per-token billing, but the dashboard uses them anyway as a "
                "reference estimate.",
    },

    # Vedi lang_it.py: sono frasi costruite da numeri, non prosa scritta, e
    # le entita' HTML qui dentro sono giuste perche' Python le incolla
    # nell'HTML al momento della generazione.
    # [EN] See lang_it.py: these are sentences built from numbers, not
    # written prose, and the HTML entities in here are correct because
    # Python pastes them into the HTML at generation time.
    "guide": {
        "verdictBase": "The comparison reference.",
        "verdictCheaper": "Worth it as long as it uses <strong>less than "
                          "{mult}&times;</strong> the tokens of {base}.",
        "verdictPricier": "Worth it if it uses <strong>less than {pct}%</strong> "
                          "of the tokens of {base}.",
        "promoTitle": "The thresholds above will change",
        "promoBody": "The reference model ({label}) has an active price-list "
                     "note: <em>{note}</em>. The break-even thresholds are "
                     "computed on the price <strong>currently</strong> in the "
                     "price list, so they will change automatically once the "
                     "list in <code>generate_dashboard/pricing.py</code> is "
                     "updated. Until it is updated, though, both this page "
                     "and the dashboard's costs stay fixed at the "
                     "promotional price.",
    },

    "footer": {
        "generated": "File generated by ~/.claude/hooks/generate_dashboard/, "
                     "invoked by the Stop hook.",
    },

    "nav": {
        "dashboard": "Dashboard",
        "pricing": "Pricing",
        "guide": "Cost guide",
        "guideHref": "cost-guide.html",
    },
}


# ------------------------------------------------------------------
# FMT -- come si scrivono numeri, valute e date in questa lingua.
# Vedi lang_it.py per il significato di ogni chiave.
# [EN] FMT -- how numbers, currencies and dates are written in this
# language. See lang_it.py for the meaning of each key.
# ------------------------------------------------------------------
FMT = {
    # Punto per i decimali, virgola per le migliaia: 1,234.56.
    # [EN] Dot for decimals, comma for thousands: 1,234.56.
    "dec": ".",
    "thou": ",",

    # Il simbolo di valuta va DAVANTI e attaccato: "$12.50". Per questo
    # il pezzo anteriore e' pieno e quello posteriore vuoto -- lo
    # specchio esatto dell'italiano.
    # [EN] The currency symbol goes IN FRONT and attached: "$12.50".
    # Hence the front piece is filled and the back one empty -- the exact
    # mirror of Italian.
    "moneyPre": "$",
    "moneyPostUsd": "",
    "moneyPostEur": "",

    # "B" per billion. Vedi la nota sul falso amico in lang_it.py.
    # [EN] "B" for billion. See the false-friend note in lang_it.py.
    "billion": "B",

    # Mesi in inglese: maiuscoli, come vuole la lingua.
    # [EN] Months in English: capitalised, as the language requires.
    "monthsShort": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ],
    "monthsLong": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
}


# ------------------------------------------------------------------
# CLI -- i messaggi stampati a terminale. Non arrivano mai al browser.
# [EN] CLI -- the messages printed to the terminal. They never reach the
# browser.
# ------------------------------------------------------------------
CLI = {}
