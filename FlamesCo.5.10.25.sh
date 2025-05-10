#!/bin/bash

# Define colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print a banner
print_banner() {
    echo -e "${GREEN}=====================================================${NC}"
    echo -e "${GREEN} $1 ${NC}"
    echo -e "${GREEN}=====================================================${NC}"
}

# ---------------------------------------------------------------------------
# DevkitPro — ALL the Nintendo toolchains & libs (and more!)
# ---------------------------------------------------------------------------
print_banner "DevkitPro (ALL supported consoles)"

echo -e "${CYAN}Installing DevkitPro pacman & a whole bunch of meta-packages, meow...${NC}"

# Bootstrap DevkitPro’s pacman (same one-liner from the docs)
# Using -fsSL for curl: fail silently on server errors, show error on client errors, follow redirects.
if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://apt.devkitpro.org/install-devkitpro-pacman | sudo bash || {
        echo -e "${RED}DevkitPro bootstrap failed! Oh noes! Skipping Nintendo (and other) toolchains. Sad meow.${NC}"
        exit 1 # Exit if bootstrap fails as dkp-pacman is essential
    }
else
    echo -e "${RED}curl is not installed! Halp! Cannot bootstrap DevkitPro. Sad kitty...${NC}"
    exit 1
fi

# Ensure the environment is live before calling dkp-pacman
# This is important for the current session if dkp-pacman was just installed.
if [ -f /etc/profile.d/devkit-env.sh ]; then
    source /etc/profile.d/devkit-env.sh
else
    echo -e "${YELLOW}Warning: DevkitPro environment script not found. This might be okay if it's already in PATH.${NC}"
fi

# Check if dkp-pacman is available
if ! command -v dkp-pacman >/dev/null 2>&1; then
    echo -e "${RED}dkp-pacman command not found after installation attempt! Something is fishy! Try running 'source /etc/profile.d/devkit-env.sh' or check installation. Purr...plexing!${NC}"
    exit 1
fi

echo -e "${CYAN}Updating DevkitPro package database, purr...${NC}"
# Update DevkitPro package database
dkp-pacman -Sy --noconfirm || {
    echo -e "${YELLOW}dkp-pacman -Sy failed to sync all databases, but we'll try to install packages anyway! Stay paw-sitive!${NC}"
}

echo -e "${CYAN}Installing **all** known DevkitPro meta-packages! This might take a while, like a long cat nap!${NC}"
# The '|| true' at the end ensures the script continues even if some packages are not found
# (e.g., for deprecated consoles or those not currently hosted in main repos).
# Package list reordered chronologically by approximate platform release.
dkp-pacman -S --noconfirm \
    gp32-dev \
    gba-dev \
    gamecube-dev \
    nds-dev \
    psp-dev \
    wii-dev \
    3ds-dev \
    wiiu-dev \
    switch-dev \
    || true

echo -e "${GREEN}✔ Purrfect! DevkitPro toolchains & libs installed (as many as the repo provides, nya!).${NC}"
echo -e "${YELLOW}If any packages failed to install, they’re probably for very old or unsupported consoles, meow! The rest should be ready to roll like a ball of yarn!${NC}"
echo -e "${CYAN}Remember to source your environment if it's a new shell: source /etc/profile.d/devkit-env.sh${NC}"
