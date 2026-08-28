"""Riscrive la costante VERSION in packaging/version.py prima della build.

Lo usa la GitHub Action per timbrare nel binario il tag della release che
sta per pubblicare. Sta in un file a parte, e non in una riga infilata nel
workflow YAML, perche' li' le virgolette annidate diventano illeggibili in
fretta e un errore non si scopre finche' non fallisce una build.

    python packaging/set_version.py v1.0.42

[EN] Rewrites the VERSION constant in packaging/version.py before the
build.

The GitHub Action uses it to stamp into the binary the tag of the release
about to be published. It lives in a separate file, rather than in a line
tucked into the workflow YAML, because nested quotes there become
unreadable fast and a mistake goes unnoticed until a build fails.

    python packaging/set_version.py v1.0.42
"""
import io
import os
import re
import sys

PLACEHOLDER = re.compile(r'^VERSION = ".*"$', re.MULTILINE)


def main(argv):
    if len(argv) != 2:
        print("uso: python packaging/set_version.py <versione>")
        return 2

    new_version = argv[1]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.py")
    source = io.open(path, encoding="utf-8").read()

    replaced, count = PLACEHOLDER.subn('VERSION = "{}"'.format(new_version), source, count=1)
    if count != 1:
        print("ERRORE: riga VERSION non trovata in {}".format(path))
        return 1

    io.open(path, "w", encoding="utf-8", newline="").write(replaced)
    print("VERSION = {}".format(new_version))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
