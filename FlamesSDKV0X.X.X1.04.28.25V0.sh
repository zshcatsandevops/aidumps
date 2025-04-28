#!/usr/bin/env bash
# 🚀 Ultimate Retro Emulator & SDK Installation Script – “test.sh”
# EN-only, Ubuntu/Debian. Run with sudo.

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C.UTF-8 LANG=C.UTF-8

#── Colors ────────────────────────────────────────────────────────────────────
RED='\033[1;31m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; MAGENTA='\033[1;35m'; CYAN='\033[1;36m'; NC='\033[0m'

#── Helpers ───────────────────────────────────────────────────────────────────
add_ppa() {
  local ppa="$1"
  if ! grep -Rq "^deb .*$ppa" /etc/apt/sources.list.d; then
    echo -e "${GREEN}[+] Adding PPA: ${ppa}${NC}"
    add-apt-repository -y "ppa:${ppa}"
    needs_update=1
  fi
}

install_snaps() {
  for pkg in "${SNAP_PACKAGES[@]}"; do
    if ! snap list | grep -qw "$pkg"; then
      echo -e "${GREEN}[+] snap install ${pkg}${NC}"
      snap install "$pkg" --classic
    fi
  done
}

install_flatpaks() {
  if ! flatpak remote-list | grep -q flathub; then
    echo -e "${GREEN}[+] flatpak remote-add flathub${NC}"
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
  fi
  for pkg in "${FLATPAK_PACKAGES[@]}"; do
    if ! flatpak list | grep -qw "$pkg"; then
      echo -e "${GREEN}[+] flatpak install ${pkg}${NC}"
      flatpak install -y flathub "$pkg"
    fi
  done
}

install_yuzu() {
  echo -e "${GREEN}[+] Fetching latest Yuzu AppImage…${NC}"
  local url
  url=$(wget -qO- https://api.github.com/repos/yuzu-emu/yuzu-mainline/releases/latest \
        | grep -oP 'browser_download_url.*AppImage' | head -1 | cut -d '"' -f4)
  if [[ -n "$url" ]]; then
    echo -e "${GREEN}[+] Downloading Yuzu…${NC}"
    wget -qO /opt/yuzu.AppImage "$url"
    chmod +x /opt/yuzu.AppImage
    ln -sf /opt/yuzu.AppImage /usr/local/bin/yuzu
  else
    echo -e "${YELLOW}[!] Yuzu download failed; please install manually.${NC}"
  fi
}

#── Root check ─────────────────────────────────────────────────────────────────
if (( EUID != 0 )); then
  echo -e "${RED}[ERROR] Please run as root (sudo).${NC}" >&2
  exit 1
fi

echo -e "${BLUE}=== Multi-Emulator & Retro-SDK Installer (EN) ===${NC}"
sleep 1

#── Base system prep ───────────────────────────────────────────────────────────
echo -e "${CYAN}[1/4] Updating system & installing core deps…${NC}"
apt update -qq
apt install -qq -y software-properties-common curl wget git flatpak snapd

#── Add PPAs ───────────────────────────────────────────────────────────────────
declare -a PPAS=(
  "ewscott9/snes9x"         # SNES9x
  "samoilov-lex/retrogames" # Higan & friends
  "mborgerson/xemu"         # Original Xbox
)
needs_update=0
for p in "${PPAS[@]}"; do add_ppa "$p"; done
if (( needs_update )); then
  echo -e "${CYAN}[+] Running apt update again…${NC}"
  apt update -qq
fi

#── Install APT packages ────────────────────────────────────────────────────────
declare -a APT_PACKAGES=(
  # Mainframes / micro / home
  hercules simh vice fuse-emulator-gtk hatari fs-uae fs-uae-launcher
  atari800 openmsx dosbox
  # Classic consoles
  stella fceux higan snes9x dgen yabause
  # 32/64-bit era
  pcsxr mupen64plus-ui-console
  # handhelds & oddballs
  mgba-qt desmume tilem tiemu
  # arcade, SDKs
  mame cc65 sdcc z88dk retroarch
)
echo -e "${CYAN}[2/4] Installing ${#APT_PACKAGES[@]} APT packages…${NC}"
apt install -qq -y "${APT_PACKAGES[@]}"

#── Snaps & Flatpaks ───────────────────────────────────────────────────────────
declare -a SNAP_PACKAGES=(
  reicast dolphin-emulator rpcs3-emu ppsspp-emu citra-emu
)
declare -a FLATPAK_PACKAGES=(
  net.pcsx2.PCSX2
)
echo -e "${CYAN}[3/4] Installing snaps…${NC}"
install_snaps
echo -e "${CYAN}[3/4] Installing flatpaks…${NC}"
install_flatpaks

#── Yuzu ───────────────────────────────────────────────────────────────────────
echo -e "${CYAN}[4/4] Installing Yuzu…${NC}"
install_yuzu

#── Done ───────────────────────────────────────────────────────────────────────
echo -e "${GREEN}\n✔ All emulators & SDKs installed!${NC}"
echo -e "${YELLOW}⚠ Remember: BIOS/keys/firmware & ROMs are NOT included.${NC}"
echo -e "${GREEN}Enjoy – game (or code) on! 🚀${NC}"
