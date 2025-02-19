#!/bin/bash

# This script attempts to optimize performance for applications running under Rosetta on M1 Macs

# Step 1: Ensure Rosetta 2 is installed
if ! /usr/bin/pgrep oahd > /dev/null 2>&1; then
    echo "Installing Rosetta 2..."
    softwareupdate --install-rosetta --agree-to-license
fi

# Step 2: Check if running under Rosetta
if [ "$(sysctl -n sysctl.proc_translated)" = "1" ]; then
    echo "This shell is running under Rosetta."
else
    echo "This shell is running natively. Switching to Rosetta for this session."
    exec arch -x86_64 /bin/bash
fi

# Step 3: Clean up potentially slow bash startup files
echo "Cleaning up bash startup files to reduce delays..."
for file in ~/.bash_profile ~/.bashrc ~/.bash_login; do
    if [ -f "$file" ]; then
        # Remove any slow commands or unnecessary sourcing
        sed -i '.bak' '/set -o/d' "$file"
        sed -i '.bak' '/source/d' "$file"
    fi
done

# Step 4: Optimize system for better performance
echo "Optimizing system performance..."
# Disable animations which might cause lag
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001

# Step 5: Clear system logs which might slow down terminal operations
echo "Clearing system logs..."
sudo rm -rf /private/var/log/asl/*.asl

echo "Performance optimization steps completed. You might need to restart your terminal or system for some changes to take effect."

# Note: Some of these steps require a restart to fully take effect, and not all will directly impact Rosetta performance but can generally improve system responsiveness.
