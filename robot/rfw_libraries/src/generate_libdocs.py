import os
import subprocess

BASE_PACKAGE = "rfw.lib"
OUTPUT_DIR = "libdocs"

# Create output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Path to actual .pyd files
LIB_PATH = os.path.join("rfw", "lib")

for file in os.listdir(LIB_PATH):
    if file.endswith(".pyd"):
        # Extract library name (remove cp310-win_amd64.pyd)
        lib_name = file.split(".cp")[0]

        full_import = f"{BASE_PACKAGE}.{lib_name}"
        output_file = os.path.join(OUTPUT_DIR, f"{lib_name}.html")

        print(f"Generating libdoc for {full_import}...")

        subprocess.run(["python", "-m", "robot.libdoc", full_import, output_file], check=False)

print("All library documentation generated.")
