"""Calcola lo SHA-256 di un file nel formato di sha256sum.

    python packaging/sha256.py dashboard-token-windows.exe

Stampa "<hash>  <nomefile>" (due spazi, come vuole il formato standard), che
e' esattamente cio' che updater._expected_digest() si aspetta di trovare
nell'asset SHA256SUMS della release.

Esiste perche' gli strumenti da riga di comando per l'hash NON sono
uniformi sui runner di GitHub: su macOS c'e' "shasum" ma non "sha256sum",
sul Git Bash di Windows c'e' "sha256sum" ma non "shasum", su Linux ci sono
entrambi. Python invece e' gia' installato su tutti e tre (serve per la
build), quindi e' l'unica cosa su cui si puo' contare davvero.

[EN] Computes the SHA-256 of a file in sha256sum format.

    python packaging/sha256.py dashboard-token-windows.exe

Prints "<hash>  <filename>" (two spaces, as the standard format requires),
which is exactly what updater._expected_digest() expects to find in the
release's SHA256SUMS asset.

It exists because the command-line hashing tools are NOT uniform across
GitHub runners: macOS has "shasum" but not "sha256sum", Git Bash on
Windows has "sha256sum" but not "shasum", Linux has both. Python, on the
other hand, is already installed on all three (the build needs it), so it
is the only thing you can truly count on.
"""
import hashlib
import os
import sys

# Legge a blocchi invece che tutto in memoria: i binari sono da ~20 MB, non
# e' un problema di RAM, ma non c'e' motivo di caricarli interi.
# [EN] Reads in blocks instead of all in memory: the binaries are ~20 MB,
# not a RAM problem, but there is no reason to load them whole.
BLOCK = 1024 * 1024


def main(argv):
    if len(argv) != 2:
        print("uso: python packaging/sha256.py <file>")
        return 2

    path = argv[1]
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(BLOCK), b""):
            digest.update(block)

    # Solo il nome del file, non il percorso: e' cosi' che appare nella
    # release, ed e' su quello che l'updater fa il confronto.
    # [EN] Only the file name, not the path: that is how it appears in the
    # release, and that is what the updater compares against.
    print("{}  {}".format(digest.hexdigest(), os.path.basename(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
