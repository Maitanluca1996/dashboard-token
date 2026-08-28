# Dashboard token usage — Python-script installation / installazione a script Python

## 🇬🇧 English

> **You probably don't need this page.** The recommended way to install is to
> download the executable from the
> [Releases](https://github.com/Maitanluca1996/dashboard-token/releases/latest):
> a single file, double click, no Python required, and it updates itself with
> every new version. See the [main README](../README.md).
>
> Described below is the "classic" Python-script installation, which remains
> valid and supported: it is meant for those who develop the project, those
> who prefer not to run an unsigned binary, or those on a platform no
> builds are published for.

Shows the costs/tokens consumed with Claude Code, through a local HTML
dashboard that refreshes itself at every turn. No data leaves your PC: it only
reads the logs Claude Code already writes to `~/.claude/logs`.

### Installation (1 minute)

1. Copy the whole `installer` folder (or the zip) anywhere on your PC — no
   required location; you can run it straight from where you unzipped it.
2. **Windows**: double-click **`install.cmd`**.
   **macOS/Linux**: open a terminal in this folder and run
   `bash install.sh`.
3. If it asks to install Python and you don't have it, answer S (for "sì",
   yes — see "Prerequisites" below). If Claude Code was already open, restart
   it (the hooks take effect from the next session). At the end of the first
   turn you will find the dashboard at
   `~/.claude/dashboard-token/dashboard.html`
   (`%USERPROFILE%\.claude\...` on Windows).

No questions beyond the optional Python installation: fixed paths, no
administrator rights needed to install the hooks, everything ends up under
your `~/.claude/`.

### Updates

When a newer version comes out, download it again and re-run `install.cmd`
(or `install.sh`): it recognizes the hooks already
installed (by file name, not by the exact command) and updates their
definition in place, without creating duplicates. Safe to re-run as many times
as you like.

### Prerequisites

- **Python 3** reachable as `python3` in the PATH. No other dependency: the
  hooks are invoked directly by Claude Code (no shell/bash involved).

If it is missing, the script tells you and **offers to install it for you**
(it asks for S/n — yes/no — confirmation before proceeding, and never does it
without asking):

- **Windows**: `python3` often appears to be "found" even without Python
  installed — it is the Microsoft Store alias, which does not run real Python.
  The script detects this by actually trying to execute it (the path alone is
  not enough: on some machines that alias still resolves to a real
  installation). If you confirm, it installs Python 3.12 via `winget`
  (included in Windows 11); if `winget` is not available, it points you to the
  download link.
- **macOS**: if you confirm, it tries Homebrew (`brew install python3`) if
  present, otherwise it runs `python3 --version` to trigger the native
  installation prompt for the Command Line Tools (which include Python).
- **Linux**: if you confirm, it uses the first package manager it finds among
  `apt-get`/`dnf`/`pacman` (it may ask for the sudo password).

In any case you can answer "n" and install it manually yourself, then re-run
`install.cmd`/`install.sh`.

> **Note**: `install.sh` mirrors the logic of `install.ps1`; the
> `settings.json` merge is covered by the tests, while the package-manager
> branches have not been exercised on macOS/Linux yet. Open an issue if you
> run into trouble.

### Optional customizations

Both are optional and local to your machine:

- `~/.claude/hooks/dashboard_config.json` — to generate the dashboard in a
  folder other than the default one:
  ```json
  { "out_dir": "C:\\percorso\\a\\piacere" }
  ```
  (on macOS/Linux: `{ "out_dir": "/percorso/a/piacere" }`)
- `~/.claude/hooks/account_labels.json` — to show a readable label instead of
  the account UUID when you use multiple Claude accounts on the same PC:
  ```json
  { "<uuid-account>": "lavoro", "<altro-uuid>": "personale" }
  ```

### What `install.cmd` / `install.sh` does

- Verifies that `python3` actually works, offering to install it if needed
  (see "Prerequisites").
- Copies the `generate_dashboard/` package and the `log_tokens.py`,
  `log_operation.py` scripts into `~/.claude/hooks/`.
- Registers (or updates, if already present) the `Stop` and `PostToolUse`
  hooks in `~/.claude/settings.json` in "exec form" (`command`+`args`, no
  shell), without touching any hooks already present for other purposes.

---

## 🇮🇹 Italiano

> **Probabilmente non ti serve questa pagina.** Il modo consigliato di
> installare e' scaricare l'eseguibile dalle
> [Release](https://github.com/Maitanluca1996/dashboard-token/releases/latest):
> un file solo, doppio click, nessun Python richiesto, e si aggiorna da solo
> a ogni nuova versione. Vedi il [README principale](../README.md).
>
> Quella descritta qui sotto e' l'installazione "classica" a script Python,
> che resta valida e supportata: serve a chi sviluppa il progetto, a chi
> preferisce non eseguire un binario non firmato, o a chi sta su una
> piattaforma per cui non vengono pubblicate build.

Mostra costi/token consumati con Claude Code, generata da una dashboard HTML
locale che si autoaggiorna ad ogni turno. Nessun dato lascia il tuo PC: legge
solo i log che Claude Code scrive gia' in `~/.claude/logs`.

### Installazione (1 minuto)

1. Copia l'intera cartella `installer` (o lo zip) dove vuoi sul tuo PC —
   nessuna posizione obbligatoria, puoi lanciarla direttamente da dove
   l'hai scompattata.
2. **Windows**: doppio click su **`install.cmd`**.
   **macOS/Linux**: apri un terminale in questa cartella e lancia
   `bash install.sh`.
3. Se ti chiede di installare Python e non ce l'hai, rispondi S (vedi
   "Prerequisiti" sotto). Se Claude Code era gia' aperto, riavvialo (gli
   hook si attivano dalla sessione successiva). Alla fine del primo turno
   trovi la dashboard in `~/.claude/dashboard-token/dashboard.html`
   (`%USERPROFILE%\.claude\...` su Windows).

Nessuna domanda oltre all'eventuale installazione di Python: percorsi fissi,
nessun diritto da amministratore per l'installazione degli hook, tutto
finisce sotto il tuo `~/.claude/`.

### Aggiornamenti

Quando esce una versione piu' recente, riscaricala e rilancia `install.cmd`
(o `install.sh`): riconosce gli hook gia'
installati (dal nome file, non dal comando esatto) e ne aggiorna la
definizione sul posto, senza creare doppioni. Sicuro da rilanciare quante
volte vuoi.

### Prerequisiti

- **Python 3** raggiungibile come `python3` nel PATH. Nessun'altra
  dipendenza: gli hook sono invocati direttamente da Claude Code (nessuna
  shell/bash coinvolta).

Se manca, lo script te lo segnala e **offre di installarlo per te** (chiede
conferma S/n prima di procedere, non lo fa mai senza chiedere):

- **Windows**: `python3` risulta spesso "trovato" anche senza Python
  installato — e' l'alias di Microsoft Store, che non esegue Python vero. Lo
  script se ne accorge provando a eseguirlo davvero (non basta il percorso:
  su alcune macchine quell'alias risolve comunque a un'installazione reale).
  Se confermi, installa Python 3.12 via `winget` (incluso in Windows 11); se
  `winget` non e' disponibile, ti manda al link di download.
- **macOS**: se confermi, prova Homebrew (`brew install python3`) se
  presente, altrimenti lancia `python3 --version` per innescare il prompt
  nativo di installazione dei Command Line Tools (include Python).
- **Linux**: se confermi, usa il primo gestore pacchetti che trova tra
  `apt-get`/`dnf`/`pacman` (puo' chiedere la password sudo).

In ogni caso puoi rispondere "n" e installarlo tu manualmente, poi rilanciare
`install.cmd`/`install.sh`.

> **Nota**: `install.sh` rispecchia la logica di `install.ps1`; il merge di
> `settings.json` e' coperto dai test, mentre i rami dei singoli gestori
> pacchetti non sono ancora stati esercitati su macOS/Linux. Se incontri
> problemi, apri una issue.

### Personalizzazioni facoltative

Sono entrambe opzionali e locali alla tua macchina:

- `~/.claude/hooks/dashboard_config.json` — per generare la dashboard in una
  cartella diversa da quella di default:
  ```json
  { "out_dir": "C:\\percorso\\a\\piacere" }
  ```
  (su macOS/Linux: `{ "out_dir": "/percorso/a/piacere" }`)
- `~/.claude/hooks/account_labels.json` — per mostrare un'etichetta leggibile
  invece dell'UUID account quando usi piu' account Claude sullo stesso PC:
  ```json
  { "<uuid-account>": "lavoro", "<altro-uuid>": "personale" }
  ```

### Cosa fa `install.cmd` / `install.sh`

- Verifica che `python3` funzioni davvero, offrendo di installarlo se serve
  (vedi "Prerequisiti").
- Copia il package `generate_dashboard/` e gli script `log_tokens.py`,
  `log_operation.py` in `~/.claude/hooks/`.
- Registra (o aggiorna, se gia' presenti) gli hook `Stop` e `PostToolUse` in
  `~/.claude/settings.json` in "exec form" (`command`+`args`, senza shell),
  senza toccare eventuali hook gia' presenti per altri scopi.
