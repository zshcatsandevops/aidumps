#!/usr/bin/env bash
# 🚀 Ultimate Retro Emulator & SDK Installation Script – “test.sh”
# Covers everything from ENIAC mainframes to Nintendo Switch.
# Tested on Ubuntu / Debian.  Run with sudo.

###############################################################################
# 0.  English-only environment (no localisation surprises)
###############################################################################
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

###############################################################################
# 1.  Colour codes for pretty output
###############################################################################
RED='\033[1;31m';  GREEN='\033[1;32m';  YELLOW='\033[1;33m'
BLUE='\033[1;34m'; MAGENTA='\033[1;35m'; CYAN='\033[1;36m'; NC='\033[0m'

###############################################################################
# 2.  Must be root
###############################################################################
if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}[ERROR] Please run this script with sudo or as root.${NC}"
  exit 1
fi

echo -e "${BLUE}*********************************************************************${NC}"
echo -e "${BLUE}***  🚀 Multi-Emulator & Retro-SDK Setup Extravaganza  (English)  ***${NC}"
echo -e "${BLUE}*********************************************************************${NC}\n"
sleep 1

###############################################################################
# 3.  Update base system and add Flatpak/Snap support
###############################################################################
echo -e "${GREEN}[+] Updating package lists …${NC}"
apt update -y

echo -e "${GREEN}[+] Installing core utilities (git, flatpak, snapd, etc.) …${NC}"
apt install -y software-properties-common curl wget git flatpak snapd

# Enable Flathub (for Flatpak) once
if ! flatpak remote-list | grep -q flathub ; then
  echo -e "${GREEN}[+] Adding Flathub repository …${NC}"
  flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

###############################################################################
# 4.  Mainframes & Minicomputers
###############################################################################
echo -e "${MAGENTA}\n===== Mainframes & Minicomputers (1940s-1970s) =====${NC}"
apt install -y hercules simh            # IBM / PDP / VAX, etc.

###############################################################################
# 5.  Home / Microcomputers
###############################################################################
echo -e "${MAGENTA}\n===== 8- & 16-bit Home Computers (1970s-1990s) =====${NC}"
apt install -y vice fuse-emulator-gtk hatari fs-uae fs-uae-launcher \
               atari800 openmsx dosbox

###############################################################################
# 6.  Classic Consoles (Atari → Saturn, including SNES)
###############################################################################
echo -e "${MAGENTA}\n===== Classic Video-Game Consoles (1970s-1990s) =====${NC}"
apt install -y stella           \  # Atari 2600
               fceux            \  # NES / Famicom
               higan            \  # High-accuracy SNES / GBA / GB
               snes9x           \  # Fast SNES – extra option you asked for
               dgen             \  # Sega Genesis / Mega Drive
               yabause             # Sega Saturn

###############################################################################
# 7.  32-/64-bit Era (PS1, N64, Dreamcast, PS2)
###############################################################################
echo -e "${MAGENTA}\n===== 32-/64-bit Consoles (1990s-2000s) =====${NC}"
apt  install -y pcsxr mupen64plus-ui-console       # PS1 & N64
snap install   reicast --classic                   # Dreamcast
flatpak install -y flathub net.pcsx2.PCSX2         # PlayStation 2

###############################################################################
# 8.  GameCube, Wii, Original Xbox
###############################################################################
echo -e "${MAGENTA}\n===== GameCube / Wii / Original Xbox =====${NC}"
snap install dolphin-emulator                      # GC / Wii
add-apt-repository -y ppa:mborgerson/xemu && apt update -y
apt install -y xemu                                # Original Xbox

###############################################################################
# 9.  “Modern” HD Consoles & Handhelds
###############################################################################
echo -e "${MAGENTA}\n===== HD / Handheld Era (PS3, PSP, Switch, 3DS) =====${NC}"
snap install rpcs3-emu ppsspp-emu citra-emu        # PS3, PSP, 3DS

echo -e "${GREEN}[+] Fetching the latest Yuzu (Switch) AppImage …${NC}"
YUZU_URL="$(wget -qO- https://api.github.com/repos/yuzu-emu/yuzu-mainline/releases/latest \
            | grep -oP 'browser_download_url.*AppImage' | head -1 | cut -d '"' -f4)"

if [[ -n $YUZU_URL ]]; then
  wget -O /opt/yuzu.AppImage "$YUZU_URL"
  chmod +x /opt/yuzu.AppImage
  ln -sf /opt/yuzu.AppImage /usr/local/bin/yuzu
else
  echo -e "${YELLOW}[WARN] Could not download Yuzu automatically. Install it later from yuzu-emu.org.${NC}"
fi

###############################################################################
# 10. Hand-held oddities & calculators
###############################################################################
echo -e "${MAGENTA}\n===== Hand-helds & Calculators =====${NC}"
apt install -y mgba-qt desmume tilem tiemu         # GBA, NDS, TI-83/84/89/92

###############################################################################
# 11. Arcade Machines
###############################################################################
echo -e "${MAGENTA}\n===== Arcade Machines (MAME) =====${NC}"
apt install -y mame

###############################################################################
# 12. Retro Development SDKs
###############################################################################
echo -e "${MAGENTA}\n===== Cross-compilers & Homebrew SDKs =====${NC}"
apt install -y cc65 sdcc z88dk

echo -e "${GREEN}[+] Installing devkitPro toolchains (GBA → Switch) …${NC}"
wget -qO /tmp/install-devkitpro.sh https://apt.devkitpro.org/install-devkitpro-pacman \
  && chmod +x /tmp/install-devkitpro.sh && /tmp/install-devkitpro.sh
dkp-pacman -Syu --noconfirm
dkp-pacman -S --noconfirm gba-dev nds-dev 3ds-dev gamecube-dev wii-dev switch-dev

###############################################################################
# 13. RetroArch (one-stop frontend)
###############################################################################
echo -e "${MAGENTA}\n===== RetroArch Front-end =====${NC}"
apt install -y retroarch

###############################################################################
# 14.  Wrap-up
###############################################################################
echo -e "${GREEN}\n=== All requested emulators & SDKs are now installed! ===${NC}"
echo -e "${YELLOW}Remember: BIOS/keys/firmware and game ROMs are NOT included.${NC}"
echo -e "${YELLOW}Dump them from your own hardware to stay legal.${NC}"
echo -e "${GREEN}Have fun – game (or code) on! 🚀${NC}"

## [C] ------- Team Flames ---------
