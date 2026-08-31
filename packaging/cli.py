"""Punto di ingresso unico dell'eseguibile dashboard-token.

Un solo binario fa tutto, distinguendo il compito dal primo argomento:

    dashboard-token                 installa (e' cosa succede col doppio click)
    dashboard-token install         idem, da riga di comando
    dashboard-token log-tokens      hook Stop -- lo chiama Claude Code
    dashboard-token log-operation   hook PostToolUse -- lo chiama Claude Code
    dashboard-token backfill        recupera lo storico dalle sessioni gia' aperte
    dashboard-token config          le tre personalizzazioni facoltative
    dashboard-token self-update     controlla e installa una versione nuova
    dashboard-token version         stampa la versione e i percorsi

I due comandi "log-*" sono quelli registrati in settings.json e girano
dentro il turno di Claude Code: devono essere veloci e non devono MAI
buttare fuori un'eccezione non gestita, altrimenti il turno segnala un hook
fallito all'utente.

[EN] Single entry point of the dashboard-token executable.

One binary does everything, telling the tasks apart by the first argument:

    dashboard-token                 installs (what a double click does)
    dashboard-token install         same, from the command line
    dashboard-token log-tokens      Stop hook -- invoked by Claude Code
    dashboard-token log-operation   PostToolUse hook -- invoked by Claude Code
    dashboard-token backfill        recovers history from sessions already open
    dashboard-token config          the three optional customizations
    dashboard-token self-update     checks for and installs a new version
    dashboard-token version         prints the version and the paths

The two "log-*" commands are the ones registered in settings.json and run
inside the Claude Code turn: they must be fast and must NEVER let an
unhandled exception escape, otherwise the turn reports a failed hook to
the user.
"""
import os
import sys
import time


def _prepare_import_path():
    """Rende importabili log_tokens / log_operation / generate_dashboard.

    Dentro l'eseguibile impacchettato ci pensa PyInstaller (i moduli sono
    gia' dentro il binario). Lanciato dai sorgenti, invece, quei moduli
    stanno in installer/hooks/, che va aggiunto a mano a sys.path -- serve
    per poter provare il dispatcher senza dover ricostruire l'exe ogni volta.

    [EN] Makes log_tokens / log_operation / generate_dashboard importable.

    Inside the packaged executable PyInstaller takes care of it (the
    modules are already inside the binary). When launched from the sources,
    instead, those modules live in installer/hooks/, which must be added to
    sys.path by hand -- needed to try out the dispatcher without rebuilding
    the exe every time.
    """
    if getattr(sys, "frozen", False):
        return
    here = os.path.dirname(os.path.abspath(__file__))
    hooks = os.path.join(os.path.dirname(here), "installer", "hooks")
    if os.path.isdir(hooks) and hooks not in sys.path:
        sys.path.insert(0, hooks)


_prepare_import_path()

# (dopo _prepare_import_path per costruzione)
# [EN] (after _prepare_import_path, by construction)
import paths        # noqa: E402
import setup_hooks  # noqa: E402
import updater      # noqa: E402
import version      # noqa: E402

# Il testo di aiuto non e' piu' una costante qui: sta nel dizionario, sotto
# la chiave "usage", perche' va tradotto come tutto il resto. Resta pero'
# scritto per esteso e non ricavato da __doc__, per la ragione di sempre: se
# un giorno la build usasse l'ottimizzazione -OO di Python, le docstring
# verrebbero eliminate dal binario e __doc__ sarebbe None.
# [EN] The help text is no longer a constant here: it lives in the
# dictionary, under the "usage" key, because it must be translated like
# everything else. It stays written out in full and not derived from
# __doc__, for the usual reason: if one day the build used Python's -OO
# optimization, docstrings would be stripped from the binary and __doc__
# would be None.
def _T():
    """Il traduttore dei messaggi, legato alla lingua scelta per il
    terminale.

    L'import di generate_dashboard sta DENTRO la funzione e non in cima al
    file: in cima il package non e' ancora raggiungibile, perche' e'
    _prepare_import_path() a metterlo nel percorso di ricerca, e quello gira
    dopo. E' lo stesso motivo per cui gli altri import del package, qui
    dentro, sono tutti dentro le funzioni che li usano.

    [EN] The message translator, bound to the language chosen for the
    terminal.

    The generate_dashboard import lives INSIDE the function and not at the
    top of the file: at the top the package is not reachable yet, because it
    is _prepare_import_path() that puts it on the search path, and that runs
    later. It is the same reason the other package imports in here are all
    inside the functions that use them.
    """
    from generate_dashboard import i18n
    return i18n.translator(i18n.cli_lang())


def _run_log_tokens():
    """Hook Stop: registra i token del turno appena concluso e rigenera le
    pagine HTML. Al termine, fuori dal percorso critico, valuta se e' ora di
    controllare gli aggiornamenti.

    [EN] Stop hook: logs the tokens of the turn that just ended and
    regenerates the HTML pages. At the end, off the critical path, decides
    whether it is time to check for updates."""
    updater.cleanup_stale()
    import log_tokens

    try:
        log_tokens.main()
    finally:
        # In "finally" di proposito: anche se il logging fallisse, il
        # controllo aggiornamenti resta utile -- potrebbe essere proprio la
        # versione nuova a sistemare il problema.
        # [EN] In "finally" on purpose: even if logging failed, the update
        # check is still useful -- the new version might be exactly what
        # fixes the problem.
        updater.maybe_trigger()
    return 0


def _run_log_operation():
    """Hook PostToolUse: registra la singola operazione. Non fa partire il
    controllo aggiornamenti perche' scatta molte volte per turno; se ne
    occupa log-tokens, che scatta una volta sola.

    [EN] PostToolUse hook: logs the single operation. It does not kick off
    the update check because it fires many times per turn; log-tokens takes
    care of that, firing only once."""
    import log_operation

    log_operation.main()
    return 0


def _run_backfill(flags):
    """Recupero retroattivo dello storico dai transcript.

    Lo lancia l'installer subito dopo aver registrato gli hook (come
    sottoprocesso: l'installer e' volutamente magro e non si porta dentro il
    package generate_dashboard, mentre l'applicazione appena installata si').
    Resta anche disponibile a mano, per rilanciarlo o per provarlo a vuoto:
    e' idempotente, rifarlo non duplica nulla.

    [EN] Retroactive recovery of history from the transcripts.

    The installer launches it right after registering the hooks (as a
    subprocess: the installer is deliberately lean and does not carry the
    generate_dashboard package, while the freshly installed application
    does). It also stays available by hand, to rerun it or to try it as a
    dry run: it is idempotent, redoing it duplicates nothing.
    """
    from generate_dashboard import backfill

    rc = backfill.run(dry_run=("--dry-run" in flags))
    if "--no-pause" not in flags:
        print("")
        _pause()
    return rc


def _read_json(path):
    import json

    try:
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
        return json.loads(text) if text.strip() else {}
    except (OSError, ValueError):
        return {}


def _write_json(path, data):
    import json

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _known_accounts():
    """UUID degli account gia' visti nel log dei token, per poterli proporre
    da etichettare invece di farli copiare a mano.

    [EN] UUIDs of the accounts already seen in the token log, so they can
    be offered for labeling instead of having the user copy them by hand."""
    import csv

    csv_path = os.path.join(paths.CLAUDE_DIR, "logs", "tokens.csv")
    accounts = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) > 7 and row[7] and row[7] not in accounts:
                    accounts.append(row[7])
    except OSError:
        pass
    # scarta l'intestazione
    # [EN] drop the header row
    return [a for a in accounts if a != "account"]


def _configure():
    """Le due personalizzazioni facoltative. Non e' un wizard di
    installazione: i percorsi non vanno configurati, si ricavano da soli
    dalla home dell'utente. Questo comando serve solo a chi vuole spostare
    l'output o dare un nome leggibile ai propri account.

    [EN] The two optional customizations. Not an installation wizard: the
    paths need no configuration, they derive themselves from the user's
    home. This command only serves those who want to move the output or
    give their accounts a readable name."""
    config_path = os.path.join(paths.HOOKS_DIR, "dashboard_config.json")
    labels_path = os.path.join(paths.HOOKS_DIR, "account_labels.json")
    default_out = os.path.join(paths.CLAUDE_DIR, "dashboard-token")

    from generate_dashboard import i18n
    T = _T()

    print(T("cfg.title"))
    print(T("cfg.enterKeeps"))
    print("")

    config = _read_json(config_path)
    current = config.get("out_dir") or default_out
    print(T("cfg.outDir"))
    print(T("cfg.current", valore=current))
    answer = input(T("cfg.outDirPrompt")).strip()
    if answer == "-":
        config.pop("out_dir", None)
        _write_json(config_path, config)
        print(T("cfg.backToDefault"))
    elif answer:
        config["out_dir"] = answer
        _write_json(config_path, config)
        print(T("cfg.set"))

    # La lingua dei messaggi a terminale. Le pagine non la leggono da qui:
    # hanno il loro switch e ricordano la scelta nel browser. Questa vale
    # solo per il terminale, ed e' il modo di dirlo una volta per sempre su
    # questa macchina; per un singolo comando basta la variabile d'ambiente
    # DASHBOARD_TOKEN_LANG (vedi i18n.cli_lang).
    # "-" toglie la chiave invece di scrivere un valore: senza preferenza
    # scritta si torna a dedurla dal sistema operativo, che e' una cosa
    # diversa dallo scegliere l'inglese.
    # [EN] The language of the terminal messages. The pages do not read it
    # from here: they have their own switch and remember the choice in the
    # browser. This one applies to the terminal only, and it is the way to
    # say it once and for all on this machine; for a single command the
    # DASHBOARD_TOKEN_LANG environment variable is enough (see
    # i18n.cli_lang).
    # "-" removes the key instead of writing a value: with no preference
    # written we go back to deducing it from the operating system, which is
    # a different thing from choosing English.
    print("")
    print(T("cfg.langTitle"))
    print(T("cfg.current",
            valore=config.get("lang") or T("cfg.langAuto")))
    answer = input(T("cfg.langPrompt", lingue="/".join(i18n.LANGS))).strip()
    if answer == "-":
        config.pop("lang", None)
        _write_json(config_path, config)
        print(T("cfg.backToDefault"))
    elif answer and i18n.normalize(answer):
        config["lang"] = i18n.normalize(answer)
        _write_json(config_path, config)
        print(T("cfg.set"))

    accounts = _known_accounts()
    if accounts:
        print("")
        print(T("cfg.labels"))
        labels = _read_json(labels_path)
        changed = False
        for uuid in accounts:
            current_label = labels.get(uuid, "")
            prompt = "  {} [{}]: ".format(uuid, current_label or T("cfg.noLabel"))
            answer = input(prompt).strip()
            if answer:
                labels[uuid] = answer
                changed = True
        if changed:
            _write_json(labels_path, labels)
            print(T("cfg.labelsSaved"))

    print("")
    print(T("cfg.done"))
    return 0


def _selftest():
    """Controllo di sanita' del binario, lanciato dalla CI subito dopo la
    build. Non tocca niente su disco: importa tutto quello che serve a
    runtime e carica i template.

    Serve perche' un errore di impacchettamento (un hiddenimports mancante,
    i template non inclusi) produce un exe che parte, si installa senza una
    lamentela, e poi fallisce al primo turno vero su chi l'ha installata. Meglio
    scoprirlo qui, dove blocca la release.

    [EN] Sanity check of the binary, run by the CI right after the build.
    Touches nothing on disk: it imports everything needed at runtime and
    loads the templates.

    It exists because a packaging mistake (a missing hiddenimports entry,
    templates left out) produces an exe that starts, installs without a
    complaint, and then fails on the first real turn after installation.
    Better to find out here, where it blocks the release.
    """
    import log_operation  # noqa: F401
    import log_tokens  # noqa: F401
    from generate_dashboard import backfill  # noqa: F401
    from generate_dashboard import templating

    for name in ("dashboard.html", "pricing.html", "guide.html",
                 "guide.en.html"):
        body = templating.load_template(name)
        if not body.strip():
            print("FALLITO: template {} vuoto".format(name))
            return 1
        print("  template {}: {} byte".format(name, len(body)))

    # Le due guide sono lo stesso documento in due lingue, e devono restare
    # la stessa STRUTTURA: e' il prezzo di averle come due file invece che
    # come un template solo tradotto a runtime (il perche' di quella scelta
    # e' nel docstring di render_guide.render).
    # Il confronto guarda gli id delle sezioni, che sono anche le ancore dei
    # collegamenti interni e i bersagli degli aria-controls dei bottoni: se
    # divergono, in una delle due lingue un bottone smette di dire a quale
    # riquadro appartiene, e un collegamento porta nel vuoto. Sono guasti
    # che nessuno nota rileggendo la traduzione, e che invece qui saltano
    # fuori subito.
    # Lo stile non ha bisogno di controlli: vive in guide_css.py, e i due
    # template lo richiamano invece di portarselo scritto dentro.
    # [EN] The two guides are the same document in two languages, and must
    # stay the same STRUCTURE: that is the price of having them as two files
    # rather than one template translated at runtime (why that choice was
    # made is in render_guide.render's docstring).
    # The comparison looks at the sections' ids, which are also the anchors
    # of the internal links and the targets of the buttons' aria-controls:
    # if they diverge, in one of the two languages a button stops saying
    # which panel it belongs to, and a link leads nowhere. These are faults
    # nobody notices while re-reading the translation, and which instead
    # show up here immediately.
    # The style needs no check: it lives in guide_css.py, and the two
    # templates call it in rather than carrying it written inside.
    import re

    def _ids(name):
        body = templating.load_template(name)
        return (sorted(re.findall(r'id="([^"]+)"', body)),
                sorted(re.findall(r'aria-controls="([^"]+)"', body)))

    it_ids, it_ctrl = _ids("guide.html")
    en_ids, en_ctrl = _ids("guide.en.html")
    if it_ids != en_ids or it_ctrl != en_ctrl:
        print("FALLITO: guide.html e guide.en.html hanno strutture diverse")
        print("  solo in guide.html:    {}".format(
            sorted(set(it_ids + it_ctrl) - set(en_ids + en_ctrl))))
        print("  solo in guide.en.html: {}".format(
            sorted(set(en_ids + en_ctrl) - set(it_ids + it_ctrl))))
        return 1
    print("  guide.html / guide.en.html: {} sezioni allineate".format(len(it_ctrl)))

    # Ogni valuta offerta nella combo deve avere un cambio, un simbolo e un
    # codice. Senza cambio verrebbe convertita a 1.0, cioe' mostrerebbe
    # importi in dollari con sopra un altro simbolo: nessun errore, nessuna
    # pagina rotta, solo numeri sbagliati che sembrano giusti. E' il tipo di
    # difetto che si nota mesi dopo, quindi si ferma qui.
    # [EN] Every currency offered in the combo must have a rate, a symbol
    # and a code. With no rate it would be converted at 1.0, that is, it
    # would show dollar amounts with another symbol on them: no error, no
    # broken page, just wrong numbers that look right. It is the kind of
    # flaw noticed months later, so it is stopped here.
    from generate_dashboard import i18n, pricing
    mancanti = [
        (c, [nome for nome, tabella in (("USD_RATES", pricing.USD_RATES),
                                        ("CURRENCY_SYMBOLS", i18n.CURRENCY_SYMBOLS),
                                        ("CURRENCY_CODES", i18n.CURRENCY_CODES))
             if c not in tabella])
        for c in i18n.CURRENCIES
    ]
    mancanti = [(c, dove) for c, dove in mancanti if dove]
    if mancanti:
        print("FALLITO: valute senza tutti i dati che servono")
        for c, dove in mancanti:
            print("  {}: manca da {}".format(c, ", ".join(dove)))
        return 1
    print("  valute: {} complete (cambi del {})".format(
        len(i18n.CURRENCIES), pricing.USD_RATES_DATE))

    print("selftest OK ({})".format(version.VERSION))
    return 0


def _pause():
    try:
        input(_T()("misc.pressEnter"))
    except (EOFError, KeyboardInterrupt):
        pass


def _interactive_update():
    """Il "pulsante aggiorna": cos'e' il doppio click sull'applicazione gia'
    installata.

    Esiste perche' un pulsante dentro la dashboard non e' possibile -- quella
    e' una pagina HTML aperta nel browser, e un browser non puo' lanciare un
    eseguibile locale. Questa e' la cosa piu' vicina a un pulsante che si
    possa dare a chi non apre mai un terminale.

    [EN] The "update button": what a double click on the already installed
    application is.

    It exists because a button inside the dashboard is not possible -- that
    is an HTML page opened in the browser, and a browser cannot launch a
    local executable. This is the closest thing to a button you can give
    someone who never opens a terminal.
    """
    T = _T()
    print("dashboard-token {}".format(version.VERSION))
    print("")
    print(T("upd.launchedByClaude"))
    print(T("upd.yourDashboard"))
    print("  {}".format(os.path.join(paths.CLAUDE_DIR, "dashboard-token", "dashboard.html")))
    print("")
    print(T("upd.checking"))

    found = updater.check_latest(print)
    if found is None:
        # check_latest ha gia' stampato il motivo: siamo aggiornati, oppure
        # la rete non risponde.
        # [EN] check_latest has already printed the reason: we are up to
        # date, or the network is not responding.
        print("")
        _pause()
        return 0

    tag, entry, assets = found
    print("")
    print(T("upd.available", nuova=tag, attuale=version.VERSION))
    try:
        answer = input(T("upd.prompt")).strip()
    except (EOFError, KeyboardInterrupt):
        answer = T("upd.promptNo")
    # La lettera del "no" arriva dalla traduzione: in italiano si risponde
    # "n", in inglese pure, ma una terza lingua potrebbe non farlo, e il
    # confronto deve restare quello della lingua in cui e' stata posta la
    # domanda.
    # [EN] The "no" letter comes from the translation: in Italian one
    # answers "n", in English too, but a third language might not, and the
    # comparison must stay the one of the language the question was asked in.
    if answer[:1].lower() == T("upd.promptNo")[:1].lower():
        print(T("upd.declined"))
        print("")
        _pause()
        return 0

    print(T("upd.downloading"))
    if not updater.apply_update(tag, entry, assets, print):
        print("")
        print(T("upd.failed1"))
        print(T("upd.failed2"))
        print("")
        _pause()
        return 0

    print("")
    print(T("upd.started1"))
    print(T("upd.started2"))
    # Nessuna pausa qui, di proposito: finche' questo processo vive, la
    # cartella da cui gira resta bloccata e l'installer non puo'
    # sostituirla. I pochi secondi di attesa servono solo a dare il tempo
    # di leggere -- l'installer riprova comunque per due minuti.
    # [EN] No pause here, on purpose: as long as this process lives, the
    # folder it runs from stays locked and the installer cannot replace
    # it. The few seconds of waiting only give the user time to read --
    # the installer retries for two minutes anyway.
    time.sleep(4)
    return 0


def _print_version():
    T = _T()
    ruolo = T("misc.roleInstaller") if paths.is_installer() else T("misc.roleApp")
    print("dashboard-token {} ({})".format(version.VERSION, ruolo))
    print(T("misc.exe", valore=paths.current_exe() or T("misc.fromSource")))
    print(T("misc.installed", valore=paths.INSTALL_DIR))
    print(T("misc.settings", valore=paths.SETTINGS_PATH))
    print(T("misc.repo",
            valore="https://github.com/{}".format(version.GITHUB_REPO)))
    return 0


def main(argv):
    command = argv[1] if len(argv) > 1 else None
    flags = argv[2:]

    # Nessun argomento = doppio click. Sull'installer scaricato da GitHub
    # significa "installa", con la pausa finale che tiene aperta la finestra
    # perche' l'utente legga il riepilogo (senza, la console si chiuderebbe
    # di colpo). Sull'applicazione gia' installata non c'e' niente da fare:
    # e' Claude Code che la chiama, con un sottocomando.
    # [EN] No argument = double click. On the installer downloaded from
    # GitHub it means "install", with the final pause keeping the window
    # open so the user can read the summary (without it, the console would
    # slam shut). On the already installed application there is nothing to
    # do: it is Claude Code that invokes it, with a subcommand.
    if command is None:
        if paths.is_installer():
            return setup_hooks.install(interactive=True)
        return _interactive_update()

    if command == "install":
        return setup_hooks.install(interactive="--no-pause" not in flags)
    if command == "log-tokens":
        return _run_log_tokens()
    if command == "log-operation":
        return _run_log_operation()
    if command == "self-update":
        return updater.run_update(verbose=("--verbose" in flags or "-v" in flags))
    if command == "backfill":
        return _run_backfill(flags)
    if command == "selftest":
        return _selftest()
    if command == "config":
        return _configure()
    if command in ("version", "--version", "-V"):
        return _print_version()
    if command in ("help", "--help", "-h"):
        print(_T()("usage").strip())
        return 0

    T = _T()
    print(T("misc.unknownCommand", comando=command))
    print(T("usage").strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
