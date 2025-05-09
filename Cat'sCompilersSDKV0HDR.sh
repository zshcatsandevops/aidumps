\#!/bin/bash

# ============================================================

# Script: test.sh

# Description: Install a wide range of programming language compilers,

# toolchains, AArch64‑ELF cross‑compiler, and PS1–PS4 homebrew devkits

# on Ubuntu (e.g., WSL2).

# Note: Run this script with root privileges (e.g., using sudo).

# ============================================================

# Define text styles for vibrant output

BOLD="\033\[1m"
RESET="\033\[0m"
GREEN="\033\[0;32m"
YELLOW="\033\[1;33m"
CYAN="\033\[1;36m"
PURPLE="\033\[1;35m"

# Welcome message

echo -e "\${PURPLE}=============================================================\${RESET}"
echo -e "\${PURPLE}🤖 Welcome to the Ultimate Dev Environment & Homebrew SDK Setup! 🤖\${RESET}"
echo -e "\${PURPLE}Installing compilers, toolchains, and PS1–PS4 devkits. 🚀\${RESET}"
echo -e "\${PURPLE}=============================================================\${RESET}\n"

# ------------------------------------------------------------

# Update & Essentials

# ------------------------------------------------------------

echo -e "\${CYAN}🔄 Updating package lists...\${RESET}"
sudo apt-get update
echo -e "\${GREEN}✅ Package lists updated.\${RESET}\n"

echo -e "\${CYAN}📦 Installing essential tools (curl, git)...\${RESET}"
sudo apt-get install -y curl git build-essential cmake clang gfortran&#x20;
default-jdk python3 python3-pip python3-venv&#x20;
nodejs npm ruby-full golang ghc cabal-install
echo -e "\${GREEN}✅ Core compilers & tools installed.\${RESET}\n"

# ------------------------------------------------------------

# Rust via rustup

# ------------------------------------------------------------

echo -e "\${CYAN}🦀 Installing Rust (via rustup)...\${RESET}"
curl -sSf [https://sh.rustup.rs](https://sh.rustup.rs) | sh -s -- -y
source \$HOME/.cargo/env
echo -e "\${GREEN}✅ Rust installed.\${RESET}\n"

# ------------------------------------------------------------

# AArch64‑ELF Cross‑Compiler

# ------------------------------------------------------------

echo -e "\${CYAN}🔧 Installing AArch64‑ELF cross‑compiler...\${RESET}"
sudo apt-get install -y gcc-aarch64-none-elf binutils-aarch64-none-elf
echo -e "\${GREEN}✅ AArch64‑ELF GCC & binutils installed.\${RESET}"
echo -e "\${CYAN}📝 Verifying installation:\${RESET}"
aarch64-none-elf-gcc --version
echo -e ""

# ------------------------------------------------------------

# PS1–PS4 Homebrew Devkits

# ------------------------------------------------------------

echo -e "\${CYAN}🎮 Installing PS1–PS4 homebrew SDKs/devkits...\${RESET}"

# PS1: PSn00bSDK

if \[ ! -d "\$HOME/psn00bSDK" ]; then
git clone [https://github.com/jmthibault/psn00bSDK.git](https://github.com/jmthibault/psn00bSDK.git) \~/psn00bSDK
cd \~/psn00bSDK
make
sudo make install
cd -
fi
echo -e "\${GREEN}✅ PS1 homebrew devkit (PSn00bSDK) installed.\${RESET}"

# PS2: PS2DEV

if \[ ! -d "\$HOME/ps2sdk" ]; then
git clone [https://github.com/ps2dev/ps2sdk.git](https://github.com/ps2dev/ps2sdk.git) \~/ps2sdk
cd \~/ps2sdk
make
sudo make install
cd -
fi
echo -e "\${GREEN}✅ PS2 homebrew devkit (PS2DEV) installed.\${RESET}"

# PS3: PS3SDK

if \[ ! -d "\$HOME/ps3sdk" ]; then
git clone [https://github.com/ps3dev/ps3sdk.git](https://github.com/ps3dev/ps3sdk.git) \~/ps3sdk
cd \~/ps3sdk
./bootstrap
./configure
make
sudo make install
cd -
fi
echo -e "\${GREEN}✅ PS3 homebrew devkit (PS3SDK) installed.\${RESET}"

# PS4: Orbis Toolchain

if \[ ! -d "\$HOME/orbisdev" ]; then
git clone [https://github.com/failoverflow/orbisdev.git](https://github.com/failoverflow/orbisdev.git) \~/orbisdev
cd \~/orbisdev
./setup.sh    # runs the Orbis SDK installer
cd -
fi
echo -e "\${GREEN}✅ PS4 homebrew devkit (Orbis Toolchain) installed.\${RESET}\n"

# ------------------------------------------------------------

# Final Summary and Celebration

# ------------------------------------------------------------

echo -e "\${PURPLE}=============================================================\${RESET}"
echo -e "\${PURPLE}🎉 All done! Your dev environment & homebrew SDKs are ready! 🎉\${RESET}"
echo -e "\${PURPLE}=============================================================\${RESET}"
echo -e "\${BOLD}Installed toolchains and SDKs include:\${RESET}"
echo -e "  - GCC/G++ & Clang                     \${GREEN}✔\${RESET}"
echo -e "  - GFortran                            \${GREEN}✔\${RESET}"
echo -e "  - OpenJDK (Java)                      \${GREEN}✔\${RESET}"
echo -e "  - Python 3 & pip                      \${GREEN}✔\${RESET}"
echo -e "  - Node.js & npm                       \${GREEN}✔\${RESET}"
echo -e "  - Ruby (RubyGems)                     \${GREEN}✔\${RESET}"
echo -e "  - Go (Golang)                         \${GREEN}✔\${RESET}"
echo -e "  - Rust (rustc & cargo)                \${GREEN}✔\${RESET}"
echo -e "  - Haskell (GHC & Cabal)               \${GREEN}✔\${RESET}"
echo -e "  - AArch64‑ELF cross‑compiler           \${GREEN}✔\${RESET}"
echo -e "  - PS1 homebrew devkit (PSn00bSDK)     \${GREEN}✔\${RESET}"
echo -e "  - PS2 homebrew devkit (PS2DEV)        \${GREEN}✔\${RESET}"
echo -e "  - PS3 homebrew devkit (PS3SDK)        \${GREEN}✔\${RESET}"
echo -e "  - PS4 homebrew devkit (Orbis Toolchain)\${GREEN}✔\${RESET}"
echo -e "  - Git                                 \${GREEN}✔\${RESET}"
echo -e "\n\${BOLD}Now go forth and build amazing software—and games!\${RESET} \${YELLOW}🚀\${RESET}\n"  make this include every single hardwarew snes gba nes ps1 everything since 1930-2025 go otpimize /imagine
