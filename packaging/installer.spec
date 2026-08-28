# -*- mode: python ; coding: utf-8 -*-
"""Stadio 2: l'INSTALLER, in forma onefile.

    pyinstaller --distpath dist packaging/installer.spec

Richiede che lo stadio 1 sia gia' stato costruito: si porta dentro, come
dato impacchettato, l'intera cartella prodotta da app.spec. E' questo il
file unico che si scarica dalle Release e su cui si fa doppio click.

Qui il costo di avvio del onefile non conta: viene lanciato una volta per
installare, non a ogni turno.

L'installer NON ha bisogno dei template ne' dei moduli degli hook: non
genera nessuna dashboard, si limita a estrarre il payload e a scrivere
settings.json. Tenerlo magro tiene piccolo il file da scaricare.

[EN] Stage 2: the INSTALLER, in onefile form.

    pyinstaller --distpath dist packaging/installer.spec

Requires stage 1 to have been built already: it carries, as bundled data,
the whole folder produced by app.spec. This is the single file that gets
downloaded from the Releases and double-clicked.

Here the startup cost of the onefile does not matter: it is launched once
to install, not on every turn.

The installer does NOT need the templates nor the hook modules: it
generates no dashboard, it just extracts the payload and writes
settings.json. Keeping it lean keeps the download small.
"""
import os

ROOT = os.path.dirname(SPECPATH)

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
    pathex=[SPECPATH],
    binaries=[],
    # L'intera applicazione finisce nella cartella "payload" dentro il
    # binario. Il nome deve combaciare con paths._PAYLOAD_DIR_NAME: e' cosi'
    # che cli.py capisce di essere l'installer e non l'applicazione.
    # [EN] The whole application ends up in the "payload" folder inside the
    # binary. The name must match paths._PAYLOAD_DIR_NAME: that is how
    # cli.py knows it is the installer and not the application.
    datas=[(PAYLOAD, "payload")],
    hiddenimports=[],
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
