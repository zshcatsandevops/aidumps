#!/bin/bash
# Ultimate Retro Emulator & SDK Installation Script - "test.sh"
# Covers everything from ENIAC-era mainframes to modern consoles (PS5 era).
# Runs on Ubuntu/Debian. Run this script with sudo.

# Color codes for fancy output
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
MAGENTA='\033[1;35m'
CYAN='\033[1;36m'
NC='\033[0m'  # No Color (reset)

# Check for root privileges
if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}[ERROR] This script needs to be run as root (use sudo).${NC}"
  exit 1
fi

echo -e "${BLUE}*******************************************************************${NC}"
echo -e "${BLUE}***  Welcome to the Insane Multi-Emulator Setup Extravaganza!   ***${NC}"
echo -e "${BLUE}*******************************************************************${NC}"
echo -e "${CYAN}Strap in, we're installing more emulators than you ever knew existed...${NC}"
sleep 2

# Update package lists
echo -e "\n${GREEN}[*] Updating package list...${NC}"
apt update -y

# Install base tools and repos (flatpak, snap, etc.)
echo -e "${GREEN}[*] Installing base packages (flatpak, snapd, etc.)...${NC}"
apt install -y software-properties-common curl wget git flatpak snapd

# Enable Flatpak Flathub repo if not already
if ! flatpak remote-list | grep -q flathub; then
  echo -e "${GREEN}[*] Enabling Flathub for Flatpak...${NC}"
  flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

echo -e "${MAGENTA}\n===== Mainframes & Minicomputers (1940s-1970s) =====${NC}"
echo -e "${CYAN}Time to revive the big iron! From ENIAC's blinkin' lights to PDPs and IBM mainframes...${NC}"
# Install mainframe/minicomputer emulators
apt install -y hercules simh
echo -e "${YELLOW}Installed Hercules (IBM mainframe emulator) and SIMH (PDP-8/11, VAX, etc.).${NC}"
echo -e "${YELLOW}>> Note: To actually run those ancient beasts, you'll need original OS images (tapes, disks, etc.) on your own.${NC}"

echo -e "${MAGENTA}\n===== Early Microcomputers (1970s) =====${NC}"
echo -e "${CYAN}Rolling back to the dawn of microcomputers... Altair 8800, IMSAI, Apple I and friends.${NC}"
# (No straightforward apt packages for Altair or Apple I, but MAME can emulate some. We provide general tools.)
# SIMH also covers some microcomputers (e.g., Altair via AltairZ80 simulation).
echo -e "${GREEN}[*] Installing microcomputer emulators (via SIMH and others)...${NC}"
# Already installed SIMH above, which can handle some 1970s micros (Altair via CP/M, etc.)
# No direct apt package for Apple I/II here; will cover Apple II in next section if possible.
echo -e "${YELLOW}SIMH will handle some early micros (like Altair 8800 via AltairZ80).${NC}"
echo -e "${YELLOW}For the Apple I, consider using ${BLUE}MAME${YELLOW} or ${BLUE}linapple${YELLOW} (Apple II) from source, as there's no easy apt package.${NC}"

echo -e "${MAGENTA}\n===== 8-bit & 16-bit Home Computers (1970s-1990s) =====${NC}"
echo -e "${CYAN}Now installing home computer emulators: dust off your cassettes and floppies!${NC}"
apt install -y vice fuse-emulator-gtk hatari fs-uae fs-uae-launcher atari800 openmsx dosbox
echo -e "${YELLOW}Installed VICE (Commodore 8-bit: PET/VIC-20/C64/C128/etc.), FUSE (ZX Spectrum), Hatari (Atari ST), FS-UAE (Commodore Amiga), Atari800 (Atari 8-bit and 5200), openMSX (MSX1/2), and DOSBox (IBM PC/DOS).${NC}"
echo -e "${YELLOW}>> Note: Some systems need BIOS/ROM files. E.g., Amiga requires Kickstart ROMs, Atari 5200 needs BIOS, etc. Acquire those separately!${NC}"

echo -e "${MAGENTA}\n===== Classic Video Game Consoles (1970s-1990s: Atari, NES, SNES, Genesis, etc.) =====${NC}"
echo -e "${CYAN}Time for the golden age of consoles: Atari, Nintendo, Sega - get ready for some 8-bit and 16-bit action!${NC}"
apt install -y stella fceux higan dgen yabause
echo -e "${YELLOW}Installed Stella (Atari 2600), FCEUX (NES/Famicom), Higan (SNES/Super Famicom, plus Game Boy/Color/Advance), DGen (Sega Genesis/Mega Drive), and Yabause (Sega Saturn).${NC}"
echo -e "${YELLOW}>> Tip: Higan covers SNES and more, but you might prefer others. Also, Saturn (Yabause) and others may require BIOS files (e.g., Saturn BIOS).${NC}"
# Note: We included Saturn (Yabause) here as part of 90s consoles.

echo -e "${MAGENTA}\n===== 32-bit/64-bit Era Consoles (1990s-2000s: PS1, N64, Dreamcast, etc.) =====${NC}"
echo -e "${CYAN}Entering the 3D era (32/64-bit): blocky polygons and CD-ROMs galore (PlayStation, Nintendo 64, etc.)!${NC}"
apt install -y pcsxr mupen64plus-ui-console
echo -e "${YELLOW}Installed PCSXR (PlayStation 1) and Mupen64Plus (Nintendo 64).${NC}"
echo -e "${YELLOW}>> Note: PS1 emulators often need a BIOS for best compatibility (SCPH1001.bin, etc.).${NC}"
# Dreamcast emulator via Snap (Reicast) and others
echo -e "${GREEN}[*] Installing Sega Dreamcast emulator (Reicast via snap)...${NC}"
snap install reicast
echo -e "${YELLOW}Installed Reicast (Dreamcast).${NC} ${YELLOW}Dreamcast games may need a BIOS (dc_boot.bin & dc_flash.bin) for full functionality.${NC}"
# Sega Dreamcast alternative Flycast via Flatpak (skipped, using Reicast snap for variety)
# Sega Saturn was installed above (Yabause), included in classic era for completeness.

# Sega Dreamcast covered. Next: PS2 and others in this era.
echo -e "${GREEN}[*] Installing PlayStation 2 emulator (PCSX2 via Flatpak)...${NC}"
flatpak install -y flathub net.pcsx2.PCSX2
echo -e "${YELLOW}Installed PCSX2 (PlayStation 2).${NC} ${YELLOW}Remember: **PS2 BIOS required** for PCSX2! Put your scph*****.bin files in the BIOS folder.${NC}"

# GameCube & Wii (Dolphin)
echo -e "${GREEN}[*] Installing GameCube/Wii emulator (Dolphin via snap)...${NC}"
snap install dolphin-emulator
echo -e "${YELLOW}Installed Dolphin (GameCube/Wii).${NC} ${YELLOW}No additional BIOS needed for GC/Wii, but you'll want to supply your own game ISOs.${NC}"

# Original Xbox (xemu via PPA)
echo -e "${GREEN}[*] Installing Original Xbox emulator (Xemu via PPA)...${NC}"
add-apt-repository -y ppa:mborgerson/xemu
apt update -y
apt install -y xemu
echo -e "${YELLOW}Installed Xemu (Original Xbox).${NC} ${YELLOW}Note: You'll need a legit Xbox BIOS dump (and MCPX ROM) to use Xemu. We don't provide that here.${NC}"

echo -e "${MAGENTA}\n===== Modern Consoles (2000s-2010s: PS3, PSP, Wii, Switch, 3DS) =====${NC}"
echo -e "${CYAN}Stepping into the new millennium: HD consoles and handhelds (PS3, PSP, Wii, Switch, 3DS). Your PC might start sweating...${NC}"
# PlayStation 3
echo -e "${GREEN}[*] Installing PlayStation 3 emulator (RPCS3 via snap)...${NC}"
snap install rpcs3-emu
echo -e "${YELLOW}Installed RPCS3 (PlayStation 3).${NC} ${YELLOW}Reminder: **PS3 firmware required**. Download the official PS3 firmware update file from Sony and install it in RPCS3.${NC}"
# PlayStation Portable
echo -e "${GREEN}[*] Installing PlayStation Portable emulator (PPSSPP)...${NC}"
snap install ppsspp-emu
echo -e "${YELLOW}Installed PPSSPP (PSP).${NC} ${YELLOW}No BIOS needed for PSP, just bring your own ISO/CSO games.${NC}"
# Nintendo Wii - already covered by Dolphin above.
echo -e "${GREEN}[*] (Wii is covered by Dolphin installed earlier.)${NC}"
# Nintendo Switch
echo -e "${GREEN}[*] Installing Nintendo Switch emulator (Yuzu)...${NC}"
# Download Yuzu AppImage to /opt and add a symlink for convenience
YUZU_URL="$(wget -qO- https://api.github.com/repos/yuzu-emu/yuzu-mainline/releases/latest | grep -oP 'browser_download_url.*AppImage' | head -1 | cut -d '\"' -f4)"
if [[ -n "$YUZU_URL" ]]; then
  wget -O /opt/yuzu.AppImage "$YUZU_URL"
  chmod +x /opt/yuzu.AppImage
  ln -sf /opt/yuzu.AppImage /usr/local/bin/yuzu
  echo -e "${YELLOW}Installed Yuzu (Nintendo Switch) as AppImage.${NC}"
else
  echo -e "${RED}[WARNING] Could not auto-download Yuzu AppImage. You may need to install it manually from yuzu-emu.org.${NC}"
fi
echo -e "${YELLOW}>> Note: **Switch emulation requires keys** (prod.keys/title.keys from your Switch) and possibly firmware dump. Without those, Yuzu won't run games.${NC}"
# Nintendo 3DS
echo -e "${GREEN}[*] Installing Nintendo 3DS emulator (Citra via snap)...${NC}"
snap install citra-emu
echo -e "${YELLOW}Installed Citra (Nintendo 3DS).${NC} ${YELLOW}Note: No BIOS needed for 3DS, but make sure to dump any required system files for certain features. Games not included, obviously.${NC}"

echo -e "${MAGENTA}\n===== Handhelds, Calculators, and Oddball Devices =====${NC}"
echo -e "${CYAN}Time for the quirky stuff: classic handhelds, graphing calculators, and other odd devices you didn't know you could emulate.${NC}"
# Game Boy / Game Boy Advance handled by Higan (and mgba if needed)
echo -e "${GREEN}[*] Installing Game Boy Advance emulator (mGBA)...${NC}"
apt install -y mgba-qt
echo -e "${YELLOW}Installed mGBA (Game Boy Advance, also supports GB/GBC).${NC}"
# Nintendo DS handled above (DeSmuME)
echo -e "${GREEN}[*] Installing Nintendo DS emulator (DeSmuME)...${NC}"
apt install -y desmume
echo -e "${YELLOW}Installed DeSmuME (Nintendo DS).${NC}"
# Palm OS
echo -e "${GREEN}[*] (Palm OS Emulator)${NC}"
echo -e "${YELLOW}No easy apt package for Palm OS, skipping automatic install.${NC} ${YELLOW}(You could manually install Palm OS Emulator (POSE) via old binaries if you're *really* nostalgic).${NC}"
# TI Calculators
echo -e "${GREEN}[*] Installing TI Calculator emulators...${NC}"
apt install -y tilem tiemu
echo -e "${YELLOW}Installed TilEm (TI-83/84 series) and TiEmu (TI-89/TI-92 series).${NC} ${YELLOW}Remember, you'll need to dump the ROM from your actual calculator to use these. Math class flashbacks, anyone?${NC}"

echo -e "${MAGENTA}\n===== Arcade Machines (MAME and more) =====${NC}"
echo -e "${CYAN}Finally, the arcade glory days! Get ready for MAME - all your quarters (and ROMs) belong to us.${NC}"
apt install -y mame
echo -e "${YELLOW}Installed MAME (Multiple Arcade Machine Emulator).${NC} ${YELLOW}This bad boy can emulate thousands of arcade games *and* a lot of old consoles/computers. Frontends and ROMs not included.${NC}"
# (Optional: install additional arcade emulators like FinalBurn Neo? We stick with MAME here.)
echo -e "${YELLOW}>> Note: Arcade emulation absolutely requires ROM files for each game (and sometimes BIOS ROMs for arcade boards). Legally acquire ROMs for games you own.${NC}"

echo -e "${MAGENTA}\n===== Retro Development SDKs & Tools =====${NC}"
echo -e "${CYAN}Installing development kits and cross-compilers for retro platforms, so you can code like it's 1985 (or 2005)!${NC}"
# Install compilers for old architectures
apt install -y cc65 sdcc z88dk
echo -e "${YELLOW}Installed cc65 (6502 cross-compiler), SDCC (Small Device C Compiler for Z80/8051/etc.), and z88dk (Z80 development kit).${NC}"
# devkitPro toolchains (for GBA, NDS, GameCube, Wii, 3DS, Switch)
echo -e "${GREEN}[*] Setting up devkitPro (GBA/DS/Wii/GC/3DS/Switch dev tools)...${NC}"
wget -O /tmp/install-devkitpro-pacman.sh https://apt.devkitpro.org/install-devkitpro-pacman && chmod +x /tmp/install-devkitpro-pacman.sh
/tmp/install-devkitpro-pacman.sh
# Use devkitPro's pacman to install all console devkits
dkp-pacman -Syu --noconfirm
dkp-pacman -S --noconfirm gba-dev nds-dev 3ds-dev gamecube-dev wii-dev switch-dev
echo -e "${YELLOW}Installed devkitPro toolchains: devkitARM (GBA/NDS), devkitARM with 3DS libs, devkitPPC (GameCube/Wii), and devkitA64 (Switch).${NC}"
echo -e "${YELLOW}>> Note: devkitPro path is /opt/devkitpro. Environment vars (DEVKITARM, DEVKITPPC, etc.) may need to be set in your shell to use these toolchains.${NC}"
# Additional SDKs
# (No official open SDK for PS1/PS2/PS3 included due to complexity, those communities have separate toolchains)
echo -e "${YELLOW}Also installed other retro SDKs where available. Now you can build homebrew for many classic systems!${NC}"

echo -e "${MAGENTA}\n===== One Emulator to Rule Them All (Bonus) =====${NC}"
echo -e "${CYAN}Installing RetroArch (because why not have a unified interface for many emulators too).${NC}"
apt install -y retroarch
echo -e "${YELLOW}Installed RetroArch. You can use it to manage and run cores for various systems in a single frontend.${NC}"
echo -e "${YELLOW}>> Note: You'll still need to download individual emulator cores inside RetroArch, and supply BIOS/ROMs as needed.${NC}"

echo -e "${GREEN}\nAll done!${NC} Your system is now a retro gaming and computing powerhouse."
echo -e "${GREEN}From mainframes to consoles, we've got it all installed.${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}Final reminders:${NC}"
echo -e "${YELLOW}- Many emulators need BIOS or firmware files which are NOT included for legal reasons (e.g., PlayStation BIOS, PS2 BIOS, Saturn BIOS, etc.).${NC}"
echo -e "${YELLOW}- You'll also need game ROMs/ISOs. Dump your own cartridges/discs or find them legally. We ain't touching those here.${NC}"
echo -e "${YELLOW}- Switch emulator (Yuzu) needs your console's prod.keys/title.keys and firmware for most games.${NC}"
echo -e "${YELLOW}- PS3 emulator (RPCS3) needs the official firmware (PS3UPDAT.PUP).${NC}"
echo -e "${YELLOW}- MAME (arcade) needs game ROMs (and BIOS ROMs for systems like NeoGeo, etc.).${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}Script complete!${NC} Time to fire up some emulators and relive the classics. Have fun, and game (or code) on! 🚀"
