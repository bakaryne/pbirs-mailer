$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

function Stop-Setup {
    param([string]$Message)

    Write-Host ""
    Write-Host "ERREUR : $Message" -ForegroundColor Red
    exit 1
}

Write-Host "PBIRS Mailer - Installation" -ForegroundColor Cyan
Write-Host ""

$PythonExecutable = $null
$PythonPrefix = @()
$Version = $null
$PythonCandidates = @()

foreach ($CommandName in @("python.exe", "python3.exe")) {
    $PythonCommand = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($null -ne $PythonCommand) {
        $PythonCandidates += [PSCustomObject]@{
            Executable = $PythonCommand.Source
            Prefix = @()
        }
    }
}

$PyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
if ($null -ne $PyLauncher) {
    $PythonCandidates += [PSCustomObject]@{
        Executable = $PyLauncher.Source
        Prefix = @("-3")
    }
}

foreach ($Candidate in $PythonCandidates) {
    $CandidateExecutable = $Candidate.Executable
    $CandidatePrefix = @($Candidate.Prefix)
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $CandidateResult = [string](& $CandidateExecutable @CandidatePrefix -c "import sys; print('{}|{}'.format('.'.join(map(str, sys.version_info[:3])), int(sys.version_info >= (3, 10))))" 2>$null)
        $CandidateExitCode = $LASTEXITCODE
    }
    catch {
        $CandidateResult = ""
        $CandidateExitCode = 1
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }

    if ($CandidateExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($CandidateResult)) {
        continue
    }

    $CandidateParts = $CandidateResult.Trim().Split("|")
    if ($CandidateParts.Count -eq 2 -and $CandidateParts[1] -eq "1") {
        $PythonExecutable = $Candidate.Executable
        $PythonPrefix = @($Candidate.Prefix)
        $Version = $CandidateParts[0]
        break
    }
}

if ($null -eq $PythonExecutable) {
    Stop-Setup "Aucun Python compatible n'a ete trouve. Installez Python 3.10 ou plus recent."
}

Write-Host "[OK] Python $Version"

$VenvDirectory = Join-Path $PSScriptRoot ".venv"
$VenvPython = Join-Path $VenvDirectory "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "[1/3] Creation de l'environnement Python isole..."
    & $PythonExecutable @PythonPrefix -m venv $VenvDirectory
    if ($LASTEXITCODE -ne 0) {
        Stop-Setup "La creation de .venv a echoue."
    }
}
else {
    $VenvIsSupported = & $VenvPython -c "import sys; print('yes' if sys.version_info >= (3, 10) else 'no')" 2>$null
    if ($LASTEXITCODE -ne 0 -or $VenvIsSupported.Trim() -ne "yes") {
        Write-Host "[1/3] Ancien environnement incompatible : recreation..."
        Remove-Item -LiteralPath $VenvDirectory -Recurse -Force
        & $PythonExecutable @PythonPrefix -m venv $VenvDirectory
        if ($LASTEXITCODE -ne 0) {
            Stop-Setup "La recreation de .venv a echoue."
        }
    }
    else {
        Write-Host "[1/3] Environnement Python deja present."
    }
}

Write-Host "[2/3] Installation de PBIRS Mailer et Playwright..."
& $VenvPython -m pip install --disable-pip-version-check .
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "L'installation Python a echoue. Consultez les messages pip affiches ci-dessus."
}

$ConfigPath = Join-Path $PSScriptRoot "config.json"
$ExampleConfigPath = Join-Path $PSScriptRoot "config.example.json"
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Copy-Item -LiteralPath $ExampleConfigPath -Destination $ConfigPath
    Write-Host "[3/3] config.json cree a partir de l'exemple."
}
else {
    Write-Host "[3/3] config.json conserve sans modification."
}

$EdgeCandidates = @()
if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
    $EdgeCandidates += Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"
}
if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
    $EdgeCandidates += Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"
}

$EdgeFound = $false
foreach ($Candidate in $EdgeCandidates) {
    if (Test-Path -LiteralPath $Candidate) {
        $EdgeFound = $true
        break
    }
}

if ($EdgeFound) {
    Write-Host "[OK] Microsoft Edge detecte."
}
else {
    Write-Warning "Microsoft Edge n'a pas ete detecte. Installez Edge avant la premiere capture."
}

Write-Host ""
Write-Host "Verification de la configuration..."
& $VenvPython main.py --config $ConfigPath --dry-run
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "La verification de config.json a echoue."
}

Write-Host ""
Write-Host "Installation terminee." -ForegroundColor Green
Write-Host "1. Modifiez config.json."
Write-Host "2. Testez avec : .\run.cmd --dry-run"
Write-Host "3. Capturez sans email et sans afficher Edge : .\run.cmd --no-send --verbose"
Write-Host "   Diagnostic visuel uniquement : ajoutez --headed"
