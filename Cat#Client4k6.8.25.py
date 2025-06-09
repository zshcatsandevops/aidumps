import minecraft_launcher_lib
import subprocess
import argparse

LAUNCHER_NAME = "CatClient4k"
LAUNCHER_VERSION = "0.1"

parser = argparse.ArgumentParser(description=f"{LAUNCHER_NAME} {LAUNCHER_VERSION} - Custom Minecraft Launcher")
parser.add_argument("--version", help="Minecraft version to launch", default=minecraft_launcher_lib.utils.get_latest_version()['release'])
parser.add_argument("--username", help="Username for offline mode", default="Player")
args = parser.parse_args()

minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()

# Install the specified version if not already installed
minecraft_launcher_lib.install.install_minecraft_version(args.version, minecraft_directory)

# Set options for launching (for testing only)
options = minecraft_launcher_lib.utils.generate_test_options()
options["username"] = args.username
options["jvmArguments"] = ["-Xmx4G", "-Xms2G"]  # Optimize memory for better performance

# Get the launch command
command = minecraft_launcher_lib.command.get_minecraft_command(args.version, minecraft_directory, options)

# Launch Minecraft
print(f"Launching Minecraft {args.version} as {args.username}")
subprocess.run(command)
