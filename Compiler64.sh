#!/bin/bash

# Check if dialog is installed
if ! command -v dialog &> /dev/null; then
  echo "Error: dialog is not installed. Please install it (e.g., 'brew install dialog')."
  exit 1
fi

# --- Function: Detect ROM Format ---
detect_rom_format() {
  local file="$1"
  # Use head, xxd, and awk to analyze the header
  # Example (this needs refinement - it's just a starting point):
  local header=$(head -c 4 "$file" | xxd -p)
  # Big-endian usually starts with 80371240
  if [[ "$header" == "80371240" ]]; then
    echo "z64"  # Big-endian
  elif [[ "$header" == "37804012" ]]; then
    echo "v64" # Byteswapped
  elif [[ "$header" == "40123780" ]]; then
      echo "n64_wordswapped" #Rare case
  else
    echo "unknown"
  fi
}

# --- File Selection ---
selected_file=$(dialog --stdout --title "Select N64 ROM" --fselect "$HOME" 15 50)

if [[ -z "$selected_file" ]]; then
  echo "No file selected. Exiting."
  exit 1
fi

# --- Detect Format ---
rom_format=$(detect_rom_format "$selected_file")

# --- Conversion Options (Example: Force .z64) ---
force_z64=false
if dialog --stdout --yesno "Force conversion to .z64 format?" 10 40; then
  force_z64=true
fi

# --- Output File Name ---
output_file="${selected_file%.*}.z64" # Default to .z64

# --- Perform Conversion (using dd) ---
case "$rom_format" in
  "z64")
    if $force_z64 ; then
        dialog --msgbox "ROM is already in z64 format, copying..." 10 60
        cp "$selected_file" "$output_file"
    else
        dialog --msgbox "ROM is already in z64 format. No changes needed." 10 60
        exit 0
    fi
    ;;
  "v64")
     dialog --infobox "Converting from v64 to z64..." 10 60
     dd if="$selected_file" of="$output_file" bs=2 conv=swab
    ;;
    "n64_wordswapped")
        dialog --infobox "Converting from n64 (word-swapped) to z64..." 10 60;
        # Word swapping.  We'll swap every 4 bytes (two 16-bit words)
        dd if="$selected_file" of="$output_file" bs=4 conv=swab
    ;;
  "unknown")
    dialog --msgbox "Unknown ROM format. Cannot convert." 10 40
    exit 1
    ;;
esac

# --- Display Result ---
dialog --msgbox "Conversion complete. Output file: $output_file" 10 60

exit 0
