"""Identita' della build: numero di versione e coordinate per l'auto-update.

Questo file e' l'unico punto in cui e' scritta la versione dell'eseguibile.
In sviluppo resta "0.0.0-dev"; la GitHub Action, prima di lanciare
PyInstaller, lo riscrive con il numero della release che sta per pubblicare
(vedi .github/workflows/release.yml). Cosi' l'exe "sa" quale versione e',
e puo' confrontarla con l'ultima release pubblicata su GitHub per capire
se deve aggiornarsi.

[EN] Identity of the build: version number and coordinates for the
auto-update.

This file is the only place where the executable's version is written. In
development it stays "0.0.0-dev"; the GitHub Action, before launching
PyInstaller, rewrites it with the number of the release about to be
published (see .github/workflows/release.yml). This way the exe "knows"
which version it is, and can compare it with the latest release published
on GitHub to figure out whether it must update itself.
"""
import sys

# Riscritta dalla CI a ogni build. Il confronto con la release piu' recente
# e' una semplice disuguaglianza di stringhe ("sono diverso dall'ultima
# pubblicata?"), non un ordinamento semantico: non serve, perche' l'unica
# fonte di verita' e' sempre e solo l'ultima release su GitHub.
# [EN] Rewritten by the CI on every build. The comparison with the most
# recent release is a plain string inequality ("am I different from the
# last one published?"), not a semantic ordering: none is needed, because
# the only source of truth is always and only the latest release on GitHub.
VERSION = "0.0.0-dev"

# Repo pubblica da cui scaricare gli aggiornamenti. Essendo pubblica, le
# chiamate all'API di GitHub e il download degli asset non richiedono nessun
# token: e' il motivo per cui non c'e' niente da configurare.
# [EN] Public repo the updates are downloaded from. Being public, the
# GitHub API calls and the asset downloads require no token: this is why
# there is nothing to configure.
GITHUB_REPO = "Maitanluca1996/dashboard-token"

LATEST_RELEASE_API = "https://api.github.com/repos/{}/releases/latest".format(GITHUB_REPO)

# Nome del file pubblicato nella release per ciascun sistema operativo.
# Deve combaciare esattamente con i nomi prodotti dalla GitHub Action.
# [EN] Name of the file published in the release for each operating
# system. Must match exactly the names produced by the GitHub Action.
_ASSET_BY_PLATFORM = {
    "win32": "dashboard-token-windows.exe",
    "darwin": "dashboard-token-macos",
    "linux": "dashboard-token-linux",
}

# Nome con cui l'eseguibile si installa in ~/.claude/hooks/. Volutamente
# uguale su tutte le piattaforme (a parte l'estensione .exe di Windows),
# cosi' il percorso registrato in settings.json e' prevedibile.
# [EN] Name under which the executable installs itself in ~/.claude/hooks/.
# Deliberately the same on every platform (apart from the Windows .exe
# extension), so the path registered in settings.json is predictable.
INSTALLED_NAME = "dashboard-token.exe" if sys.platform == "win32" else "dashboard-token"


def asset_name():
    """Nome dell'asset di release da scaricare per la piattaforma corrente,
    oppure None se giriamo su un sistema per cui non pubblichiamo binari
    (in quel caso l'auto-update semplicemente non fa nulla).

    [EN] Name of the release asset to download for the current platform,
    or None if we are running on a system we publish no binaries for (in
    that case the auto-update simply does nothing)."""
    return _ASSET_BY_PLATFORM.get(sys.platform)
