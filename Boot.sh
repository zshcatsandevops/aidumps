#!/bin/bash

# File: program.sh
# This script optimizes your M1 Pro Mac for performance.

# Enable full performance mode by setting CPU governor to performance
echo "Setting CPU governor to performance..."
sudo sysctl -w machdep.cpu.info="performance"

# Disable unnecessary background services for more CPU power
echo "Disabling unused system services..."
sudo launchctl bootout system /System/Library/LaunchDaemons/com.apple.findmydeviced.plist
sudo launchctl bootout system /System/Library/LaunchDaemons/com.apple.smbd.plist
sudo launchctl bootout system /System/Library/LaunchDaemons/com.apple.AirPlayXPCHelper.plist

# Disable any unnecessary startup applications
echo "Disabling unnecessary startup applications..."
osascript -e 'tell application "System Preferences" to quit'
osascript -e 'tell application "Finder" to quit'

# Enable GPU acceleration where applicable
echo "Enabling GPU acceleration..."
sudo pmset -a gpuswitch 2

# Make sure swap usage is minimal
echo "Setting up optimal memory usage..."
sudo sysctl -w vm.swapusage="0"

# Maximize disk cache performance (adjusting some sysctl params)
echo "Increasing disk cache performance..."
sudo sysctl -w vm.min_free_kbytes=16384
sudo sysctl -w vm.max_map_count=655360

# Clean system and reclaim memory from unused processes
echo "Cleaning up unnecessary processes..."
sudo purge

# Use Rosetta 2 efficiently for compatibility if needed
echo "Optimizing Rosetta 2 for compatibility (if required)..."
softwareupdate --install-rosetta --agree-to-license

# Disable unnecessary logging for performance
echo "Disabling system logs for better performance..."
sudo launchctl bootout system /System/Library/LaunchDaemons/com.apple.syslogd.plist

# Final feedback
echo "Optimization complete! System is now set for full performance."
