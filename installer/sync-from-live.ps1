#requires -Version 5.1
<#
Ricopia i canonici da ~/.claude/hooks/ (dove li modifichi e testi dal vivo) a
questa cartella installer/hooks/ (quella da cui la CI costruisce i binari).
Lancialo dopo ogni modifica al package generate_dashboard/, log_tokens.py o
log_operation.py, prima di committare.

Copia SOLO una whitelist esplicita: i due hook, i .py alla radice del
package e i template .html. La cartella live contiene anche configurazione
e dati locali (dashboard_config.json, account_labels.json), che non fanno
parte del progetto.

[EN] Copies the canonical files back from ~/.claude/hooks/ (where you edit
and test them live) to this installer/hooks/ folder (the one the CI builds
the binaries from). Run it after every change to the generate_dashboard/
package, log_tokens.py or log_operation.py, before committing.

It copies ONLY an explicit whitelist: the two hooks, the .py files at the
package root and the .html templates. The live folder also holds local
configuration and data (dashboard_config.json, account_labels.json), which
are not part of the project.
#>

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hooksDst  = Join-Path $scriptDir 'hooks'
$hooksSrc  = Join-Path $env:USERPROFILE '.claude\hooks'

$files = @('log_tokens.py', 'log_operation.py')

foreach ($f in $files) {
    $src = Join-Path $hooksSrc $f
    if (-not (Test-Path $src)) {
        Write-Host "ATTENZIONE: $src non trovato, saltato." -ForegroundColor Yellow
        continue
    }
    Copy-Item -Path $src -Destination (Join-Path $hooksDst $f) -Force
    Write-Host "Sincronizzato: $f" -ForegroundColor Green
}

$pkgSrc = Join-Path $hooksSrc 'generate_dashboard'
$pkgDst = Join-Path $hooksDst 'generate_dashboard'
if (Test-Path $pkgSrc) {
    if (Test-Path $pkgDst) {
        Remove-Item -Path $pkgDst -Recurse -Force
    }
    # Whitelist: solo i sorgenti. Niente copia ricorsiva integrale, cosi'
    # la configurazione e i dati locali restano fuori dal pacchetto.
    # [EN] Whitelist: sources only. No full recursive copy, so local
    # [EN] configuration and data stay out of the package.
    New-Item -ItemType Directory -Path (Join-Path $pkgDst 'templates') -Force | Out-Null
    Get-ChildItem -Path $pkgSrc -Filter '*.py' -File |
        Copy-Item -Destination $pkgDst -Force
    Get-ChildItem -Path (Join-Path $pkgSrc 'templates') -Filter '*.html' -File |
        Copy-Item -Destination (Join-Path $pkgDst 'templates') -Force
    Write-Host "Sincronizzato: generate_dashboard/ (solo *.py e templates/*.html)" -ForegroundColor Green
} else {
    Write-Host "ATTENZIONE: $pkgSrc non trovato, saltato." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Fatto. Ricorda: questo aggiorna solo installer/hooks/ in locale."
Write-Host "Committa le modifiche: la CI costruisce i binari e pubblica la release."
