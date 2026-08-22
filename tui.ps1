# OpenHandTrack — interactive installer & example launcher (Windows).
#
# Run it without cloning anything (PowerShell):
#   irm https://raw.githubusercontent.com/Xznder1984/OpenHandTracker/main/tui.ps1 | iex
#
# macOS / Linux users: use tui.sh instead.
#   curl -fsSL https://raw.githubusercontent.com/Xznder1984/OpenHandTracker/main/tui.sh | bash

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Xznder1984/OpenHandTracker.git"
$Dir = if ($env:OHT_DIR) { $env:OHT_DIR } else { Join-Path $HOME "OpenHandTracker" }

function Write-Info($msg) { Write-Host "==>" -ForegroundColor Cyan -NoNewline; Write-Host " $msg" }
function Write-Ok($msg)   { Write-Host " ok " -ForegroundColor Green -NoNewline; Write-Host " $msg" }
function Write-Warn2($msg){ Write-Host " !! " -ForegroundColor Yellow -NoNewline; Write-Host " $msg" }
function Die($msg) {
    Write-Host " ✖ " -ForegroundColor Red -NoNewline; Write-Host "$msg" -ForegroundColor Red
    if ($host.Name -eq "ConsoleHost") { Read-Host "press Enter to close" | Out-Null }
    exit 1
}

function Show-Banner {
    Write-Host ""
    Write-Host "  ___                   _   _                 _ _____               _" -ForegroundColor Cyan
    Write-Host " / _ \ _ __   ___ _ __ | | | | __ _ _ __   __| |_   _| __ __ _  ___| | __" -ForegroundColor Cyan
    Write-Host "| | | | '_ \ / _ \ '_ \| |_| |/ _`` | '_ \ / _`` | | || '__/ _`` |/ __| |/ /" -ForegroundColor Cyan
    Write-Host "| |_| | |_) |  __/ | | |  _  | (_| | | | | (_| | | || | | (_| | (__|   <" -ForegroundColor Cyan
    Write-Host " \___/| .__/ \___|_| |_|_| |_|\__,_|_| |_|\__,_| |_||_|  \__,_|\___|_|\_\" -ForegroundColor Cyan
    Write-Host "      |_|          real-time hand tracking - wave at your webcam" -ForegroundColor DarkGray
    Write-Host ""
}

# ---------------------------------------------------------------------------
# 1. Find a Python that MediaPipe can actually install on (3.11 or 3.12)
# ---------------------------------------------------------------------------
$Check = 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,13) else 1)'
$Py = $null

foreach ($candidate in @("py -3.12", "py -3.11", "python", "python3")) {
    $parts = $candidate.Split(" ")
    $cmd = Get-Command $parts[0] -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    # "py -3.12" style: extra args after the executable
    $extra = if ($parts.Count -gt 1) { $parts[1..($parts.Count - 1)] } else { @() }
    & $parts[0] @extra -c $Check *>$null
    if ($LASTEXITCODE -eq 0) { $Py = @{ exe = $parts[0]; args = $extra }; break }
}

if (-not $Py) {
    Die @"
No Python 3.11/3.12 found.
MediaPipe only ships wheels for Python 3.11-3.12.
Install it from https://www.python.org/downloads/ (tick 'Add to PATH'),
or: winget install Python.Python.3.12
"@
}

$ver = & $Py.exe @($Py.args) --version 2>&1
Write-Info "Using $ver"

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Die @"
git is required. Install it from https://git-scm.com/download/win
or: winget install Git.Git
"@
}

# ---------------------------------------------------------------------------
# 2. Get the code
# ---------------------------------------------------------------------------
if (Test-Path (Join-Path $Dir ".git")) {
    Write-Info "Updating existing checkout at $Dir"
    Push-Location $Dir
    git pull --ff-only -q 2>$null
    if (-not $?) { Write-Warn2 "could not update (offline?) - using existing checkout" }
    Pop-Location
} else {
    Write-Info "Cloning into $Dir"
    git clone --depth 1 -q $RepoUrl $Dir
    if (-not $?) { Die "git clone failed" }
}
Set-Location $Dir

# ---------------------------------------------------------------------------
# 3. Virtualenv + dependencies (idempotent; fast when already satisfied)
# ---------------------------------------------------------------------------
$VEnv = Join-Path $Dir ".venv"
$VPy = Join-Path $VEnv "Scripts\python.exe"
if (-not (Test-Path $VPy)) {
    Write-Info "Creating virtualenv (.venv)"
    & $Py.exe @($Py.args) -m venv $VEnv
    if (-not $?) { Die "could not create a virtualenv" }
}

Write-Info "Installing openhandtrack + example deps (first run downloads ~100 MB)"
& $VPy -m pip install --quiet --upgrade pip
if (-not $?) { Die "pip upgrade failed - see output above" }
& $VPy -m pip install --quiet -e "$Dir\python[examples]"
if (-not $?) { Die "pip install failed - see output above" }
Write-Ok "Ready."

# ---------------------------------------------------------------------------
# 4. Menu
# ---------------------------------------------------------------------------
$Examples = @(
    @{ slug = "air_draw";             title = "Air Draw";              desc = "pinch to draw in the air, palette + eraser built in" },
    @{ slug = "finger_count";         title = "Finger Counter";        desc = "counts extended fingers with tip markers" },
    @{ slug = "peace_selfie";         title = "Peace Selfie";          desc = "hold V-sign for a countdown photo" },
    @{ slug = "virtual_mouse";        title = "Virtual Mouse";         desc = "index finger steers the cursor, pinch to click" },
    @{ slug = "air_scroll";           title = "Air Scroll";            desc = "point up/down to scroll, fist locks position" },
    @{ slug = "pinch_ruler";          title = "Pinch Ruler";           desc = "live thumb-index distance meter" },
    @{ slug = "two_hand_zoom";        title = "Two-Hand Zoom";         desc = "spread/squeeze both hands to zoom" },
    @{ slug = "volume_control";       title = "Volume Control";        desc = "pinch and drag to set system volume" },
    @{ slug = "presentation_remote";  title = "Presentation Remote";   desc = "swipe to change slides, fist to blank" }
)

function Pause-Enter {
    Read-Host "press Enter to continue" | Out-Null
}

while ($true) {
    Show-Banner
    Write-Host "  Examples  ($Dir)" -ForegroundColor White
    for ($i = 0; $i -lt $Examples.Count; $i++) {
        $e = $Examples[$i]
        Write-Host ("   {0}) " -f ($i + 1)) -ForegroundColor Green -NoNewline
        Write-Host ("{0,-20}" -f $e.title) -NoNewline
        Write-Host $e.desc -ForegroundColor DarkGray
    }
    Write-Host "   q) Quit" -ForegroundColor Green
    Write-Host ""

    $choice = Read-Host "  choose"

    if ($choice -eq "q" -or $choice -eq "Q") {
        Write-Ok "bye - rerun anytime with the same command"
        break
    }

    $index = 0
    if ([int]::TryParse($choice, [ref]$index) -and $index -ge 1 -and $index -le $Examples.Count) {
        $e = $Examples[$index - 1]
        $script = Join-Path $Dir "python\examples\$($e.slug)\$($e.slug).py"
        Write-Host ""
        Write-Host "-- $($e.title) -- (Ctrl+C to stop)" -ForegroundColor White
        Write-Host ""
        & $VPy $script
        if (-not $?) { Write-Warn2 "example exited with an error (webcam permission? another app using the camera?)" }
        Pause-Enter
    } else {
        Write-Warn2 "unknown option: $choice"
    }
}
