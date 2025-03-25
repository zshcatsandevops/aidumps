#!/bin/bash
# Run as root
# test.sh - Windows 11 Optimization Equivalent for Linux/macOS

# Check for root
if [[ "$EUID" -ne 0 ]]; then
    echo "Please run this script as root!"
    exit 1
fi

echo "Starting Linux/macOS system optimization..."

# Set CPU performance governor to performance
if command -v cpupower >/dev/null; then
    cpupower frequency-set -g performance
elif [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
    for CPUFREQ in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$CPUFREQ"
    done
fi

# Disable visual effects - GNOME/KDE specific (placeholder)
echo "You may need to disable animations manually depending on your DE."

# Disable transparency effects - GNOME example
gsettings set org.gnome.desktop.interface enable-animations false 2>/dev/null
gsettings set org.gnome.desktop.interface gtk-enable-animations false 2>/dev/null

# Clean temporary files
echo "Cleaning temporary files..."
rm -rf /tmp/* ~/.cache/* 2>/dev/null

# Disable startup applications (GNOME autostart)
echo "Disabling user startup applications..."
rm -f ~/.config/autostart/*

# Stop and disable non-essential services (example services)
echo "Stopping non-essential services..."
for service in bluetooth cups avahi-daemon; do
    systemctl stop $service 2>/dev/null
    systemctl disable $service 2>/dev/null
done

# Network optimization - Clear DNS cache (varies by system)
echo "Flushing DNS cache..."
if systemctl is-active systemd-resolved &>/dev/null; then
    systemd-resolve --flush-caches
elif command -v resolvectl &>/dev/null; then
    resolvectl flush-caches
fi

# Reset networking stack (basic)
echo "Restarting networking service..."
systemctl restart NetworkManager 2>/dev/null || systemctl restart networking 2>/dev/null

# Disable background services (example)
echo "Disabling background apps..."
systemctl mask systemd-backlight@backlight:acpi_video0.service 2>/dev/null

# Disable telemetry services
echo "Disabling telemetry (if applicable)..."
systemctl disable apport.service 2>/dev/null
systemctl stop apport.service 2>/dev/null

echo "Optimization complete!"
echo "Some changes may require a reboot to take full effect."
