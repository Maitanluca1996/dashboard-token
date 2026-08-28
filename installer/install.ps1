#requires -Version 5.1
<#
Installa la dashboard token usage di Claude Code sul PC corrente:
- verifica/offre di installare python3 se manca (via winget, con conferma)
- copia gli hook (Python puro) in ~/.claude/hooks
- registra gli hook Stop/PostToolUse in ~/.claude/settings.json in "exec form"
  (command+args, nessuna shell -- non serve bash/Git for Windows)
- merge non distruttivo: non tocca hook estranei gia' presenti

Rilanciabile piu' volte: se trova gia' un hook per questi script (riconosciuto
dal nome file in "args", non dalla stringa comando esatta) ne aggiorna la
definizione sul posto invece di duplicarla -- cosi' un aggiornamento futuro
si applica semplicemente ricopiando questa cartella e rilanciando lo script.

Parametro -InstallPython: salta il prompt S/n e installa direttamente se
manca (utile per lanci automatizzati/non interattivi).

[EN] Installs the Claude Code token usage dashboard on the current PC:
- checks for / offers to install python3 if missing (via winget, with
  confirmation)
- copies the hooks (pure Python) into ~/.claude/hooks
- registers the Stop/PostToolUse hooks in ~/.claude/settings.json in
  "exec form" (command+args, no shell -- bash/Git for Windows not needed)
- non-destructive merge: does not touch unrelated hooks already present

Re-runnable multiple times: if it already finds a hook for these scripts
(recognized by the file name in "args", not by the exact command string)
it updates its definition in place instead of duplicating it -- so a
future update is applied simply by copying this folder again and
re-running the script.

-InstallPython parameter: skips the S/n prompt and installs directly if
missing (useful for automated/non-interactive runs).
#>

param(
    [switch]$InstallPython
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hooksSrc  = Join-Path $scriptDir 'hooks'
$claudeDir = Join-Path $env:USERPROFILE '.claude'
$hooksDst  = Join-Path $claudeDir 'hooks'
$settingsPath = Join-Path $claudeDir 'settings.json'

Write-Host "== Installazione dashboard token usage per Claude Code ==" -ForegroundColor Cyan
Write-Host ""

# --- 1. Prerequisiti ---------------------------------------------------------
# Su Windows 11 senza Python installato, "python3" e' spesso comunque
# "trovato" sul PATH: e' l'alias di Microsoft Store sotto WindowsApps, che
# non esegue Python vero (apre lo Store). Ma il solo percorso non basta per
# distinguere i due casi: su alcune macchine quell'alias risolve comunque a
# un'installazione reale e funzionante (es. Python installato dallo Store
# stesso) -- verificato empiricamente, un controllo sul path da solo da'
# falsi negativi. L'unico modo affidabile e' provare a eseguirlo davvero.
# [EN] --- 1. Prerequisites ---
# [EN] On Windows 11 without Python installed, "python3" is often still
# [EN] "found" on the PATH: it is the Microsoft Store alias under
# [EN] WindowsApps, which does not run real Python (it opens the Store).
# [EN] But the path alone is not enough to tell the two cases apart: on
# [EN] some machines that alias still resolves to a real, working
# [EN] installation (e.g. Python installed from the Store itself) --
# [EN] verified empirically, a check on the path alone gives false
# [EN] negatives. The only reliable way is to actually try to run it.
$pythonOk = $false
try {
    $verOutput = & python3 --version 2>&1
    if ($LASTEXITCODE -eq 0 -and "$verOutput" -match 'Python 3') {
        $pythonOk = $true
    }
} catch {
    $pythonOk = $false
}

if (-not $pythonOk) {
    $cmd = Get-Command python3 -ErrorAction SilentlyContinue
    Write-Host "ATTENZIONE: python3 non risulta funzionante su questo PC." -ForegroundColor Yellow
    if ($cmd -and $cmd.Source -like '*\WindowsApps\*') {
        Write-Host "(trovato solo l'alias Microsoft Store in $($cmd.Source) -- non e' Python vero)" -ForegroundColor Yellow
    } elseif (-not $cmd) {
        Write-Host "(nessun python3 trovato sul PATH)" -ForegroundColor Yellow
    }
    Write-Host ""

    $reply = $null
    if ($InstallPython) {
        $reply = 'S'
    } elseif ([Environment]::UserInteractive -and -not ([Console]::IsInputRedirected)) {
        $reply = Read-Host "Vuoi installarlo ora via winget? (S/n)"
    }

    if ($reply -and $reply -notmatch '^[Nn]') {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "Installazione di Python 3.12 via winget in corso..." -ForegroundColor Cyan
            winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
            Write-Host "Fatto. Se lo script sotto non trova ancora python3, riapri il terminale (il PATH si aggiorna alla nuova sessione) e rilancia install.cmd." -ForegroundColor Green
        } else {
            Write-Host "winget non disponibile su questo PC. Installa Python da https://www.python.org/downloads/ (spunta 'Add python.exe to PATH') e rilancia questo script." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Ok, installa Python da https://www.python.org/downloads/ (spunta 'Add python.exe to PATH') e rilancia questo script." -ForegroundColor Yellow
    }
    Write-Host ""
}

# --- 2. Copia gli hook -------------------------------------------------------
# [EN] --- 2. Copy the hooks ---
New-Item -ItemType Directory -Force -Path $hooksDst | Out-Null
Copy-Item -Path (Join-Path $hooksSrc '*') -Destination $hooksDst -Recurse -Force
# generate_dashboard.py (file singolo) e' stato sostituito da generate_dashboard/
# (package): se un'installazione precedente l'ha lasciato sul PC, va tolto --
# altrimenti resterebbe un modulo vecchio e inerte accanto al package nuovo.
# [EN] generate_dashboard.py (single file) has been replaced by
# [EN] generate_dashboard/ (package): if a previous installation left it on
# [EN] the PC, it must be removed -- otherwise an old, inert module would
# [EN] remain next to the new package.
$staleFlatModule = Join-Path $hooksDst 'generate_dashboard.py'
if (Test-Path $staleFlatModule) {
    # Non fatale: il package generate_dashboard/ appena copiato ha comunque
    # la precedenza sul file piatto nell'import di Python (una directory con
    # __init__.py risolve prima di un modulo .py con lo stesso nome), quindi
    # anche se la pulizia fallisse (permessi, antivirus) l'installazione
    # resta funzionante.
    # [EN] Non-fatal: the just-copied generate_dashboard/ package takes
    # [EN] precedence over the flat file in Python's import anyway (a
    # [EN] directory with __init__.py resolves before a .py module with the
    # [EN] same name), so even if this cleanup failed (permissions,
    # [EN] antivirus) the installation remains functional.
    try {
        Remove-Item -Path $staleFlatModule -Force -ErrorAction Stop
    } catch {
        Write-Host "Nota: non sono riuscito a rimuovere il vecchio $staleFlatModule (non blocca l'installazione)." -ForegroundColor Yellow
    }
}
Write-Host "Hook copiati in: $hooksDst" -ForegroundColor Green

# --- 3. Merge di settings.json -----------------------------------------------
# [EN] --- 3. Merge settings.json ---
if (Test-Path $settingsPath) {
    $raw = Get-Content -Raw -Path $settingsPath -Encoding UTF8
    if ($raw.Trim().Length -eq 0) {
        $settings = [PSCustomObject]@{}
    } else {
        $settings = $raw | ConvertFrom-Json
    }
} else {
    $settings = [PSCustomObject]@{}
}

if (-not $settings.PSObject.Properties['hooks']) {
    $settings | Add-Member -MemberType NoteProperty -Name 'hooks' -Value ([PSCustomObject]@{})
}

$hooksDstUnix = $hooksDst -replace '\\', '/'

function Set-ExecHook {
    param(
        [Parameter(Mandatory)] $HooksRoot,
        [Parameter(Mandatory)] [string] $EventName,
        [Parameter(Mandatory)] [string] $ScriptPath,
        [Parameter(Mandatory)] [string] $ScriptFileName,
        [int] $Timeout = 15,
        [string] $Matcher
    )

    if (-not $HooksRoot.PSObject.Properties[$EventName]) {
        $HooksRoot | Add-Member -MemberType NoteProperty -Name $EventName -Value @()
    }

    $groups = @($HooksRoot.$EventName)

    # Riconosce un hook gia' registrato per questo script dal nome file in
    # "args" (non dalla stringa comando esatta, che cambia da una versione
    # all'altra): se trovato lo aggiorna sul posto invece di duplicarlo.
    # [EN] Recognizes a hook already registered for this script by the file
    # [EN] name in "args" (not by the exact command string, which changes
    # [EN] from one version to the next): if found, it updates it in place
    # [EN] instead of duplicating it.
    foreach ($g in $groups) {
        foreach ($h in @($g.hooks)) {
            $hArgs = @($h.args)
            if ($hArgs -and ($hArgs | Where-Object { $_ -like "*$ScriptFileName" })) {
                $h.command = 'python3'
                $h.args = @($ScriptPath)
                $h.timeout = $Timeout
                return
            }
        }
    }

    $newHook  = [PSCustomObject]@{ type = 'command'; command = 'python3'; args = @($ScriptPath); timeout = $Timeout }
    $newGroup = [PSCustomObject]@{ hooks = @($newHook) }
    if ($Matcher) {
        $newGroup | Add-Member -MemberType NoteProperty -Name 'matcher' -Value $Matcher
    }
    $HooksRoot.$EventName = $groups + $newGroup
}

Set-ExecHook -HooksRoot $settings.hooks -EventName 'Stop' `
    -ScriptPath "$hooksDstUnix/log_tokens.py" -ScriptFileName 'log_tokens.py' -Timeout 15
Set-ExecHook -HooksRoot $settings.hooks -EventName 'PostToolUse' `
    -ScriptPath "$hooksDstUnix/log_operation.py" -ScriptFileName 'log_operation.py' -Timeout 15 -Matcher '.*'

$json = $settings | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($settingsPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Hook registrati in: $settingsPath" -ForegroundColor Green

# --- 4. Riepilogo -------------------------------------------------------------
# [EN] --- 4. Summary ---
$dashboardPath = Join-Path $claudeDir 'dashboard-token\dashboard.html'
Write-Host ""
Write-Host "Fatto." -ForegroundColor Cyan
Write-Host "Riavvia Claude Code se era gia' aperto (gli hook si applicano dalla"
Write-Host "prossima sessione). Alla fine del primo turno successivo verra' generata"
Write-Host "la tua dashboard personale in:"
Write-Host "  $dashboardPath" -ForegroundColor White
Write-Host ""
Write-Host "Personalizzazioni facoltative (create in $hooksDst):"
Write-Host "  - dashboard_config.json  { ""out_dir"": ""C:\...\cartella-a-piacere"" }"
Write-Host "  - account_labels.json    { ""<uuid-account>"": ""etichetta leggibile"" }"
