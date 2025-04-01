# test.py
import os, sys, json, shutil, zipfile, threading
import urllib.request
import urllib.error  # Import for handling HTTP errors
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re # Import re for modpack parsing
import subprocess # Standard import instead of __import__
import uuid as uuidlib # For offline UUID generation

# --- Constants ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" # Common User-Agent

# --- Directory Setup ---
if os.name == 'nt':
    mc_dir = os.path.join(os.getenv('APPDATA', ''), ".minecraft")
elif sys.platform == 'darwin':
    mc_dir = os.path.expanduser("~/Library/Application Support/minecraft")
else:
    mc_dir = os.path.expanduser("~/.minecraft")
if not os.path.isdir(mc_dir):
    os.makedirs(mc_dir, exist_ok=True)

VERSIONS_DIR = os.path.join(mc_dir, "versions")
ASSETS_DIR = os.path.join(mc_dir, "assets")
MODPACKS_DIR = os.path.join(mc_dir, "modpacks") # For storing extracted modpack contents
LIBRARIES_DIR = os.path.join(mc_dir, "libraries") # Explicit library dir

os.makedirs(VERSIONS_DIR, exist_ok=True)
os.makedirs(MODPACKS_DIR, exist_ok=True)
os.makedirs(os.path.join(ASSETS_DIR, "indexes"), exist_ok=True)
os.makedirs(os.path.join(ASSETS_DIR, "objects"), exist_ok=True)
os.makedirs(LIBRARIES_DIR, exist_ok=True)

# URLs
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
ASSET_BASE_URL = "http://resources.download.minecraft.net/"
LIBRARIES_BASE_URL = "https://libraries.minecraft.net/"
FORGE_MAVEN_URL = "https://maven.minecraftforge.net/"
TLMODS_BASE_URL = "https://tlmods.org"

# --- Global Variable (used as temporary fix in original, now passed as parameter) ---
# REMOVED: global custom_game_dir (will pass game_dir explicitly)

# --- Account Management ---
accounts = []
accounts_file = os.path.join(mc_dir, "launcher_accounts.json") # Changed name slightly
if os.path.isfile(accounts_file):
    try:
        with open(accounts_file, 'r') as f:
            accounts = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {accounts_file}. Starting with empty accounts.")
        accounts = []
    except Exception as e:
        print(f"Warning: Error loading accounts: {e}")
        accounts = []

def save_accounts():
    try:
        with open(accounts_file, 'w') as f:
            json.dump(accounts, f, indent=4)
    except Exception as e:
        print(f"Error saving accounts: {e}")
        # Optionally show error to user via messagebox if GUI is available

def add_account(acc_type, email_username, password_token=None):
    """Adds/updates an account. Note: Storing TLauncher password is insecure."""
    if not email_username: return # Prevent adding empty username

    # Generate UUID for offline mode consistently
    offline_uuid = str(uuidlib.uuid3(uuidlib.NAMESPACE_DNS, email_username))

    if acc_type == "tlauncher":
        # NOTE: Storing password like this is insecure. Real launchers use tokens.
        acc = {"type": "tlauncher", "username": email_username, "password": password_token or "", "uuid": offline_uuid, "token": "null"} # Use offline UUID, TLauncher often uses this approach offline
    elif acc_type == "offline":
        acc = {"type": "offline", "username": email_username, "uuid": offline_uuid, "token": "null"}
    elif acc_type == "microsoft":
        # Placeholder: Real MS auth needs complex OAuth2 flow. Token here is assumed pre-acquired.
        # UUID would normally come from auth response. Using offline UUID as fallback.
        acc = {"type": "microsoft", "username": email_username, "uuid": offline_uuid, "token": (password_token or "0")} # Use "0" or similar for invalid/demo token
    else:
        print(f"Unknown account type: {acc_type}")
        return

    # Check if account exists (by type and username) and update, otherwise add
    found = False
    for i, existing_acc in enumerate(accounts):
        if existing_acc.get("type") == acc_type and existing_acc.get("username") == email_username:
            accounts[i] = acc # Update existing
            found = True
            break
    if not found:
        accounts.append(acc)

    save_accounts()
    print(f"Account '{email_username}' ({acc_type}) added/updated.")


# --- Download Helper ---
def download_file(url, dest_path, description="file"):
    """Download file from url to dest_path with User-Agent and better error handling."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        print(f"Downloading {description}: {os.path.basename(dest_path)} from {url}")
        with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        print(f"Finished downloading {os.path.basename(dest_path)}")
    except urllib.error.HTTPError as e:
        # Provide more specific HTTP error feedback
        raise Exception(f"Failed to download {description} from {url}. HTTP Error: {e.code} {e.reason}") from e
    except Exception as e:
        # Catch other potential errors (network, file system, etc.)
        raise Exception(f"Failed to download {description} from {url}. Error: {e}") from e


# --- Version Manifest Loading ---
version_manifest_path = os.path.join(mc_dir, "version_manifest_v2.json") # Use v2 if available, has more info
if not os.path.isfile(version_manifest_path):
    try:
        # Try v2 first
        download_file("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json", version_manifest_path, "version manifest v2")
    except Exception:
        print("Failed to download v2 manifest, falling back to v1.")
        try:
            # Fallback to v1
            version_manifest_path = os.path.join(mc_dir, "version_manifest.json")
            download_file(VERSION_MANIFEST_URL, version_manifest_path, "version manifest v1")
        except Exception as e:
            messagebox.showerror("Fatal Error", f"Could not download Minecraft version manifest: {e}")
            sys.exit(1) # Exit if we can't get any manifest

try:
    with open(version_manifest_path, 'r') as f:
        version_manifest = json.load(f)
except Exception as e:
    messagebox.showerror("Fatal Error", f"Could not read Minecraft version manifest: {e}")
    sys.exit(1)

# Build list of all versions (id and URL)
all_versions = {v['id']: v['url'] for v in version_manifest['versions']}


# --- Minecraft Installation Logic ---
def install_version(version_id, status_callback=None):
    """Ensure the given Minecraft version (version_id) and its dependencies are installed."""
    if status_callback: status_callback(f"Checking version: {version_id}...")

    version_folder = os.path.join(VERSIONS_DIR, version_id)
    version_json_path = os.path.join(version_folder, f"{version_id}.json")
    version_jar_path = os.path.join(version_folder, f"{version_id}.jar")

    # Check if primary JSON exists, if not, download it
    if not os.path.isfile(version_json_path):
        if version_id not in all_versions:
            # Maybe it's a custom JSON (like Forge) already present but jar missing?
            # Or maybe it's truly unknown. Let's assume unknown for now.
            raise Exception(f"Version '{version_id}' not found in Mojang manifest.")

        version_url = all_versions[version_id]
        os.makedirs(version_folder, exist_ok=True)
        if status_callback: status_callback(f"Downloading version JSON for {version_id}...")
        download_file(version_url, version_json_path, f"version JSON ({version_id})")
    else:
        print(f"Version JSON for {version_id} already exists.")

    # Load version JSON
    try:
        with open(version_json_path, 'r') as f:
            version_data = json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load version JSON for {version_id}: {e}")

    # --- Handle Inheritance (e.g., Forge > 1.12) ---
    parent_id = version_data.get("inheritsFrom")
    parent_data = {}
    if parent_id:
        if status_callback: status_callback(f"Version {version_id} inherits from {parent_id}. Installing parent...")
        try:
            # Recursively install parent. Pass the callback down.
            install_version(parent_id, status_callback)
            parent_json_path = os.path.join(VERSIONS_DIR, parent_id, f"{parent_id}.json")
            with open(parent_json_path, 'r') as pf:
                parent_data = json.load(pf)
        except Exception as e:
            raise Exception(f"Failed to install parent version {parent_id}: {e}")

    # --- Download Client JAR ---
    client_info = version_data.get("downloads", {}).get("client")
    if client_info and not os.path.isfile(version_jar_path):
        client_url = client_info.get("url")
        if client_url:
            if status_callback: status_callback(f"Downloading client JAR for {version_id}...")
            download_file(client_url, version_jar_path, f"client JAR ({version_id})")
        else:
            print(f"Warning: No client JAR URL found for {version_id}")
    elif not os.path.isfile(version_jar_path) and not parent_id:
         # Only raise error if it's missing AND it's not an inherited profile (which might not have its own jar)
         print(f"Warning: Client JAR for {version_id} is missing and no download info found.")


    # --- Combine Libraries (Current + Parent) ---
    libraries = version_data.get("libraries", []) + parent_data.get("libraries", [])

    # --- Download Libraries ---
    if status_callback: status_callback(f"Checking libraries for {version_id}...")
    total_libs = len(libraries)
    for i, lib in enumerate(libraries):
        # Check rules (OS, architecture)
        rules = lib.get("rules", [])
        allowed = True # Default to allow if no rules
        if rules:
            allowed = False # If rules exist, default to deny, must have an allow match
            for rule in rules:
                action = rule.get("action")
                os_rule = rule.get("os", {})
                # Arch rule currently ignored for simplicity
                if action == "allow":
                    if not os_rule: # Allow if no OS specified
                        allowed = True
                        break
                    if os_rule.get("name") == sys.platform or \
                       (sys.platform == 'win32' and os_rule.get("name") == 'windows') or \
                       (sys.platform == 'darwin' and os_rule.get("name") == 'osx') or \
                       (sys.platform.startswith('linux') and os_rule.get("name") == 'linux'):
                        allowed = True
                        break
                elif action == "disallow":
                     if not os_rule: # Disallow if no OS specified
                        allowed = False
                        break
                     if os_rule.get("name") == sys.platform or \
                       (sys.platform == 'win32' and os_rule.get("name") == 'windows') or \
                       (sys.platform == 'darwin' and os_rule.get("name") == 'osx') or \
                       (sys.platform.startswith('linux') and os_rule.get("name") == 'linux'):
                        allowed = False
                        break

        if not allowed:
            # print(f"Skipping library (rule mismatch): {lib.get('name')}")
            continue

        # Download main artifact
        artifact = lib.get("downloads", {}).get("artifact")
        if artifact and artifact.get("path"):
            lib_path = os.path.join(LIBRARIES_DIR, artifact["path"])
            if not os.path.isfile(lib_path):
                 # Construct URL: Use explicitly provided URL, fallback to Mojang's Maven, fallback to Forge Maven for forge libs
                lib_url = artifact.get("url")
                if not lib_url:
                    # Heuristic: if name contains 'forge', try forge maven first
                    if 'forge' in lib.get('name','').lower():
                        lib_url = FORGE_MAVEN_URL + artifact["path"]
                    else:
                        lib_url = LIBRARIES_BASE_URL + artifact["path"]

                if status_callback: status_callback(f"Downloading library {i+1}/{total_libs}: {os.path.basename(lib_path)}")
                try:
                    download_file(lib_url, lib_path, f"library ({os.path.basename(lib_path)})")
                except Exception as e:
                    print(f"Warning: Failed to download library {lib.get('name')}: {e}. Trying next source if available.")
                    # Fallback attempt for forge/non-forge
                    if LIBRARIES_BASE_URL in lib_url:
                         fallback_url = FORGE_MAVEN_URL + artifact["path"]
                         print(f"Trying Forge Maven: {fallback_url}")
                         try:
                             download_file(fallback_url, lib_path, f"library ({os.path.basename(lib_path)})")
                         except Exception as e2:
                             print(f"Fallback download failed: {e2}")
                    elif FORGE_MAVEN_URL in lib_url:
                         fallback_url = LIBRARIES_BASE_URL + artifact["path"]
                         print(f"Trying Mojang Libraries: {fallback_url}")
                         try:
                             download_file(fallback_url, lib_path, f"library ({os.path.basename(lib_path)})")
                         except Exception as e2:
                             print(f"Fallback download failed: {e2}")


        # Download natives
        natives_info = lib.get("natives")
        classifiers = lib.get("downloads", {}).get("classifiers", {})
        if natives_info and classifiers:
            os_key_map = {'win32': 'windows', 'darwin': 'osx', 'linux': 'linux'}
            native_os = os_key_map.get(sys.platform)
            # Handle arch if needed, e.g., natives_info.get(native_os).replace("${arch}", "64")
            arch = '64' # Assume 64-bit for simplicity
            native_key = natives_info.get(native_os, '').replace("${arch}", arch)

            if native_key and native_key in classifiers:
                native_artifact = classifiers[native_key]
                if native_artifact.get("path"):
                    native_path = os.path.join(LIBRARIES_DIR, native_artifact["path"])
                    if not os.path.isfile(native_path):
                        native_url = native_artifact.get("url")
                        if not native_url:
                             if 'forge' in lib.get('name','').lower():
                                 native_url = FORGE_MAVEN_URL + native_artifact["path"]
                             else:
                                 native_url = LIBRARIES_BASE_URL + native_artifact["path"]

                        if status_callback: status_callback(f"Downloading native library {i+1}/{total_libs}: {os.path.basename(native_path)}")
                        try:
                            download_file(native_url, native_path, f"native library ({os.path.basename(native_path)})")
                        except Exception as e:
                            print(f"Warning: Failed to download native {lib.get('name')}: {e}") # Natives are often optional if download fails

                    # Extract natives
                    natives_dir = os.path.join(version_folder, "natives")
                    os.makedirs(natives_dir, exist_ok=True)
                    try:
                        if os.path.isfile(native_path): # Check again before extracting
                            with zipfile.ZipFile(native_path, 'r') as zf:
                                # Define extraction exclusions
                                exclude_prefixes = lib.get("extract", {}).get("exclude", [])
                                for member in zf.namelist():
                                    # Skip excluded files/folders and anything in META-INF
                                    if member.startswith("META-INF/") or any(member.startswith(prefix) for prefix in exclude_prefixes):
                                        continue
                                    # Only extract if it's a file (avoids extracting empty dirs)
                                    if not member.endswith('/'):
                                       zf.extract(member, natives_dir)
                            # print(f"Extracted natives from {os.path.basename(native_path)} to {natives_dir}") # Verbose logging
                    except zipfile.BadZipFile:
                        print(f"Warning: Could not extract natives from corrupted file: {native_path}")
                    except Exception as e:
                        print(f"Warning: Failed to extract natives from {native_path}: {e}")

    # --- Download Assets ---
    asset_index_info = version_data.get("assetIndex") or parent_data.get("assetIndex")
    if asset_index_info and asset_index_info.get("id") and asset_index_info.get("url"):
        idx_id = asset_index_info["id"]
        idx_url = asset_index_info["url"]
        idx_dest = os.path.join(ASSETS_DIR, "indexes", f"{idx_id}.json")

        if not os.path.isfile(idx_dest):
            if status_callback: status_callback(f"Downloading asset index {idx_id}...")
            download_file(idx_url, idx_dest, f"asset index ({idx_id})")

        # Load asset index and download objects
        try:
            with open(idx_dest, 'r') as f:
                idx_data = json.load(f)

            if idx_data and "objects" in idx_data:
                if status_callback: status_callback(f"Checking assets for index {idx_id}...")
                total_assets = len(idx_data["objects"])
                assets_downloaded = 0
                for i, (asset_name, info) in enumerate(idx_data["objects"].items()):
                    hash_val = info.get("hash")
                    if hash_val:
                        subdir = hash_val[:2]
                        asset_path = os.path.join(ASSETS_DIR, "objects", subdir, hash_val)
                        if not os.path.isfile(asset_path):
                            assets_downloaded += 1
                            if status_callback: status_callback(f"Downloading asset {assets_downloaded}/{total_assets}: {asset_name}")
                            asset_url = ASSET_BASE_URL + f"{subdir}/{hash_val}"
                            download_file(asset_url, asset_path, f"asset ({hash_val[:8]})")

        except FileNotFoundError:
             print(f"Warning: Asset index file not found after download attempt: {idx_dest}")
        except json.JSONDecodeError:
             print(f"Warning: Could not parse asset index file: {idx_dest}")
        except Exception as e:
             print(f"Warning: Error processing assets for index {idx_id}: {e}")

    else:
        print(f"Warning: No valid asset index information found for version {version_id}")

    # --- TLauncher Skin Patch (Optional, might not work reliably) ---
    # This modifies the version JSON. It's unclear if modern TLauncher still uses this.
    try:
        with open(version_json_path, 'r+') as vf:
            data = json.load(vf)
            if not data.get("skinVersion", False): # Only write if not already true
                data["skinVersion"] = True
                vf.seek(0)
                json.dump(data, vf, indent=4)
                vf.truncate()
                print(f"Patched {version_id}.json with skinVersion=true")
    except Exception as e:
        print(f"Warning: Could not set skinVersion in {version_id}.json - {e}")

    if status_callback: status_callback(f"Version {version_id} installation complete.")


# --- Modpack Installation Logic ---
def install_modpack(modpack_slug, status_callback=None):
    """Download and extract a modpack from TLMods, returning the version ID and game directory."""
    if status_callback: status_callback(f"Fetching modpack info for '{modpack_slug}'...")

    page_url = f"{TLMODS_BASE_URL}/en/modpacks/{modpack_slug}/"
    req = urllib.request.Request(page_url, headers={'User-Agent': USER_AGENT})
    html = ""
    try:
        with urllib.request.urlopen(req) as resp:
            # Read response code
            if resp.getcode() == 200:
                 html = resp.read().decode('utf-8', errors='ignore')
            else:
                 raise Exception(f"Failed to fetch modpack page {page_url}. Status code: {resp.getcode()}")
    except urllib.error.HTTPError as e:
         raise Exception(f"Failed to fetch modpack page {page_url}. HTTP Error: {e.code} {e.reason}") from e
    except Exception as e:
        raise Exception(f"Failed to fetch modpack page {page_url}: {e}")

    # Find download link (prefer Release, fallback to first)
    # Regex updated slightly for robustness
    links = re.findall(r'href="(/files/modpacks/[^"?]+\.zip)"', html)
    if not links:
        raise Exception(f"No modpack download links found on page for '{modpack_slug}'. Does the page exist?")

    download_link = None
    for link in links:
        # Case-insensitive search for "release" in the link path
        if "release" in link.lower():
            download_link = link
            break
    if not download_link:
        download_link = links[0] # Fallback to the first link found

    download_url = TLMODS_BASE_URL + download_link
    tmp_zip = os.path.join(mc_dir, f"temp_{modpack_slug}.zip") # Use temp name

    if status_callback: status_callback(f"Downloading modpack '{modpack_slug}'...")
    try:
        download_file(download_url, tmp_zip, f"modpack zip ({modpack_slug})")
    except Exception as e:
        if os.path.exists(tmp_zip): os.remove(tmp_zip) # Clean up partial download
        raise Exception(f"Failed to download modpack zip: {e}")


    # Extract modpack
    target_dir = os.path.join(MODPACKS_DIR, modpack_slug)
    if status_callback: status_callback(f"Extracting modpack '{modpack_slug}'...")
    try:
        # Clean old directory before extracting
        if os.path.isdir(target_dir):
            print(f"Removing existing modpack directory: {target_dir}")
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)

        with zipfile.ZipFile(tmp_zip, 'r') as zf:
            zf.extractall(target_dir)
        print(f"Modpack extracted to {target_dir}")
    except zipfile.BadZipFile:
        raise Exception("Failed to extract modpack: Downloaded file is not a valid ZIP archive.")
    except Exception as e:
         raise Exception(f"Failed to extract modpack: {e}")
    finally:
        if os.path.exists(tmp_zip):
            os.remove(tmp_zip) # Clean up downloaded zip

    # --- Determine Launch Version ---
    if status_callback: status_callback("Determining launch version...")
    launch_version = None
    base_mc_version = None # To store the vanilla MC version needed

    # 1. Check for included 'versions' folder in the extracted modpack
    mod_versions_dir = os.path.join(target_dir, "versions")
    extracted_version_id = None
    if os.path.isdir(mod_versions_dir):
        print("Found 'versions' folder in modpack.")
        for item in os.listdir(mod_versions_dir):
            src = os.path.join(mod_versions_dir, item)
            dest = os.path.join(VERSIONS_DIR, item)
            if os.path.isdir(src): # Expecting a version folder
                print(f"Moving version '{item}' from modpack to main versions directory.")
                if os.path.isdir(dest): shutil.rmtree(dest) # Overwrite if exists
                shutil.move(src, dest)
                # Assume the first *moved* version folder is the one to use
                if extracted_version_id is None:
                    extracted_version_id = item
            # Ignore loose files in versions folder
        # If a version was moved, use it.
        if extracted_version_id:
             launch_version = extracted_version_id
             # We still need to run install_version on it to ensure its own dependencies (libs, assets) are met
             print(f"Modpack provided version: {launch_version}. Ensuring its dependencies...")
             install_version(launch_version, status_callback) # Install dependencies for the extracted version
        # Clean up the now empty mod_versions_dir from target
        try:
             os.rmdir(mod_versions_dir)
        except OSError:
             pass # Ignore if not empty or doesn't exist

    # 2. If no version folder found, parse manifest.json (CurseForge format)
    if not launch_version:
        manifest_path = os.path.join(target_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            print("Found manifest.json, attempting to parse...")
            try:
                with open(manifest_path, 'r') as mf:
                    manifest = json.load(mf)

                base_mc_version = manifest.get("minecraft", {}).get("version")
                mod_loaders = manifest.get("minecraft", {}).get("modLoaders", [])

                if base_mc_version:
                     print(f"Manifest specifies Minecraft version: {base_mc_version}")
                     # Ensure base MC version is installed *first*
                     install_version(base_mc_version, status_callback)

                     loader_type = None
                     loader_version = None
                     if mod_loaders:
                         # Find primary loader (usually Forge or Fabric)
                         primary_loader = next((l for l in mod_loaders if l.get("primary", False)), mod_loaders[0])
                         loader_id = primary_loader.get("id", "") # e.g., "forge-47.1.3" or "fabric-0.14.21"
                         print(f"Manifest specifies loader: {loader_id}")

                         if loader_id.startswith("forge-"):
                             loader_type = "forge"
                             loader_version = loader_id.split("forge-", 1)[1]
                         elif loader_id.startswith("fabric-"):
                              loader_type = "fabric"
                              loader_version = loader_id.split("fabric-", 1)[1]
                              print("Fabric installation from modpack not yet fully supported by this script.") # TODO: Add Fabric support if needed
                              # Fabric requires installing the Fabric loader itself, similar to Forge.

                         # --- Handle Forge Installation ---
                         if loader_type == "forge" and loader_version:
                             forge_version_id = f"{base_mc_version}-forge-{loader_version}" # Adjusted format
                             forge_dir = os.path.join(VERSIONS_DIR, forge_version_id)
                             forge_json_path = os.path.join(forge_dir, f"{forge_version_id}.json")

                             if not os.path.isfile(forge_json_path):
                                 print(f"Forge profile '{forge_version_id}' not found. Attempting to install Forge...")
                                 if status_callback: status_callback(f"Downloading Forge {loader_version} installer...")
                                 # Construct installer URL (common pattern)
                                 installer_url = f"{FORGE_MAVEN_URL}net/minecraftforge/forge/{base_mc_version}-{loader_version}/forge-{base_mc_version}-{loader_version}-installer.jar"
                                 installer_path = os.path.join(mc_dir, f"forge-installer-{base_mc_version}-{loader_version}.jar")

                                 try:
                                     download_file(installer_url, installer_path, f"Forge {loader_version} installer")

                                     # Extract version.json and libraries from installer JAR
                                     if status_callback: status_callback(f"Extracting Forge {loader_version} profile...")
                                     with zipfile.ZipFile(installer_path, 'r') as zf:
                                         # Extract version.json (often named install_profile.json or version.json inside)
                                         profile_extracted = False
                                         for name in zf.namelist():
                                             if name == "version.json" or name == "install_profile.json":
                                                 os.makedirs(forge_dir, exist_ok=True)
                                                 zf.extract(name, forge_dir)
                                                 # Rename install_profile.json if needed
                                                 extracted_json_path = os.path.join(forge_dir, name)
                                                 if name == "install_profile.json":
                                                     # Need to parse install_profile, get "versionInfo" and save *that* as version_id.json
                                                     with open(extracted_json_path, 'r') as ipf:
                                                         install_profile = json.load(ipf)
                                                     version_info = install_profile.get("versionInfo")
                                                     if version_info:
                                                         with open(forge_json_path, 'w') as vjf:
                                                             json.dump(version_info, vjf, indent=4)
                                                         profile_extracted = True
                                                     os.remove(extracted_json_path) # Remove the install_profile.json

                                                 elif name == "version.json":
                                                      shutil.move(extracted_json_path, forge_json_path)
                                                      profile_extracted = True
                                                 print(f"Extracted Forge profile JSON to {forge_json_path}")
                                                 break # Found the profile

                                         if not profile_extracted:
                                             print("Warning: Could not find version.json or install_profile.json in Forge installer.")

                                         # Extract libraries (usually in 'maven' folder within installer)
                                         print("Extracting libraries from Forge installer...")
                                         for member in zf.namelist():
                                             # Adjust path for libraries inside the installer zip
                                             if member.startswith("maven/"):
                                                  # Relative path inside the 'maven' dir
                                                  rel_path = member[len("maven/"):]
                                                  if rel_path and not rel_path.endswith('/'): # Is a file
                                                      dest_path = os.path.join(LIBRARIES_DIR, rel_path)
                                                      os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                                      # Extract file content
                                                      with open(dest_path, 'wb') as fout:
                                                          fout.write(zf.read(member))
                                             elif member.startswith("libraries/"): # Older installers might use this path
                                                  rel_path = member[len("libraries/"):]
                                                  if rel_path and not rel_path.endswith('/'):
                                                      dest_path = os.path.join(LIBRARIES_DIR, rel_path)
                                                      os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                                      with open(dest_path, 'wb') as fout:
                                                          fout.write(zf.read(member))


                                 except zipfile.BadZipFile:
                                     print(f"Error: Forge installer {installer_path} seems corrupted.")
                                 except Exception as e:
                                     print(f"Error installing Forge: {e}")
                                 finally:
                                     # Clean up installer
                                     if os.path.isfile(installer_path):
                                         os.remove(installer_path)

                             # If Forge profile JSON now exists, ensure its dependencies are met
                             if os.path.isfile(forge_json_path):
                                 print(f"Forge profile '{forge_version_id}' found. Ensuring its dependencies...")
                                 install_version(forge_version_id, status_callback)
                                 launch_version = forge_version_id
                             else:
                                 print(f"Warning: Failed to install Forge profile '{forge_version_id}'. Falling back.")

            except json.JSONDecodeError:
                print("Warning: Could not parse manifest.json.")
            except Exception as e:
                print(f"Error processing manifest.json: {e}")

    # 3. Fallback: If no version determined yet, try inferring base MC version from TLMods page (less reliable)
    if not launch_version and not base_mc_version:
         print("No version info from modpack files or manifest. Trying to infer from TLMods page...")
         # Regex to find "Game Version: X.Y.Z" on the page
         m = re.search(r'Game Version:\s*<span[^>]*>([0-9]+\.[0-9]+(\.[0-9]+)?)\s*<', html, re.IGNORECASE)
         if m:
             base_mc_version = m.group(1)
             print(f"Inferred base Minecraft version from page: {base_mc_version}")
             # Install the inferred base version
             install_version(base_mc_version, status_callback)
             # Set launch version to the base version (no loader info available here)
             launch_version = base_mc_version
         else:
              print("Warning: Could not determine base Minecraft version from TLMods page.")

    # 4. Final Decision: Use determined launch_version, or fallback to base_mc_version if loader install failed
    if not launch_version:
        if base_mc_version:
             print(f"Warning: Could not determine or install specific mod loader version. Launching with base Minecraft version: {base_mc_version}")
             launch_version = base_mc_version
        else:
             raise Exception("Could not determine any Minecraft version to launch for this modpack.")

    if status_callback: status_callback(f"Modpack setup complete. Launch version: {launch_version}")
    return launch_version, target_dir # Return version ID and the modpack's specific game directory


# --- Game Launch Logic ---
def launch_game(version_id, account, ram_mb=1024, java_path="java", game_dir=None, server_ip=None, port=None, status_callback=None):
    """Constructs and executes the Minecraft launch command."""
    if status_callback: status_callback(f"Preparing to launch {version_id}...")

    # Use provided game_dir or default .minecraft
    effective_game_dir = game_dir if game_dir and os.path.isdir(game_dir) else mc_dir
    print(f"Using game directory: {effective_game_dir}")

    # Ensure the target version and its dependencies are fully installed
    try:
        install_version(version_id, status_callback)
    except Exception as e:
        raise Exception(f"Failed to ensure version '{version_id}' is installed before launch: {e}")

    # Load the final version JSON data (could be base MC, Forge, Fabric, etc.)
    version_folder = os.path.join(VERSIONS_DIR, version_id)
    version_json_path = os.path.join(version_folder, f"{version_id}.json")
    if not os.path.isfile(version_json_path):
        raise Exception(f"Launch aborted: Version JSON not found for '{version_id}' at {version_json_path}")

    with open(version_json_path, 'r') as f:
        vdata = json.load(f)

    # --- Gather launch arguments and classpath ---
    main_class = vdata.get("mainClass")
    jvm_args = []
    game_args = []
    classpath = set() # Use a set to avoid duplicates

    # Handle inheritance (merge args and libs) - Simplified merge
    parent_data = {}
    inherits_from = vdata.get("inheritsFrom")
    if inherits_from:
        try:
            parent_json_path = os.path.join(VERSIONS_DIR, inherits_from, f"{inherits_from}.json")
            with open(parent_json_path, 'r') as pf:
                parent_data = json.load(pf)
            # If main class is missing in child, inherit from parent
            if not main_class:
                main_class = parent_data.get("mainClass")
        except Exception as e:
            print(f"Warning: Could not load parent version {inherits_from}: {e}. Proceeding without parent data.")


    # Combine libraries from self and parent
    all_libraries = vdata.get("libraries", []) + parent_data.get("libraries", [])

    # Process libraries for classpath
    natives_dir_absolute = os.path.abspath(os.path.join(version_folder, "natives"))
    for lib in all_libraries:
        # Rules check (simplified, assumes install_version handled skipping)
        rules = lib.get("rules", [])
        allowed = True # Assume allowed if it passed install_version check
        # Re-check rules lightly (mainly for OS)
        if rules:
            allowed = False
            for rule in rules:
                action = rule.get("action")
                os_rule = rule.get("os", {})
                if action == "allow":
                    if not os_rule or os_rule.get("name") == sys.platform or \
                       (sys.platform == 'win32' and os_rule.get("name") == 'windows') or \
                       (sys.platform == 'darwin' and os_rule.get("name") == 'osx') or \
                       (sys.platform.startswith('linux') and os_rule.get("name") == 'linux'):
                        allowed = True; break
                elif action == "disallow":
                    if not os_rule or os_rule.get("name") == sys.platform or \
                       (sys.platform == 'win32' and os_rule.get("name") == 'windows') or \
                       (sys.platform == 'darwin' and os_rule.get("name") == 'osx') or \
                       (sys.platform.startswith('linux') and os_rule.get("name") == 'linux'):
                         allowed = False; break
            if not allowed: continue

        # Add artifact to classpath
        artifact = lib.get("downloads", {}).get("artifact")
        if artifact and artifact.get("path"):
            lib_file = os.path.join(LIBRARIES_DIR, artifact["path"])
            if os.path.isfile(lib_file):
                classpath.add(os.path.abspath(lib_file))
            else:
                print(f"Warning: Required library file missing: {lib_file}")


    # Add the version JAR itself to classpath
    version_jar_path = os.path.join(version_folder, f"{version_id}.jar")
    if os.path.isfile(version_jar_path):
        classpath.add(os.path.abspath(version_jar_path))
    else:
        # If jar is missing, maybe parent has it? Check parent jar
        if inherits_from:
             parent_jar_path = os.path.join(VERSIONS_DIR, inherits_from, f"{inherits_from}.jar")
             if os.path.isfile(parent_jar_path):
                  classpath.add(os.path.abspath(parent_jar_path))
             else:
                  print(f"Warning: Main version JAR ({version_id}.jar) and parent JAR ({inherits_from}.jar) are missing!")
        else:
             print(f"Warning: Main version JAR is missing: {version_jar_path}")


    # --- Process Arguments (JVM and Game) ---
    # Combine args from self and parent, handling modern 'arguments' dict and legacy 'minecraftArguments' string
    args_data = vdata.get("arguments", {})
    parent_args_data = parent_data.get("arguments", {})

    # JVM Arguments (Combine, parent first)
    raw_jvm_args = parent_args_data.get("jvm", []) + args_data.get("jvm", [])
    # Game Arguments (Combine, parent first)
    raw_game_args = parent_args_data.get("game", []) + args_data.get("game", [])

    # Handle legacy format if modern format is absent
    if not raw_game_args and (vdata.get("minecraftArguments") or parent_data.get("minecraftArguments")):
        legacy_args_str = vdata.get("minecraftArguments") or parent_data.get("minecraftArguments", "")
        raw_game_args = legacy_args_str.split()
        print("Using legacy minecraftArguments format.")

    # --- Argument Placeholders ---
    asset_index_id = (vdata.get("assetIndex") or parent_data.get("assetIndex", {})).get("id", "legacy") # Default for very old versions
    auth_uuid = account.get("uuid", "invalid-uuid") # Should be set by add_account
    auth_token = account.get("token", "invalid-token") # Should be set by add_account or fetched via auth flow

    # For offline/tlauncher, ensure token is '0' or 'null' as expected by some mods/plugins
    if account.get("type") in ["offline", "tlauncher"]:
        auth_token = "0" # Common practice for offline mode

    replacements = {
        "${auth_player_name}": account.get("username", "Player"),
        "${version_name}": version_id,
        "${game_directory}": effective_game_dir,
        "${assets_root}": os.path.abspath(ASSETS_DIR),
        "${assets_index_name}": asset_index_id,
        "${auth_uuid}": auth_uuid,
        "${auth_access_token}": auth_token,
        "${user_type}": "msa" if account.get("type") == "microsoft" else "legacy", # Mojang accounts are effectively legacy now
        "${version_type}": vdata.get("type", "release"), # e.g., release, snapshot
        # Classpath related (handled separately but placeholders might exist)
        "${library_directory}": os.path.abspath(LIBRARIES_DIR),
        "${classpath_separator}": os.pathsep,
        "${launcher_name}": "CatClient",
        "${launcher_version}": "1.1",
        # Natives path (crucial for LWJGL etc.)
        "${natives_directory}": natives_dir_absolute,
    }

    # Process JVM Args
    # Start with defaults
    processed_jvm_args = [
        f"-Xmx{ram_mb}M",
        f"-Djava.library.path={natives_dir_absolute}", # Essential for natives
        # Maybe add modern GC flags? Depends on Java version used.
        # "-XX:+UseG1GC", "-XX:-UseAdaptiveSizePolicy", "-XX:MaxGCPauseMillis=200",
    ]
    for arg in raw_jvm_args:
        if isinstance(arg, str):
            # Replace placeholders within the string arg
            temp_arg = arg
            for key, value in replacements.items():
                temp_arg = temp_arg.replace(key, value)
            processed_jvm_args.append(temp_arg)
        elif isinstance(arg, dict) and "rules" in arg:
            # Apply rules (simplified check, assume OS match if here)
             include = True # Default include if rules present
             for rule in arg["rules"]:
                 action = rule.get("action")
                 os_rule = rule.get("os", {})
                 # Features rule ignored for simplicity
                 if action == "allow":
                    if not os_rule or os_rule.get("name") == sys.platform or \
                       (sys.platform == 'win32' and os_rule.get("name") == 'windows') or \
                       (sys.platform == 'darwin' and os_rule.get("name") == 'osx') or \
                       (sys.platform.startswith('linux') and os_rule.get("name") == 'linux'):
                        include = True; break # Allow if OS matches
                    else: include = False # Did not match allow rule's OS
                 elif action == "disallow":
                    if not os_rule or os_rule.get("name") == sys.platform or \
                       (sys.platform == 'win32' and os_rule.get("name") == 'windows') or \
                       (sys.platform == 'darwin' and os_rule.get("name") == 'osx') or \
                       (sys.platform.startswith('linux') and os_rule.get("name") == 'linux'):
                         include = False; break # Disallow if OS matches

             if include:
                  value = arg.get("value")
                  if isinstance(value, list):
                      for v in value:
                         temp_arg = v
                         for key, val in replacements.items(): temp_arg = temp_arg.replace(key, val)
                         processed_jvm_args.append(temp_arg)
                  elif isinstance(value, str):
                      temp_arg = value
                      for key, val in replacements.items(): temp_arg = temp_arg.replace(key, val)
                      processed_jvm_args.append(temp_arg)

    # Add Classpath to JVM Args
    cp_string = os.pathsep.join(list(classpath))
    processed_jvm_args.append("-cp")
    processed_jvm_args.append(cp_string)


    # Process Game Args
    processed_game_args = []
    for arg in raw_game_args:
        if isinstance(arg, str):
             temp_arg = arg
             for key, value in replacements.items():
                 temp_arg = temp_arg.replace(key, value)
             processed_game_args.append(temp_arg)
        elif isinstance(arg, dict) and "rules" in arg:
             # Apply rules similar to JVM args
             include = True
             # (Rule checking logic omitted for brevity, same as JVM args) ... Assume rules pass ...
             value = arg.get("value")
             if isinstance(value, list):
                 for v in value:
                     temp_arg = v
                     for key, val in replacements.items(): temp_arg = temp_arg.replace(key, val)
                     processed_game_args.append(temp_arg)
             elif isinstance(value, str):
                 temp_arg = value
                 for key, val in replacements.items(): temp_arg = temp_arg.replace(key, val)
                 processed_game_args.append(temp_arg)


    # Add server connection args if provided
    if server_ip:
        processed_game_args.append("--server")
        processed_game_args.append(server_ip)
        if port:
            processed_game_args.append("--port")
            processed_game_args.append(str(port))

    # --- Construct Final Command ---
    if not main_class:
        raise Exception("Launch aborted: Could not determine main class for the game.")

    command = [java_path] + processed_jvm_args + [main_class] + processed_game_args

    print("\n--- Launch Command ---")
    # print(" ".join(command)) # Careful, this might not be accurate if args have spaces
    print("Java Path:", command[0])
    print("JVM Args:", processed_jvm_args)
    print("Main Class:", main_class)
    print("Game Args:", processed_game_args)
    print("----------------------\n")

    # --- Execute ---
    if status_callback: status_callback(f"Launching Minecraft {version_id}...")
    try:
        # Launch in a way that doesn't block the launcher UI
        # Use Popen for non-blocking execution
        process = subprocess.Popen(command, cwd=effective_game_dir) # Set working directory
        print(f"Minecraft process started with PID: {process.pid}")
        if status_callback: status_callback(f"Minecraft {version_id} launched!")
        # We don't wait for the process to finish here
    except FileNotFoundError:
         raise Exception(f"Launch failed: Java executable not found at '{java_path}'. Please check Java Path setting.")
    except Exception as e:
        raise Exception(f"Launch failed: Could not start Minecraft process: {e}")


# --- GUI ---
class CatClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CatClient (TLauncher Edition) v1.1")
        self.root.geometry("600x550") # Increased size slightly

        # --- Account Frame ---
        acct_frame = ttk.LabelFrame(root, text="Accounts")
        acct_frame.pack(fill="x", padx=10, pady=5)

        self.acct_type_var = tk.StringVar(value="tlauncher")
        ttk.Radiobutton(acct_frame, text="TLauncher", variable=self.acct_type_var, value="tlauncher").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Radiobutton(acct_frame, text="Offline", variable=self.acct_type_var, value="offline").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(acct_frame, text="Microsoft (Demo)", variable=self.acct_type_var, value="microsoft", state="disabled").grid(row=0, column=2, sticky="w", padx=5) # Disable MS for now

        ttk.Label(acct_frame, text="Username/Email:").grid(row=1, column=0, padx=5, pady=3, sticky="e")
        self.username_entry = ttk.Entry(acct_frame, width=30)
        self.username_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="we")

        ttk.Label(acct_frame, text="Password/Token:").grid(row=2, column=0, padx=5, pady=3, sticky="e")
        self.password_entry = ttk.Entry(acct_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=3, sticky="we")
        ttk.Label(acct_frame, text="(Optional for Offline, Needed for TLauncher)").grid(row=3, column=1, columnspan=2, sticky="w", padx=5)
        ttk.Label(acct_frame, text="(Warning: Passwords stored insecurely)", foreground="orange").grid(row=4, column=1, columnspan=2, sticky="w", padx=5)

        ttk.Button(acct_frame, text="Add / Update Account", command=self.on_add_account).grid(row=1, column=3, rowspan=2, padx=10, pady=5, sticky="ns")

        ttk.Separator(acct_frame, orient='horizontal').grid(row=5, column=0, columnspan=4, sticky="ew", pady=10)

        ttk.Label(acct_frame, text="Select Account:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(acct_frame, textvariable=self.account_var, state="readonly", width=40)
        self.account_combo.grid(row=6, column=1, columnspan=3, padx=5, pady=5, sticky="we")
        self.account_combo.bind("<<ComboboxSelected>>", self.on_account_selected)

        acct_frame.columnconfigure(1, weight=1) # Make entry/combo expand
        acct_frame.columnconfigure(2, weight=1)

        # --- Version / Modpack Frame ---
        ver_frame = ttk.LabelFrame(root, text="Game Version / Modpack")
        ver_frame.pack(fill="x", padx=10, pady=5)

        # Populate versions list (releases first, then snapshots)
        release_versions = sorted([v['id'] for v in version_manifest['versions'] if v['type'] == 'release'], reverse=True)
        snapshot_versions = sorted([v['id'] for v in version_manifest['versions'] if v['type'] == 'snapshot'], reverse=True)
        # Add any custom versions found in VERSIONS_DIR
        custom_versions = []
        if os.path.isdir(VERSIONS_DIR):
            for item in os.listdir(VERSIONS_DIR):
                if os.path.isdir(os.path.join(VERSIONS_DIR, item)) and item not in all_versions:
                     custom_versions.append(item) # Add Forge/Fabric etc. profiles

        # Predefined modpacks (can be expanded)
        self.popular_modpacks = {
            "RLCraft (Modpack)": "rlcraft",
            "All the Mods 9 (Modpack)": "all-the-mods-9-atm9",
            "Pixelmon Modpack (Modpack)": "the-pixelmon-modpack",
            "One Block MC (Modpack)": "one-block-mc",
            "DawnCraft (Modpack)": "dawncraft",
            "Better MC (Modpack)": "better-mc-bmc1-forge", # Example forge
            # Add more popular modpack names and their TLMods slugs here
        }
        modpack_names = sorted(self.popular_modpacks.keys())

        combined_list = modpack_names + sorted(custom_versions, reverse=True) + release_versions + snapshot_versions
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(ver_frame, textvariable=self.version_var, values=combined_list, state="readonly", width=50)
        self.version_combo.grid(row=0, column=0, padx=5, pady=5, sticky="we")
        # Try setting default to latest release or first in list
        if release_versions:
             self.version_combo.set(release_versions[0])
        elif combined_list:
             self.version_combo.set(combined_list[0])

        ver_frame.columnconfigure(0, weight=1) # Make combo expand

        # --- Launch Options Frame ---
        options_frame = ttk.LabelFrame(root, text="Launch Options")
        options_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(options_frame, text="Max RAM (MB):").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.ram_spin = ttk.Spinbox(options_frame, from_=512, to=32768, increment=512, width=10)
        self.ram_spin.set("4096") # Default 4GB
        self.ram_spin.grid(row=0, column=1, pady=3, sticky="w")

        ttk.Label(options_frame, text="Java Path:").grid(row=1, column=0, padx=5, pady=3, sticky="e")
        self.java_entry = ttk.Entry(options_frame, width=40)
        self.java_entry.insert(0, self.find_java()) # Auto-detect Java
        self.java_entry.grid(row=1, column=1, padx=5, pady=3, sticky="we")
        ttk.Button(options_frame, text="Browse...", command=self.browse_java).grid(row=1, column=2, padx=5)

        ttk.Label(options_frame, text="Server IP (Optional):").grid(row=2, column=0, padx=5, pady=3, sticky="e")
        self.server_entry = ttk.Entry(options_frame, width=30)
        self.server_entry.grid(row=2, column=1, padx=5, pady=3, sticky="w")
        ttk.Label(options_frame, text="Port:").grid(row=2, column=2, padx=2, pady=3, sticky="e")
        self.port_entry = ttk.Entry(options_frame, width=8)
        self.port_entry.grid(row=2, column=3, padx=5, pady=3, sticky="w")


        options_frame.columnconfigure(1, weight=1) # Make Java path entry expand

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Frame(root, relief=tk.SUNKEN, padding="2 2 2 2")
        status_bar.pack(side=tk.BOTTOM, fill="x")
        ttk.Label(status_bar, textvariable=self.status_var).pack(side=tk.LEFT)

        # --- Launch Button ---
        self.launch_btn = ttk.Button(root, text="Launch Game", command=self.on_launch, style="Accent.TButton") # Use accent style if available
        self.launch_btn.pack(pady=15, ipadx=10, ipady=5)

        # --- Styling (Optional) ---
        style = ttk.Style()
        try:
            # Attempt to use a modern theme if available (e.g., on Windows)
            style.theme_use('vista')
        except tk.TclError:
             print("Vista theme not available, using default.")
        style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'), foreground="white", background="#0078D7") # Example accent style

        # --- Initial Population ---
        self.refresh_account_list()


    def find_java(self):
        """Attempts to find a suitable Java executable."""
        java_exe = "java.exe" if os.name == 'nt' else "java"
        # 1. Check JAVA_HOME
        java_home = os.environ.get("JAVA_HOME")
        if java_home and os.path.isfile(os.path.join(java_home, "bin", java_exe)):
            return os.path.join(java_home, "bin", java_exe)
        # 2. Check PATH
        java_path = shutil.which(java_exe)
        if java_path:
            return java_path
        # 3. Common install locations (Windows example)
        if os.name == 'nt':
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            common_paths = [
                os.path.join(program_files, "Java"),
                os.path.join(program_files, "Eclipse Adoptium"), # Common for Temurin/Adoptium JDK
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Java")
            ]
            for path in common_paths:
                if os.path.isdir(path):
                    # Look for latest JDK/JRE within
                    for root, dirs, files in os.walk(path):
                        if java_exe in files and "bin" in root:
                             # Check if it's a valid Java version (optional, complex)
                             return os.path.join(root, java_exe)
        # Fallback
        return "java" # Let system decide if not found


    def browse_java(self):
        """Opens file dialog to select Java executable."""
        filename = filedialog.askopenfilename(
            title="Select Java Executable",
            filetypes=[("Java Executable", "java.exe"), ("Executable files", "*.*"), ("All Files", "*.*")] if os.name == 'nt' else [("Java Executable", "java"), ("All Files", "*.*")]
        )
        if filename:
            self.java_entry.delete(0, tk.END)
            self.java_entry.insert(0, filename)

    def set_status(self, message, color="black"):
        """Updates the status bar message and color."""
        # Ensure this runs on the main Tkinter thread if called from another thread
        self.root.after(0, self._update_status_ui, message, color)

    def _update_status_ui(self, message, color):
         self.status_var.set(message)
         # Find the label within the status bar frame to set color (a bit hacky)
         for widget in self.root.winfo_children():
             if isinstance(widget, ttk.Frame) and widget.cget('relief') == tk.SUNKEN: # Identify status bar frame
                  for label in widget.winfo_children():
                      if isinstance(label, ttk.Label):
                          label.config(foreground=color)
                          break
                  break


    def on_add_account(self):
        acc_type = self.acct_type_var.get()
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get().strip()

        if not user:
            messagebox.showwarning("Input Error", "Username/Email cannot be empty!")
            return

        if acc_type == "tlauncher" and not pwd:
             result = messagebox.askyesno("Password Missing", "You selected TLauncher account but left the password empty. TLauncher usually requires a password (stored insecurely here).\n\nDo you want to continue anyway (treat as offline)?")
             if not result: return # User cancelled

        try:
            add_account(acc_type, user, pwd)
            self.refresh_account_list()
            # Clear fields after adding
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.set_status(f"Account '{user}' added/updated.", "green")
        except Exception as e:
             messagebox.showerror("Account Error", f"Failed to add/update account: {e}")
             self.set_status(f"Error adding account: {e}", "red")


    def refresh_account_list(self):
        """Reloads the account list into the combobox."""
        display_names = [f"{acc.get('type','N/A').capitalize()}: {acc.get('username','Unknown')}" for acc in accounts]
        self.account_combo['values'] = display_names
        if display_names:
            # Try to keep the current selection if it still exists
            current_selection = self.account_var.get()
            if current_selection in display_names:
                 self.account_combo.set(current_selection)
            else:
                 self.account_combo.current(0) # Select first if current is gone or empty
        else:
            self.account_combo.set('') # Clear selection if no accounts


    def on_account_selected(self, event=None):
        """(Optional) Action when an account is selected."""
        # Could pre-fill username/password fields if needed, but generally just use selection at launch.
        pass


    def on_launch(self):
        """Handles the launch button click."""
        selected_version_display = self.version_var.get()
        if not selected_version_display:
            messagebox.showerror("Error", "Please select a version or modpack.")
            return

        account_index = self.account_combo.current()
        if account_index == -1 and not accounts:
            result = messagebox.askyesno("No Account Selected", "No accounts are configured. Launch in Offline mode with username 'Player'?")
            if result:
                selected_account = {"type": "offline", "username": "Player", "uuid": str(uuidlib.uuid3(uuidlib.NAMESPACE_DNS, "Player")), "token": "0"}
            else:
                return
        elif account_index == -1 and accounts:
             messagebox.showerror("Error", "Please select an account from the list.")
             return
        else:
            selected_account = accounts[account_index]


        try:
            ram_val = int(self.ram_spin.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid RAM value. Please enter a number (MB).")
            return

        java_path_val = self.java_entry.get().strip() or self.find_java() # Use detected if empty
        server_ip_val = self.server_entry.get().strip() or None
        port_val_str = self.port_entry.get().strip()
        port_val = None
        if port_val_str:
            try:
                port_val = int(port_val_str)
                if not (0 < port_val < 65536): raise ValueError
            except ValueError:
                 messagebox.showerror("Error", "Invalid Port number. Must be between 1 and 65535.")
                 return

        # Determine if it's a modpack or regular version
        is_modpack = selected_version_display in self.popular_modpacks
        modpack_slug = self.popular_modpacks.get(selected_version_display) if is_modpack else None
        version_to_process = modpack_slug if is_modpack else selected_version_display # Use slug for modpack processing, ID for version

        # Disable UI elements during launch process
        self.launch_btn.config(state="disabled")
        self.set_status("Starting launch process...", "blue")

        # Run install/launch in a separate thread to keep UI responsive
        launch_thread = threading.Thread(
            target=self._launch_task,
            args=(version_to_process, is_modpack, selected_account, ram_val, java_path_val, server_ip_val, port_val),
            daemon=True
        )
        launch_thread.start()

    def _launch_task(self, item_to_launch, is_modpack, account, ram, java, server, port):
        """Background task for installing (if needed) and launching."""
        try:
            final_version_id = None
            game_directory = None # Default is standard .minecraft

            if is_modpack:
                self.set_status(f"Installing modpack '{item_to_launch}'...", "blue")
                # install_modpack returns the version ID to launch and the custom game directory
                final_version_id, game_directory = install_modpack(item_to_launch, status_callback=self.set_status)
                self.set_status(f"Modpack '{item_to_launch}' installed. Launching version '{final_version_id}'...", "blue")
            else:
                # It's a standard Minecraft version ID
                final_version_id = item_to_launch
                self.set_status(f"Checking installation for version '{final_version_id}'...", "blue")
                # Ensure the version is installed (downloads if needed)
                # game_directory remains None (use default .minecraft)
                install_version(final_version_id, status_callback=self.set_status)
                self.set_status(f"Version '{final_version_id}' ready. Preparing launch...", "blue")

            # Now launch the game with the determined version ID and game directory
            launch_game(
                version_id=final_version_id,
                account=account,
                ram_mb=ram,
                java_path=java,
                game_dir=game_directory, # Pass the specific modpack dir if applicable
                server_ip=server,
                port=port,
                status_callback=self.set_status
            )
            # Status will be updated inside launch_game upon execution start

        except Exception as e:
            error_message = f"Error during launch: {e}"
            print(f"ERROR: {error_message}") # Log full error to console
            import traceback
            traceback.print_exc() # Print stack trace to console for debugging
            self.set_status(f"Error: {e}", "red") # Show concise error in GUI status
            # Show error popup (ensure it runs in main thread)
            self.root.after(0, messagebox.showerror, "Launch Failed", error_message)
        finally:
            # Re-enable the launch button (ensure it runs in main thread)
            self.root.after(0, self.launch_btn.config, {"state": "normal"})


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CatClientApp(root)
    root.mainloop() 