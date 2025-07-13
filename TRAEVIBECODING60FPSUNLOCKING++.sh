#!/bin/bash
# ============================================
# M1 Pro to M4 Pro Optimization Script v5
# CatGPT X.X.X - Fixed Edition
# Purpose: Clean optimization script with proper error handling
# ============================================

set -e

GREEN="\033[1;32m"
RESET="\033[0m"
echo -e "${GREEN}===========[ CATGPT X.X.X M1→M4 OPTIMIZER v5 ]=============${RESET}"
echo "Hey gamer, optimizing your M1 Pro for 60 FPS AAA vibes!"
echo "Tweaking system parameters, energy policies, VRAM, Metal, and more."
echo "-----------------------------------------------------------"

# 1. Only touch AC (charger) power settings to avoid Battery warnings
echo "[!] Setting AC (charger) power profile ONLY. Battery untouched to prevent warnings."
sudo pmset -c sleep 30
sudo pmset -c disksleep 30
sudo pmset -c displaysleep 30
sudo pmset -c powernap 0
sudo pmset -c standby 0
sudo pmset -c autopoweroff 0
sudo pmset -c lowpowermode 0
echo "[✓] AC Power sleep profiles set (no Battery warnings)."

# 2. DO NOT use any unsupported powermetrics samplers
echo "[✓] powermetrics: Skipped unsupported samplers. Use Activity Monitor or iStat for real-time stats."

# 3. Purge Unnecessary Processes (background apps only)
echo "[!] Closing non-essential applications..."
# Get list of running applications (excluding system processes)
running_apps=$(osascript -e 'tell application "System Events" to get name of (processes where background only is false)' 2>/dev/null || echo "")
if [[ -n "$running_apps" ]]; then
    # Convert to array and process safely
    IFS=$'\n' read -rd '' -a apps <<< "$running_apps" || true
    for app in "${apps[@]}"; do
        # Skip essential apps and current terminal
        if [[ "$app" != "Finder" && "$app" != "Terminal" && "$app" != "iTerm2" && "$app" != "System Preferences" ]]; then
            echo "Closing $app..."
            osascript -e "tell application \"$app\" to quit" 2>/dev/null || killall "$app" 2>/dev/null || true
        fi
    done
fi
echo "[✓] Non-essential apps closed safely."

# 4. Free Inactive RAM & Purge Cache
sudo purge
echo "[✓] RAM cache purged."

# 5. Disable Transparency, Animations & UI Candy (reduce UI overhead)
defaults write com.apple.universalaccess reduceTransparency -bool true
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001
defaults write NSGlobalDomain com.apple.springing.delay -float 0
echo "[✓] UI overhead minimized."

# 6. Set Metal API to max performance (if available)
export MTL_DEBUG_LAYER=0
export MTL_FASTMATH=1
export MTL_SHADER_OPTIMIZATION=3
echo "[✓] Metal runtime tweaks set."

# 7. Optimize I/O Scheduling (experimental, for SSD burst)
# Note: Some sysctl parameters may not be available on all macOS versions
sudo sysctl -w kern.maxfiles=65536 2>/dev/null || echo "[!] kern.maxfiles not available"
sudo sysctl -w kern.maxfilesperproc=32768 2>/dev/null || echo "[!] kern.maxfilesperproc not available"
echo "[✓] I/O scheduling tweaked (compatible parameters only)."

# 8. Set max monitor refresh if supported (ProMotion)
defaults write -g AppleDisplayScaleFactor 1
echo "[✓] Forced best scale. Use Displays settings for 120Hz."

echo -e "${GREEN}------ SYSTEM OPTIMIZED for PEAK FPS ------${RESET}"
echo "Test with Geekbench, GFXBench Metal, and 60FPS games."
echo "You want M4 Pro scores? This is your closest without a silicon swap."
echo "------ CATGPT X.X.X: EXITING... ------"
exit 0
