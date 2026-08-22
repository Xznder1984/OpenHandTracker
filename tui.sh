#!/usr/bin/env bash
# OpenHandTrack — interactive installer & example launcher (macOS / Linux).
#
# Run it without cloning anything:
#   curl -fsSL https://raw.githubusercontent.com/Xznder1984/OpenHandTracker/main/tui.sh | bash
#
# Windows users: use tui.ps1 instead.
#   irm https://raw.githubusercontent.com/Xznder1984/OpenHandTracker/main/tui.ps1 | iex

set -euo pipefail

REPO_URL="https://github.com/Xznder1984/OpenHandTracker.git"
DIR="${OHT_DIR:-$HOME/OpenHandTracker}"

if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; CYAN=$'\033[36m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; RED=$'\033[31m'; OFF=$'\033[0m'
else
  BOLD=""; DIM=""; CYAN=""; GREEN=""; YELLOW=""; RED=""; OFF=""
fi

info() { printf '%s\n' "${CYAN}==>${OFF} $*"; }
ok()   { printf '%s\n' "${GREEN} ✔ ${OFF}$*"; }
warn() { printf '%s\n' "${YELLOW} !! ${OFF}$*"; }
die()  { printf '%s\n' "${RED} ✖ ${OFF}$*" >&2; exit 1; }

banner() {
  printf '%s\n' "${CYAN}${BOLD}"
  cat <<'BANNER'

  ___                   _   _                 _ _____               _
 / _ \ _ __   ___ _ __ | | | | __ _ _ __   __| |_   _| __ __ _  ___| | __
| | | | '_ \ / _ \ '_ \| |_| |/ _` | '_ \ / _` | | || '__/ _` |/ __| |/ /
| |_| | |_) |  __/ | | |  _  | (_| | | | | (_| | | || | | (_| | (__|   <
 \___/| .__/ \___|_| |_|_| |_|\__,_|_| |_|\__,_| |_||_|  \__,_|\___|_|\_\
      |_|          real-time hand tracking — wave at your webcam

BANNER
  printf '%s' "$OFF"
}

# ---------------------------------------------------------------------------
# 1. Find a Python that MediaPipe can actually install on (3.11 or 3.12)
# ---------------------------------------------------------------------------
python_ok() { # no stdin use: the whole script may be running from `curl | bash`
  "$1" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 13) else 1)' >/dev/null 2>&1
}

PY=""
for candidate in python3.12 python3.11 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && python_ok "$candidate"; then
    PY="$candidate"
    break
  fi
done

[ -n "$PY" ] || die "No Python 3.11/3.12 found.
    MediaPipe only ships wheels for Python 3.11-3.12.
    macOS:   brew install python@3.12
    Debian:  sudo apt install python3.12 python3.12-venv
    Fedora:  sudo dnf install python3.12"

info "Using $($PY --version) ($($PY -c 'import sys; print(sys.executable)'))"

command -v git >/dev/null 2>&1 || die "git is required.
    macOS:   brew install git     (or: xcode-select --install)
    Linux:   sudo apt install git"

# ---------------------------------------------------------------------------
# 2. Get the code
# ---------------------------------------------------------------------------
if [ -d "$DIR/.git" ]; then
  info "Updating existing checkout at $DIR"
  git -C "$DIR" pull --ff-only -q || warn "could not update (offline?) — using existing checkout"
else
  info "Cloning into $DIR"
  git clone --depth 1 -q "$REPO_URL" "$DIR" || die "git clone failed"
fi
cd "$DIR"

# ---------------------------------------------------------------------------
# 3. Virtualenv + dependencies (idempotent; fast when already satisfied)
# ---------------------------------------------------------------------------
VPY="$DIR/.venv/bin/python"
if [ ! -x "$VPY" ]; then
  info "Creating virtualenv (.venv)"
  "$PY" -m venv .venv || die "could not create a virtualenv"
fi

info "Installing openhandtrack + example deps ${DIM}(first run downloads ~100 MB)${OFF}"
"$VPY" -m pip install --quiet --upgrade pip
# NOT --quiet: this step can take minutes on the first run and users deserve
# a progress bar instead of a frozen terminal.
"$VPY" -m pip install -e "$DIR/python[examples]" \
  || die "pip install failed — see output above"

ok "Ready."

# ---------------------------------------------------------------------------
# 4. Menu
# ---------------------------------------------------------------------------
EXAMPLES=(
  "air_draw|Air Draw|pinch to draw in the air, palette + eraser built in"
  "finger_count|Finger Counter|counts extended fingers with tip markers"
  "peace_selfie|Peace Selfie|hold ✌ for a countdown photo"
  "virtual_mouse|Virtual Mouse|index finger steers the cursor, pinch to click"
  "air_scroll|Air Scroll|point up/down to scroll, fist locks position"
  "pinch_ruler|Pinch Ruler|live thumb↔index distance meter"
  "two_hand_zoom|Two-Hand Zoom|spread/squeeze both hands to zoom"
  "volume_control|Volume Control|pinch and drag to set system volume"
  "presentation_remote|Presentation Remote|swipe to change slides, fist to blank"
)

pause() {
  printf '%s' "${DIM}press Enter to continue...${OFF}"
  read -r < /dev/tty || true
}

while true; do
  banner
  printf '%s\n' "  ${BOLD}Examples${OFF}  ${DIM}(repo: $DIR)${OFF}"
  i=1
  for row in "${EXAMPLES[@]}"; do
    IFS='|' read -r slug title desc <<< "$row"
    printf '   %s%d%s) %-20s %s%s%s\n' "$GREEN" "$i" "$OFF" "$title" "$DIM" "$desc" "$OFF"
    i=$((i + 1))
  done
  printf '   %sq%s) Quit\n\n' "$GREEN" "$OFF"
  printf '%s' "  choose: "

  choice=""
  read -r choice < /dev/tty || exit 0

  if [ "$choice" = "q" ] || [ "$choice" = "Q" ]; then
    ok "bye — rerun anytime with the same curl command"
    exit 0
  fi

  case "$choice" in
  [1-9])
    row="${EXAMPLES[$((choice - 1))]}"
    IFS='|' read -r slug title desc <<< "$row"
    printf '\n%s\n' "${BOLD}── $title ──${OFF} ${DIM}(Ctrl+C to stop)${OFF}\n"
    "$VPY" "python/examples/$slug/$slug.py" || warn "example exited with an error (webcam permission? another app using the camera?)"
    pause
    ;;
  *)
    warn "unknown option: $choice"
    ;;
  esac
done
