# -*- mode: python ; coding: utf-8 -*-
"""Stadio 1: l'APPLICAZIONE, in forma onedir.

    pyinstaller --distpath dist/app packaging/app.spec

Produce dist/app/dashboard-token/ (un eseguibile piu' una cartella
_internal). E' questa la forma che finisce installata in
~/.claude/hooks/dashboard-token/ e che viene registrata negli hook.

Onedir e non onefile per una ragione misurata: un onefile si scompatta in
una cartella temporanea a ogni avvio (~880 ms), e l'hook PostToolUse scatta
a ogni chiamata di strumento. In onedir l'avvio e' ~225 ms.

PyInstaller non fa cross-compilazione: ogni sistema operativo va costruito
sul suo (per questo la GitHub Action usa una matrice di tre runner).

[EN] Stage 1: the APPLICATION, in onedir form.

    pyinstaller --distpath dist/app packaging/app.spec

Produces dist/app/dashboard-token/ (one executable plus an _internal
folder). This is the form that ends up installed in
~/.claude/hooks/dashboard-token/ and gets registered in the hooks.

Onedir rather than onefile for a measured reason: a onefile unpacks itself
into a temporary folder on every start (~880 ms), and the PostToolUse hook
fires on every tool call. In onedir form startup takes ~225 ms.

PyInstaller does not cross-compile: each operating system must be built on
its own kind (which is why the GitHub Action uses a matrix of three
runners).
"""
import os

# SPECPATH lo definisce PyInstaller: e' la cartella che contiene questo file
# (packaging/). Da li' si risale alla radice del repo.
# [EN] SPECPATH is defined by PyInstaller: it is the folder containing this
# file (packaging/). From there we walk up to the repo root.
ROOT = os.path.dirname(SPECPATH)
HOOKS = os.path.join(ROOT, "installer", "hooks")
TEMPLATES = os.path.join(HOOKS, "generate_dashboard", "templates")

a = Analysis(
    [os.path.join(SPECPATH, "cli.py")],
    # pathex: dove cercare i moduli da impacchettare. installer/hooks/
    # contiene il codice degli hook che finisce dentro il binario.
    # [EN] pathex: where to look for the modules to bundle.
    # installer/hooks/ holds the hook code that goes into the binary.
    pathex=[SPECPATH, HOOKS],
    binaries=[],
    # datas: i template HTML servono a runtime e vanno estratti sotto
    # "generate_dashboard/templates" -- lo stesso percorso che templating.py
    # cerca dentro sys._MEIPASS.
    # [EN] datas: the HTML templates are needed at runtime and must be
    # extracted under "generate_dashboard/templates" -- the same path that
    # templating.py looks up inside sys._MEIPASS.
    datas=[(TEMPLATES, "generate_dashboard/templates")],
    # hiddenimports: moduli che PyInstaller non vede analizzando il codice.
    # log_tokens importa generate_dashboard dentro una funzione, e cli.py
    # importa log_tokens/log_operation solo al momento del bisogno: import
    # "nascosti" da dichiarare a mano, altrimenti resterebbero fuori dal
    # binario e l'app fallirebbe al primo turno.
    # generate_dashboard.backfill e' un caso in piu': cli.py lo importa solo
    # dentro _run_backfill(), e __init__.py non lo tira dentro (il recupero
    # retroattivo non serve al percorso critico di ogni turno).
    # [EN] hiddenimports: modules PyInstaller cannot see by analyzing the
    # code. log_tokens imports generate_dashboard inside a function, and
    # cli.py imports log_tokens/log_operation only when needed: "hidden"
    # imports to declare by hand, otherwise they would be left out of the
    # binary and the app would fail on the first turn.
    # generate_dashboard.backfill is one more case: cli.py imports it only
    # inside _run_backfill(), and __init__.py does not pull it in (the
    # retroactive recovery is not needed on the critical path of each turn).
    hiddenimports=[
        "log_tokens", "log_operation",
        "generate_dashboard", "generate_dashboard.backfill",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # ATTENZIONE a cosa si aggiunge qui: "email" sembra inutile ma NON va
    # escluso, perche' http.client (e quindi urllib.request, e quindi tutto
    # l'auto-update) lo importa per il parsing degli header HTTP. Escluderlo
    # produce un'app che si installa benissimo e poi non si aggiorna piu',
    # in silenzio.
    # [EN] BE CAREFUL what gets added here: "email" looks useless but must
    # NOT be excluded, because http.client (and therefore urllib.request,
    # and therefore the whole auto-update) imports it to parse HTTP headers.
    # Excluding it produces an app that installs just fine and then silently
    # never updates again.
    excludes=["tkinter", "unittest", "pydoc", "doctest", "test", "setuptools", "pip"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    # onedir: i binari stanno accanto, non dentro
    # [EN] onedir: the binaries sit alongside, not inside
    exclude_binaries=True,
    name="dashboard-token",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX comprime ma fa scattare molti antivirus: non ne vale la pena
    # [EN] UPX compresses but trips many antivirus scanners: not worth it
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="dashboard-token",
)
