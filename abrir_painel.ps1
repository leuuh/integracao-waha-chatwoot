# Launcher - Abre o Painel de Integração no Chrome (sem CORS)
$dashPath = "$PSScriptRoot\dashboard.html"
$fileUrl  = "file:///" + $dashPath.Replace("\", "/")

# Caminhos comuns do Chrome
$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)

$chrome = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $chrome) {
    Write-Host "[!] Chrome nao encontrado. Tentando Edge..." -ForegroundColor Yellow
    $edgePaths = @(
        "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
    )
    $chrome = $edgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $chrome) {
        Write-Host "[!] Nenhum browser encontrado. Abra manualmente:" -ForegroundColor Red
        Write-Host $fileUrl
        pause; exit 1
    }
    $profileDir = "$env:TEMP\WahaCwEdgeProfile"
    $args = @("--disable-web-security", "--user-data-dir=$profileDir", $fileUrl)
} else {
    $profileDir = "$env:TEMP\WahaCwChromeProfile"
    $args = @("--disable-web-security", "--user-data-dir=$profileDir", $fileUrl)
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  WAHA <-> Chatwoot  Painel de Integração" -ForegroundColor Cyan
Write-Host "=========================================== ======" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Abrindo browser com CORS desabilitado..." -ForegroundColor Green
Write-Host "[*] Use esta janela SOMENTE para o painel!" -ForegroundColor Yellow
Write-Host ""

Start-Process $chrome -ArgumentList $args
