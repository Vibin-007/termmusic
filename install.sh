#!/usr/bin/env bash
# TermTune One-Line Installer Script for Linux & macOS
set -e

BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}"
echo "  🎵 Installing TermTune (termmusic)..."
echo "  ======================================"
echo -e "${RESET}"

# 1. Check Python version
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✕ Python 3 is not installed. Please install Python 3.11+ first.${RESET}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e " Found Python ${GREEN}v${PYTHON_VERSION}${RESET}"

# 2. Check mpv dependency
if ! command -v mpv &>/dev/null; then
    echo -e "${YELLOW}⚠️ 'mpv' audio engine was not found on your system.${RESET}"
    if command -v apt &>/dev/null; then
        echo -e "${CYAN}Installing mpv via apt...${RESET}"
        sudo apt update && sudo apt install -y mpv
    elif command -v brew &>/dev/null; then
        echo -e "${CYAN}Installing mpv via Homebrew...${RESET}"
        brew install mpv
    elif command -v dnf &>/dev/null; then
        echo -e "${CYAN}Installing mpv via dnf...${RESET}"
        sudo dnf install -y mpv
    elif command -v pacman &>/dev/null; then
        echo -e "${CYAN}Installing mpv via pacman...${RESET}"
        sudo pacman -S --noconfirm mpv
    else
        echo -e "${RED}Please install 'mpv' using your system package manager.${RESET}"
    fi
else
    echo -e " Found ${GREEN}mpv${RESET} audio engine"
fi

# 3. Install TermTune via pip / pipx
echo -e "${CYAN}Installing termtune Python package...${RESET}"

if command -v pipx &>/dev/null; then
    pipx install git+https://github.com/Vibin-007/termmusic.git --force
else
    python3 -m pip install --break-system-packages --user --upgrade git+https://github.com/Vibin-007/termmusic.git 2>/dev/null || \
    python3 -m pip install --user --upgrade git+https://github.com/Vibin-007/termmusic.git
fi

# 4. Ensure ~/.local/bin is in PATH
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo -e "${YELLOW}Adding $LOCAL_BIN to your PATH environment...${RESET}"
    SHELL_NAME=$(basename "$SHELL")
    if [[ "$SHELL_NAME" == "zsh" ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    else
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}🎉 TermTune successfully installed!${RESET}"
echo -e "${CYAN}Run ${BOLD}termtune${RESET}${CYAN} in your terminal to start listening to music.${RESET}"
echo ""
