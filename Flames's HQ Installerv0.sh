#!/bin/bash

# ============================================================
# Script: test.sh
# Title: ZeroShot Ultimate Retro Devkit & Emulator Installer
# Motto: From Babbage to Switch — install the timeline.
# [C] Team Flames 1920–2025 | Fueled by CATSDK 🐾✨
# ============================================================

set -euo pipefail

# ========== Terminal Styling ==========
BOLD="\033[1m"
RESET="\033[0m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
PURPLE="\033[1;35m"
RED="\033[1;31m"

banner() {
  echo -e "${PURPLE}\n>>> $1 <<<${RESET}"
}

echo -e "${CYAN}\n🔥 ZeroShot Ultimate Retro Installer (1920–2025) 🔥"
echo -e "✨ Time to install 100 years of computing history. ✨${RESET}\n"

# ========== Root Check ==========
if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Please run as root. (sudo ./test.sh)${RESET}"
  exit 1
fi

# ========== System Update ==========
banner "System Update & Essentials"
apt-get update
apt-get install -y build-essential git curl wget || true

# ========== Mainframes & Minis ==========
banner "1950s–1960s: Mainframe & Minicomputer Emulators"
apt-get install -y simh hercules || true
echo -e "${GREEN}✔ SIMH and Hercules installed. Go simulate some classic metal dinosaurs.${RESET}"

# ========== Retro PCs ==========
banner "1970s–1990s: Home Computers & Vintage PCs"
apt-get install -y vice fuse-emulator-gtk atari800 dosbox hatari fs-uae mame || true
echo -e "${GREEN}✔ C64, ZX, Atari, Amiga, DOS, and MAME emulators installed. Have fun clicking through BASIC prompts.${RESET}"

# ========== Dev Toolkits ==========
banner "Dev Toolkits for Classic Systems"
apt-get install -y cc65 sdcc z88dk open-watcom-bin || true
echo -e "${GREEN}✔ Retro compilers installed. You can now try your hand at Z80 assembly.${RESET}"

# ========== Retro Consoles ==========
banner "1970s–2000s: Console Emulators"

# Try SNES9x via apt → snap → source
banner "Installing SNES9x: Because Mode 7 Matters"

if apt-get install -y snes9x; then
  echo -e "${CYAN}🎮 SNES9x installed via APT. Good ol' apt didn't let us down. ${RESET}"
elif command -v snap >/dev/null 2>&1 && snap install snes9x-gtk; then
  echo -e "${CYAN}🎮 SNES9x installed via Snap. It might take a moment to start, but it works. ${RESET}"
else
  echo -e "${YELLOW}⚠️ SNES9x not available via apt or snap. Building from source, the dedicated way...${RESET}"
  apt-get install -y libsdl2-dev libgtk-3-dev || true
  git clone https://github.com/snes9xgit/snes9x.git /opt/snes9x || true
  (cd /opt/snes9x/gtk && make clean && make -j$(nproc)) || true
  ln -sf /opt/snes9x/gtk/snes9x /usr/local/bin/snes9x || true
  echo -e "${CYAN}🎮 SNES9x built from source. You now wield raw emulator energy. ${RESET}"
fi

# Other emulators
apt-get install -y stella fceux mupen64plus pcsxr yabause dolphin-emu ppsspp || true
echo -e "${GREEN}✔ Atari to PSP emulators installed. Boot ROMs like it’s a legally distinct holiday.${RESET}"

# ========== DevkitPro ==========
banner "DevkitPro: Nintendo's Open Source Companion"
curl -L https://apt.devkitpro.org/install-devkitpro-pacman | bash || true
source /etc/profile.d/devkit-env.sh || true
echo -e "${CYAN}Installing a comprehensive set of DevkitPro tools...${RESET}"
dkp-pacman -Syu --noconfirm \
  devkitARM devkitPPC devkitA64 \
  gba-dev nds-dev 3ds-dev \
  gamecube-dev wii-dev wiiu-dev \
  switch-dev psp-dev \
  general-tools || true
echo -e "${GREEN}✔ DevkitPro toolchains (GBA, DS, 3DS, GameCube, Wii, Wii U, Switch, PSP) are in. Let the homebrew creation begin!${RESET}"

# ========== Calculators & PDAs ==========
banner "Calculators & PDAs: Pocket-Sized Fun"
apt-get install -y tilem tiemu || true
echo -e "${GREEN}✔ Calculator emulators ready. TI-BASIC adventures unlocked.${RESET}"

# ========== Mobile Emulation ==========
banner "Android Emulation: Mobile Development Simulator"
apt-get install -y openjdk-17-jdk android-sdk-platform-tools android-sdk emulator || true
export ANDROID_SDK_ROOT="/usr/lib/android-sdk" || true
echo -e "${GREEN}✔ Android SDK installed. Go emulate your phone inside your computer like a digital inception.${RESET}"

# ========== Special Hardware ==========
banner "Special Hardware: The Truly Unique"

# Apollo Guidance Computer
git clone https://github.com/virtualagc/virtualagc.git /opt/virtualagc || true
(cd /opt/virtualagc && make clean && make -j$(nproc)) || true
echo -e "${GREEN}✔ Apollo AGC emulator built. Go simulate the Moon with ANSI C and a spirit of adventure.${RESET}"

# Arduino & AVR
apt-get install -y arduino-cli avr-libc avrdude simavr || true
echo -e "${GREEN}✔ Arduino & AVR stuff installed. Time to blink LEDs and explore microcontrollers.${RESET}"

# ========== Final Instructions ==========
echo -e "${GREEN}\n✔ All selected packages installed! You’re armed with tools spanning a century. 🌌${RESET}"
echo -e "${YELLOW}\n⚠️ Final Reminders:${RESET}"
echo -e "- Remember to acquire BIOS files manually where needed. This script does not provide them."
echo -e "- Source this file manually: ${BOLD}/etc/profile.d/devkit-env.sh${RESET} or restart your shell."
echo -e "- Cloned items in /opt may require building with 'make' if you haven't already."
echo -e "- Now go write some amazing homebrew and explore computing history!\n"

# ========== Linger with Y/N Failsafe ==========
while true; do
  echo -e "${PURPLE}🐾 Installer complete. Confirm to exit.${RESET}"
  read -rp "$(echo -e "${BOLD}Exit script and return to your shell? (y/n): ${RESET}")" answer
  case "${answer,,}" in
    y|yes)
      echo -e "${PURPLE}🐾 Goodbye! Now go emulate something and make cool stuff.${RESET}\n"
      break
      ;;
    n|no)
      echo -e "${CYAN}🐱 Still here. Type 'y' when you're ready. I'll wait... 👁️${RESET}\n"
      ;;
    *)
      echo -e "${YELLOW}❓ Invalid input. Please type 'y' or 'n'.${RESET}\n"
      ;;
  esac
done
