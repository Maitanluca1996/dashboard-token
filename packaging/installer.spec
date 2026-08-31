# -*- mode: python ; coding: utf-8 -*-
"""Stadio 2: l'INSTALLER, in forma onefile.

    pyinstaller --distpath dist packaging/installer.spec

Richiede che lo stadio 1 sia gia' stato costruito: si porta dentro, come
dato impacchettato, l'intera cartella prodotta da app.spec. E' questo il
file unico che si scarica dalle Release e su cui si fa doppio click.

Qui il costo di avvio del onefile non conta: viene lanciato una volta per
installare, non a ogni turno.

L'installer non genera nessuna dashboard -- si limita a estrarre il payload
e a scrivere settings.json -- e infatti NON si porta dentro i template HTML.
Un pezzo del package pero' gli serve: i messaggi che stampa a terminale
passano da cli._T(), che chiede la lingua a generate_dashboard.i18n. Senza
quel package il binario muore con ModuleNotFoundError al primo comando, e il
doppio click e' un comando come gli altri. Il peso aggiunto e' trascurabile:
sono moduli di solo testo, accanto a un payload che gia' contiene
l'applicazione intera.

[EN] Stage 2: the INSTALLER, in onefile form.

    pyinstaller --distpath dist packaging/installer.spec

Requires stage 1 to have been built already: it carries, as bundled data,
the whole folder produced by app.spec. This is the single file that gets
downloaded from the Releases and double-clicked.

Here the startup cost of the onefile does not matter: it is launched once
to install, not on every turn.

The installer generates no dashboard -- it just extracts the payload and
writes settings.json -- and indeed it does NOT carry the HTML templates.
One piece of the package it does need, though: the messages it prints on the
terminal go through cli._T(), which asks generate_dashboard.i18n for the
language. Without that package the binary dies with ModuleNotFoundError on
the first command, and a double click is a command like any other. The added
weight is negligible: they are text-only modules, sitting next to a payload
that already contains the whole application.
"""
import os

ROOT = os.path.dirname(SPECPATH)
HOOKS = os.path.join(ROOT, "installer", "hooks")

# Dove si trova l'applicazione costruita allo stadio 1. Sovrascrivibile con
# una variabile d'ambiente per non legare la ricetta a un percorso fisso.
# [EN] Where the application built in stage 1 lives. Overridable with an
# environment variable so the recipe is not tied to a fixed path.
PAYLOAD = os.environ.get(
    "DASHBOARD_TOKEN_PAYLOAD", os.path.join(ROOT, "dist", "app", "dashboard-token")
)
if not os.path.isdir(PAYLOAD):
    raise SystemExit(
        "Payload non trovato in {}.\n"
        "Costruisci prima lo stadio 1:\n"
        "  pyinstaller --distpath dist/app packaging/app.spec".format(PAYLOAD)
    )

a = Analysis(
    [os.path.join(SPECPATH, "cli.py")],
    # HOOKS serve a trovare generate_dashboard, che sta in
    # installer/hooks/ e non accanto a cli.py.
    # [EN] HOOKS is there to find generate_dashboard, which lives in
    # installer/hooks/ and not next to cli.py.
    pathex=[SPECPATH, HOOKS],
    binaries=[],
    # L'intera applicazione finisce nella cartella "payload" dentro il
    # binario. Il nome deve combaciare con paths._PAYLOAD_DIR_NAME: e' cosi'
    # che cli.py capisce di essere l'installer e non l'applicazione.
    # [EN] The whole application ends up in the "payload" folder inside the
    # binary. The name must match paths._PAYLOAD_DIR_NAME: that is how
    # cli.py knows it is the installer and not the application.
    datas=[(PAYLOAD, "payload")],
    # cli._T() importa generate_dashboard DENTRO la funzione (per il motivo
    # spiegato nel suo docstring): un import che l'analisi statica di
    # PyInstaller non puo' vedere, e che va quindi dichiarato a mano.
    # Niente "backfill" qui, al contrario di app.spec: il recupero dello
    # storico l'installer lo lancia come sottoprocesso dell'applicazione
    # appena installata, non lo importa.
    # [EN] cli._T() imports generate_dashboard INSIDE the function (for the
    # reason spelled out in its docstring): an import PyInstaller's static
    # analysis cannot see, and which must therefore be declared by hand.
    # No "backfill" here, unlike app.spec: the installer runs the history
    # recovery as a subprocess of the freshly installed application, it does
    # not import it.
    hiddenimports=["generate_dashboard"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc", "doctest", "test", "setuptools", "pip"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="dashboard-token-installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
