#!/bin/bash

# =============================================================================
#  UNIVERSAL EMULATOR INSTALLATION MEGA-SCRIPT (1920-2025)
# =============================================================================
# This chaotic script will attempt to install emulators for just about every
# computing platform from the 1940s through 2025 (with some humor thrown in).
# Buckle up, it's gonna be a wild ride!
#
# NOTE: Run this on a Debian/Ubuntu system. Use at your own risk!
# =============================================================================

# Color codes for pretty output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
MAGENTA="\033[1;35m"
CYAN="\033[1;36m"
NC="\033[0m"  # No Color

# Make sure we have sudo if not root
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo -e "${BLUE}Updating package list...${NC}"
$SUDO apt-get update -qq

echo -e "${BLUE}Installing base packages (build tools, git, etc.)...${NC}"
$SUDO apt-get install -y build-essential git curl wget cmake autoconf automake pkg-config libgtk2.0-dev figlet lolcat libsdl2-dev || {
    echo -e "${RED}Some base packages failed to install. Continuing...${NC}"
}
# SDL1.2 is legacy; try to install if available
$SUDO apt-get install -y libsdl1.2-dev 2>/dev/null || echo -e "${YELLOW}(Skipping libsdl1.2-dev, not available)${NC}"

# Function to print big colorful banners
print_banner() {
    local msg="$1"
    if command -v figlet >/dev/null; then
        # Use figlet for big text
        if command -v lolcat >/dev/null; then
            figlet -f slant "$msg" | lolcat
        else
            figlet -f slant "$msg"
        fi
    else
        # Fallback to simple banner
        echo -e "${MAGENTA}===== $msg =====${NC}"
    fi
}

# -----------------------------------------------------------------------------
# Mechanical & Early Electro-Mechanical Computers (1930s-1940s)
# -----------------------------------------------------------------------------
print_banner "Mechanical Era"
echo -e "${CYAN}Time to dust off those ancient calculators (Z3, Bombe, Colossus, ENIAC)...${NC}"
echo -e "${GREEN}Emulating mechanical beasts with sheer code and sarcasm...${NC}"

# Z3 (1941) - first programmable computer (electromechanical)
echo -e "${YELLOW}Z3 (1941): Spinning up virtual relays...${NC}"
sleep 1
echo -e "${GREEN}Z3 emulator installed! (Konrad Zuse is proud, probably.)${NC}"

# Bombe (1940s) - codebreaking machine used by Alan Turing
echo -e "${YELLOW}Bombe (1940s): Emulating codebreaking drums and circuits...${NC}"
sleep 1
echo -e "${GREEN}Bombe simulation ready! (Turing just gave a thumbs-up.)${NC}"

# Colossus (1940s) - another codebreaker
echo -e "${YELLOW}Colossus (1940s): Warming up vacuum tubes to crack some codes...${NC}"
sleep 1
echo -e "${GREEN}Colossus is humming along, breaking ciphers like it's 1944!${NC}"

# ENIAC (1945) - first electronic general-purpose computer
echo -e "${YELLOW}ENIAC (1945): Allocating 17,468 virtual vacuum tubes...${NC}"
sleep 1
echo -e "${GREEN}ENIAC emulator is up! (It's the size of a room, but we fit it in a program.)${NC}"

# -----------------------------------------------------------------------------
# Mainframes and Minicomputers (1950s-1970s)
# -----------------------------------------------------------------------------
print_banner "Mainframes"
echo -e "${CYAN}Big Iron time: Installing PDP-8, PDP-11, VAX, IBM 1401, System/360 emulators...${NC}"
echo -e "${BLUE}Installing SIMH (PDP & more) and Hercules (IBM mainframes)...${NC}"
$SUDO apt-get install -y simh || echo -e "${RED}Failed to install SIMH from apt.${NC}"
$SUDO apt-get install -y hercules || echo -e "${RED}Failed to install Hercules from apt.${NC}"

echo -e "${GREEN}SIMH installed (PDP-8, PDP-11, VAX, etc. ready to roll).${NC}"
echo -e "${GREEN}Hercules installed (IBM System/360/370 mainframe emulator ready).${NC}"
echo -e "${YELLOW}You can now pretend your PC is a 1960s IBM mainframe. Have fun with those punchcards!${NC}"

# -----------------------------------------------------------------------------
# Early Personal Computers (1970s-early 1980s)
# Altair 8800, Apple I, Apple II, Commodore PET, IBM PC
# -----------------------------------------------------------------------------
print_banner "Early PCs"
echo -e "${CYAN}Personal computing dawn: Altair 8800, Apple I/II, PET, IBM PC...${NC}"

# Altair 8800 (1975) - using SIMH AltairZ80 simulator if available
echo -e "${YELLOW}Altair 8800 (1975): Toggling in some bootstrap code via SIMH...${NC}"
if command -v simh >/dev/null; then
    echo -e "${GREEN}Altair 8800 emulator ready (SIMH AltairZ80 loaded).${NC}"
else
    echo -e "${RED}SIMH not found, skipping Altair 8800 emulation.${NC}"
fi

# Apple I (1976)
echo -e "${YELLOW}Apple I (1976): Trying to bring up Woz's wooden wonder...${NC}"
echo -e "${BLUE}No apt package, building Apple I emulator from source (imagine soldering wires)...${NC}"
sleep 1
echo -e "${GREEN}Apple I emulator installed!* ${NC}"
echo -e "${YELLOW}*Actually, we just pretend it's installed. Hope that's okay, Woz.${NC}"

# Apple II (1977)
echo -e "${YELLOW}Apple II (1977): Cloning Apple II emulator (LinApple)...${NC}"
git clone https://github.com/linappleii/linapple.git || echo -e "${RED}Failed to clone LinApple repository!${NC}"
if [ -d "linapple" ]; then
    cd linapple/src && make -f Makefile.unix && $SUDO cp linapple /usr/local/bin/ && cd ../..
    if command -v linapple >/dev/null; then
        echo -e "${GREEN}Apple II emulator (LinApple) built and installed!${NC}"
    else
        echo -e "${RED}LinApple build failed, skipping Apple II emulator.${NC}"
    fi
else
    echo -e "${RED}LinApple source not available, skipping Apple II.${NC}"
fi

# Commodore PET (1977) - using VICE (covers PET, VIC-20, C64, etc.)
echo -e "${YELLOW}Commodore PET (1977): Installing VICE (Versatile Commodore Emulator)...${NC}"
$SUDO apt-get install -y vice || echo -e "${RED}Failed to install VICE from apt.${NC}"
if command -v xpet >/dev/null; then
    echo -e "${GREEN}VICE installed! PET/VIC-20/C64/C128 emulators ready (xpet, x64 etc.).${NC}"
else
    echo -e "${RED}VICE emulator not found. Commodore PET might be skipped.${NC}"
fi

# IBM PC (1981) - using DOSBox for simplicity
echo -e "${YELLOW}IBM PC (1981): Installing DOSBox for DOS-era PC emulation...${NC}"
$SUDO apt-get install -y dosbox || echo -e "${RED}Failed to install DOSBox from apt.${NC}"
if command -v dosbox >/dev/null; then
    echo -e "${GREEN}DOSBox installed! Time to party like it's 1989 in DOS.${NC}"
else
    echo -e "${RED}DOSBox not found. No IBM PC emulation for you.${NC}"
fi

echo -e "${MAGENTA}Early personal computers are set!${NC} (Don't forget to put on your bell-bottoms.)"

# -----------------------------------------------------------------------------
# 1980s–1990s Home Computers (8-bit and 16-bit glory)
# Commodore 64, ZX Spectrum, Amiga, Atari ST, MSX, etc.
# -----------------------------------------------------------------------------
print_banner "Home Computers"
echo -e "${CYAN}Installing emulators for 1980s home micros: C64, ZX Spectrum, Amiga, Atari ST, MSX...${NC}"

# Commodore 64 (1982) - part of VICE (already installed in earlier section)
if command -v x64 >/dev/null; then
    echo -e "${GREEN}Commodore 64 emulator ready (VICE x64).${NC}"
else
    echo -e "${YELLOW}VICE (C64 emulator) not found. Attempting to install...${NC}"
    $SUDO apt-get install -y vice || echo -e "${RED}VICE install failed.${NC}"
fi

# ZX Spectrum (1982)
echo -e "${YELLOW}ZX Spectrum (1982): Installing Fuse emulator...${NC}"
$SUDO apt-get install -y fuse-emulator-gtk || echo -e "${RED}Failed to install Fuse from apt.${NC}"
if command -v fuse >/dev/null || command -v fuse-sdl >/dev/null; then
    echo -e "${GREEN}Fuse ZX Spectrum emulator installed!${NC}"
else
    echo -e "${RED}Fuse not found. No Speccy for you.${NC}"
fi

# Amiga (1985)
echo -e "${YELLOW}Commodore Amiga (1985): Installing FS-UAE...${NC}"
$SUDO apt-get install -y fs-uae || echo -e "${RED}Failed to install FS-UAE.${NC}"
if command -v fs-uae >/dev/null; then
    echo -e "${GREEN}FS-UAE installed! Amiga forever!${NC}"
else
    echo -e "${RED}FS-UAE not found. Amiga emulation skipped.${NC}"
fi

# Atari ST (1985)
echo -e "${YELLOW}Atari ST (1985): Installing Hatari emulator...${NC}"
$SUDO apt-get install -y hatari || echo -e "${RED}Failed to install Hatari.${NC}"
if command -v hatari >/dev/null; then
    echo -e "${GREEN}Hatari installed! Atari ST is ready to rock (16 MHz of fury).${NC}"
else
    echo -e "${RED}Hatari not found. No Atari ST emulation.${NC}"
fi

# MSX (1983)
echo -e "${YELLOW}MSX (1983): Installing openMSX emulator...${NC}"
$SUDO apt-get install -y openmsx || echo -e "${RED}Failed to install openMSX.${NC}"
if command -v openmsx >/dev/null; then
    echo -e "${GREEN}openMSX installed! MSX 8-bit goodness is go.${NC}"
else
    echo -e "${RED}openMSX not found. MSX emulation skipped.${NC}"
fi

echo -e "${MAGENTA}All 1980s home computer emulators are installed (hopefully)!${NC} Time to break out the cassette tapes and floppies."

# -----------------------------------------------------------------------------
# Handheld Game Consoles and Calculators
# (Game Boy, Game Boy Advance, TI graphing calculators, etc.)
# -----------------------------------------------------------------------------
print_banner "Handhelds"
echo -e "${CYAN}Installing handheld console emulators (Game Boys) and calculator emulators...${NC}"

# Nintendo Game Boy / Game Boy Color / Game Boy Advance
echo -e "${YELLOW}Game Boy (1989) & Game Boy Advance (2001): Installing mGBA...${NC}"
$SUDO apt-get install -y mgba-qt || echo -e "${RED}mGBA not found in apt, trying VisualBoyAdvance...${NC}"
if ! command -v mgba-qt >/dev/null; then
    $SUDO apt-get install -y visualboyadvance || echo -e "${RED}VisualBoyAdvance also not found.${NC}"
fi
if command -v mgba-qt >/dev/null || command -v visualboyadvance >/dev/null; then
    echo -e "${GREEN}Game Boy emulators installed! Time to catch 'em all (in glorious 8-bit).${NC}"
else
    echo -e "${RED}No Game Boy emulator installed. Pikachu is sad.${NC}"
fi

# TI Graphing Calculators (e.g., TI-83, TI-89)
echo -e "${YELLOW}TI Graphing Calculators: Installing TilEm (Z80 calcs) and TiEmu (TI-89)...${NC}"
$SUDO apt-get install -y tilem || echo -e "${RED}TilEm not found.${NC}"
$SUDO apt-get install -y tiemu || echo -e "${RED}TiEmu not found.${NC}"
if command -v tilem >/dev/null || command -v tiemu >/dev/null; then
    echo -e "${GREEN}TI calculator emulators installed! (Time to play Block Dude in class).${NC}"
else
    echo -e "${RED}No TI calculator emulators installed. Use bc or an abacus instead.${NC}"
fi

echo -e "${MAGENTA}Handheld consoles and calculators ready.${NC} Don't forget to replace the damn batteries!"

# -----------------------------------------------------------------------------
# Retro Gaming Consoles (1970s-2000s)
# Atari 2600, NES, SNES, Sega Genesis, N64, PlayStation 1, PlayStation 2
# -----------------------------------------------------------------------------
print_banner "Retro Consoles"
echo -e "${CYAN}Installing retro console emulators: Atari, NES, SNES, Genesis, N64, PS1, PS2...${NC}"

# Atari 2600 (1977)
echo -e "${YELLOW}Atari 2600 (1977): Installing Stella...${NC}"
$SUDO apt-get install -y stella || echo -e "${RED}Failed to install Stella.${NC}"
if command -v stella >/dev/null; then
    echo -e "${GREEN}Stella installed! (Time to play Combat and E.T. ... or maybe not E.T.)${NC}"
else
    echo -e "${RED}Stella not found. Atari 2600 will remain buried in the desert.${NC}"
fi

# Nintendo Entertainment System (NES, 1983)
echo -e "${YELLOW}NES (1983): Installing FCEUX...${NC}"
$SUDO apt-get install -y fceux || echo -e "${RED}FCEUX not found, trying Nestopia...${NC}"
if ! command -v fceux >/dev/null; then
    $SUDO apt-get install -y nestopia || echo -e "${RED}Nestopia not found either.${NC}"
fi
if command -v fceux >/dev/null || command -v nestopia >/dev/null; then
    echo -e "${GREEN}NES emulator installed! Ready for some 8-bit Super Mario Bros.${NC}"
else
    echo -e "${RED}No NES emulator installed. Blowing the cartridge didn't help.${NC}"
fi

# Super Nintendo (SNES, 1990)
echo -e "${YELLOW}SNES (1990): Installing SNES emulator...${NC}"
$SUDO apt-get install -y snes9x-gtk 2>/dev/null || echo -e "${RED}snes9x-gtk not found.${NC}"
if ! command -v snes9x-gtk >/dev/null; then
    $SUDO apt-get install -y zsnes 2>/dev/null || echo -e "${RED}zsnes not found (maybe 32-bit only).${NC}"
fi
if command -v snes9x-gtk >/dev/null || command -v zsnes >/dev/null; then
    echo -e "${GREEN}SNES emulator installed! Let's go rescue Princess Toadstool in 16-bit.${NC}"
else
    echo -e "${RED}No SNES emulator installed. Mode 7 will have to wait.${NC}"
fi

# Sega Genesis / Mega Drive (1988)
echo -e "${YELLOW}Sega Genesis (1988): Installing DGen...${NC}"
$SUDO apt-get install -y dgen || echo -e "${RED}Failed to install DGen.${NC}"
if command -v dgen >/dev/null; then
    echo -e "${GREEN}DGen installed! SEGA!!! (blast processing engaged)${NC}"
else
    echo -e "${RED}DGen not found. No Genesis does what Nintendon't today.${NC}"
fi

# Nintendo 64 (1996)
echo -e "${YELLOW}Nintendo 64 (1996): Installing Mupen64Plus...${NC}"
$SUDO apt-get install -y mupen64plus || echo -e "${RED}Failed to install Mupen64Plus.${NC}"
if command -v mupen64plus >/dev/null; then
    echo -e "${GREEN}Mupen64Plus installed! Do a barrel roll in 3D!${NC}"
else
    echo -e "${RED}Mupen64Plus not found. N64 emulation skipped.${NC}"
fi

# Sony PlayStation (PS1, 1994)
echo -e "${YELLOW}Sony PlayStation (PS1, 1994): Installing PCSX-Reloaded...${NC}"
$SUDO apt-get install -y pcsxr || echo -e "${RED}Failed to install PCSXR.${NC}"
if command -v pcsxr >/dev/null; then
    echo -e "${GREEN}PCSX-Reloaded installed! Time for some Final Fantasy VII.${NC}"
else
    echo -e "${RED}PCSXR not found. No PlayStation nostalgia this time.${NC}"
fi

# Sony PlayStation 2 (PS2, 2000)
echo -e "${YELLOW}Sony PlayStation 2 (2000): Installing PCSX2...${NC}"
$SUDO apt-get install -y pcsx2 || {
    echo -e "${BLUE}PCSX2 not in apt, let's build it from source (brace yourself)!${NC}"
    git clone --depth=1 https://github.com/PCSX2/pcsx2.git || echo -e "${RED}Failed to clone PCSX2 repository.${NC}"
    if [ -d "pcsx2" ]; then
        cd pcsx2
        ./build.sh --release || make -j$(nproc) || echo -e "${RED}PCSX2 build failed. (You might be missing dependencies.)${NC}"
        if [ -f "bin/PCSX2" ]; then
            $SUDO cp bin/PCSX2 /usr/local/bin/ && echo -e "${GREEN}PCSX2 built and installed!${NC}"
        else
            echo -e "${RED}PCSX2 build did not produce an executable. Skipping.${NC}"
        fi
        cd ..
    fi
}
if command -v PCSX2 >/dev/null || command -v pcsx2 >/dev/null; then
    echo -e "${GREEN}PS2 emulator ready! (Don't forget the BIOS files.)${NC}"
else
    echo -e "${RED}No PS2 emulator installed. The console might still be too powerful...${NC}"
fi

echo -e "${MAGENTA}Retro console emulators are all set!${NC} Go grab your CRT and light gun!"

# -----------------------------------------------------------------------------
# Arcade Machines (MAME)
# -----------------------------------------------------------------------------
print_banner "Arcade"
echo -e "${CYAN}Installing MAME (Multiple Arcade Machine Emulator) for arcade classics...${NC}"
$SUDO apt-get install -y mame || echo -e "${RED}Failed to install MAME from apt.${NC}"
if command -v mame >/dev/null; then
    echo -e "${GREEN}MAME installed! Insert coin to continue...${NC}"
else
    echo -e "${RED}MAME not found. No arcade games for you.${NC}"
fi

# -----------------------------------------------------------------------------
# Modern Consoles & Handhelds (2000s-2020s)
# Wii, Switch, PSP, Nintendo DS, Nintendo 3DS
# -----------------------------------------------------------------------------
print_banner "Modern Consoles"
echo -e "${CYAN}Installing modern console emulators: Wii, Switch, PSP, DS, 3DS...${NC}"

# Nintendo Wii (2006) / GameCube (2001) - Dolphin Emulator
echo -e "${YELLOW}Nintendo Wii/GameCube: Installing Dolphin emulator...${NC}"
$SUDO apt-get install -y dolphin-emu || {
    echo -e "${BLUE}Dolphin not in apt. Cloning Dolphin-emu from GitHub...${NC}"
    git clone --depth=1 https://github.com/dolphin-emu/dolphin.git || echo -e "${RED}Failed to clone Dolphin repository.${NC}"
    if [ -d "dolphin" ]; then
        cd dolphin && mkdir Build && cd Build
        cmake .. && make -j$(nproc) && $SUDO make install || echo -e "${RED}Dolphin build failed.${NC}"
        cd ../..
    fi
}
if command -v dolphin-emu >/dev/null || command -v dolphin-emu-master >/dev/null; then
    echo -e "${GREEN}Dolphin emulator ready! (Time for some Mario Kart Wii in HD)${NC}"
else
    echo -e "${RED}Dolphin not installed. No Wii for you.${NC}"
fi

# Nintendo Switch (2017) - Yuzu Emulator
echo -e "${YELLOW}Nintendo Switch: Installing Yuzu emulator...${NC}"
git clone --depth=1 https://github.com/yuzu-emu/yuzu-mainline.git || echo -e "${RED}Failed to clone Yuzu repository.${NC}"
if [ -d "yuzu-mainline" ]; then
    cd yuzu-mainline && mkdir build && cd build
    cmake .. && make -j$(nproc) && $SUDO make install || echo -e "${RED}Yuzu build failed (you might need dependencies like Qt).${NC}"
    cd ../..
fi
if command -v yuzu >/dev/null; then
    echo -e "${GREEN}Yuzu installed! Switch emulation is a go (don't forget your legally dumped games).${NC}"
else
    echo -e "${RED}Yuzu not installed. Switch might be too new or require manual setup.${NC}"
fi

# Sony PlayStation Portable (PSP, 2004) - PPSSPP
echo -e "${YELLOW}Sony PSP: Installing PPSSPP...${NC}"
$SUDO apt-get install -y ppsspp || {
    echo -e "${BLUE}PPSSPP not in apt. Cloning from GitHub...${NC}"
    git clone --depth=1 https://github.com/hrydgard/ppsspp.git || echo -e "${RED}Failed to clone PPSSPP repository.${NC}"
    if [ -d "ppsspp" ]; then
        cd ppsspp && mkdir build && cd build
        cmake .. && make -j$(nproc) && $SUDO make install || echo -e "${RED}PPSSPP build failed.${NC}"
        cd ../..
    fi
}
if command -v ppsspp >/dev/null; then
    echo -e "${GREEN}PPSSPP installed! Time to relive your PSP classics on PC.${NC}"
else
    echo -e "${RED}PPSSPP not installed. PSP emulation skipped.${NC}"
fi

# Nintendo DS (2004) - DeSmuME
echo -e "${YELLOW}Nintendo DS: Installing DeSmuME...${NC}"
$SUDO apt-get install -y desmume || {
    echo -e "${BLUE}DeSmuME not in apt. Cloning from GitHub...${NC}"
    git clone --depth=1 https://github.com/TASEmulators/desmume.git || echo -e "${RED}Failed to clone DeSmuME repository.${NC}"
    if [ -d "desmume" ]; then
        cd desmume && ./configure && make -j$(nproc) && $SUDO make install || echo -e "${RED}DeSmuME build failed.${NC}"
        cd ..
    fi
}
if command -v desmume >/dev/null; then
    echo -e "${GREEN}DeSmuME installed! Enjoy your Nintendogs and Pokémon on PC.${NC}"
else
    echo -e "${RED}DeSmuME not installed. No DS dual-screen fun.${NC}"
fi

# Nintendo 3DS (2011) - Citra
echo -e "${YELLOW}Nintendo 3DS: Installing Citra emulator...${NC}"
git clone --depth=1 https://github.com/citra-emu/citra.git || echo -e "${RED}Failed to clone Citra repository.${NC}"
if [ -d "citra" ]; then
    cd citra && mkdir build && cd build
    cmake .. && make -j$(nproc) && $SUDO make install || echo -e "${RED}Citra build failed.${NC}"
    cd ../..
fi
if command -v citra >/dev/null; then
    echo -e "${GREEN}Citra installed! 3DS emulation ready (hope you have the BIOS/firmware dumped).${NC}"
else
    echo -e "${RED}Citra not installed. 3DS might be tricky without dependencies.${NC}"
fi

echo -e "${MAGENTA}Modern console emulators done!${NC} Time to plug in that USB gamepad and enjoy. Hell yeah!"

# -----------------------------------------------------------------------------
# PDA Emulation (Palm OS and friends)
# -----------------------------------------------------------------------------
print_banner "PDA"
echo -e "${CYAN}Installing PDA emulators (Palm Pilot, etc.)...${NC}"

# Palm OS (Palm Pilot)
echo -e "${YELLOW}Palm OS (Palm Pilot): Searching for Palm emulator...${NC}"
$SUDO apt-get install -y xcopilot 2>/dev/null || echo -e "${BLUE}xcopilot not in apt. Palm OS emulator is elusive...${NC}"
if command -v xcopilot >/dev/null; then
    echo -e "${GREEN}xcopilot installed! (Palm Pilot emulator ready, time to HotSync)${NC}"
else
    echo -e "${YELLOW}No Palm OS emulator available via apt.${NC}"
    echo -e "${GREEN}Simulating a Palm Pilot by beaming IR signals... Done (just kidding).${NC}"
fi

# (Could add Windows CE, etc., but we'll skip for now)
echo -e "${MAGENTA}PDA emulation section complete.${NC} You may now play Snake on a virtual Nokia... oh wait, wrong device."

# -----------------------------------------------------------------------------
# Mobile & Smartphone Emulators (Android, iPhone)
# -----------------------------------------------------------------------------
print_banner "Mobile"
echo -e "${CYAN}Setting up mobile phone emulators (Android, iPhone*)...${NC}"
echo -e "${YELLOW}*iPhone on Linux? Well, we'll try our best...${NC}"

# Android (2008+)
echo -e "${YELLOW}Android: Installing Android SDK and Emulator...${NC}"
$SUDO apt-get install -y default-jdk 2>/dev/null || echo -e "${RED}Failed to install Java JDK. Android tools may not run.${NC}"
ANDROID_DIR="$HOME/Android"
mkdir -p "$ANDROID_DIR/cmdline-tools"
cd /tmp
echo -e "${BLUE}Downloading Android SDK command-line tools...${NC}"
wget -q https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip -O cmdline-tools.zip
unzip -q cmdline-tools.zip -d "$ANDROID_DIR/cmdline-tools"
# Accept licenses and install platforms + emulator
echo -e "${BLUE}Installing Android platform tools and emulator (this may take a while)...${NC}"
yes | "$ANDROID_DIR/cmdline-tools/cmdline-tools/bin/sdkmanager" --licenses > /dev/null 2>&1 || true
"$ANDROID_DIR/cmdline-tools/cmdline-tools/bin/sdkmanager" "platform-tools" "platforms;android-30" "system-images;android-30;default;x86_64" "emulator" > /dev/null 2>&1
# Note: For actual use, user might need to create an AVD via avdmanager.
cd ~
if [ -d "$ANDROID_DIR" ]; then
    echo -e "${GREEN}Android emulator installed! (You'll need to create an AVD and then run 'emulator' to use it.)${NC}"
else
    echo -e "${RED}Android emulator installation failed or incomplete. (Maybe just install Android Studio?)${NC}"
fi

# iPhone (2007+) - no official emulator on Linux
echo -e "${YELLOW}iPhone: Attempting to install iPhone simulator...${NC}"
sleep 2
echo -e "${RED}Error 404: Apple doesn't allow iPhone emulators on Linux. Aborting.${NC}"
echo -e "${YELLOW}(Seriously, there's no real iPhone simulator outside macOS/Xcode. Sorry.)${NC}"

echo -e "${MAGENTA}Mobile device emulation step complete.${NC} (Your Android emulator is ready; iPhone... not so much.)"

# -----------------------------------------------------------------------------
# Futuristic Devices (2025 and beyond) - Just for fun!
# -----------------------------------------------------------------------------
print_banner "Future Tech"
echo -e "${CYAN}Emulating hypothetical future tech (because why not)...${NC}"

# Quantum Computer Simulator
echo -e "${YELLOW}Quantum Computer (2025): Initializing qubits and entanglement...${NC}"
sleep 2
echo -e "${GREEN}Quantum computer emulator ready! (It's simultaneously working and not working until observed.)${NC}"

# Star Trek Holodeck
echo -e "${YELLOW}Star Trek Holodeck: Engaging holo-emitters and safety protocols...${NC}"
sleep 2
echo -e "${GREEN}Holodeck simulation running! (Computer: \"Tea, Earl Grey, hot.\")${NC}"

# Skynet T-800 Terminator Neural Net
echo -e "${YELLOW}Skynet Neural Net: Booting up self-aware AI core...${NC}"
sleep 2
echo -e "${GREEN}Skynet T-800 emulator activated. (It says: \"I'll be back.\")${NC}"

echo -e "${MAGENTA}Future tech emulation complete. The future is now (sort of)!${NC}"

# =============================================================================
echo -e "${GREEN}ALL DONE!${NC} You've just installed emulators for about a century of computing! 🎉"
if command -v figlet >/dev/null; then
    if command -v lolcat >/dev/null; then
        figlet "DONE!" | lolcat
    else
        figlet "DONE!"
    fi
fi
echo -e "${MAGENTA}Now go forth and emulate all the things!${NC}"
echo -e "${MAGENTA}Launching an interactive shell. Have fun!${NC}"
exec bash
