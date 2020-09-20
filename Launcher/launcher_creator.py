
import os
import sys
import argparse
import shutil
import base64
import tempfile
import zipfile
import subprocess
import dirhash

LAUNCHER_TEMPLATE = "launcher.py"
LAUNCHER_SCRIPT = "launcher.py"
LAUNCHER_EXE = LAUNCHER_SCRIPT.replace(".py", ".exe")
HASH_FOR_DIR = "md5"

PYINSTALLER_COMMAND = "{} -m PyInstaller --onefile -w {} --distpath {} --workpath {} --specpath {}"

VARIABLES = """
COMPRESSED_UPDATE = {}
PROGRAM = "{}"
DIR_HASH = "{}"
HASH_USED = "{}"
LAUNCHER_NAME = "*{}"
EXTRACTION_DIRECTORY = "{}"
"""

def zip_directory(path, zip_handler):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, path)
            zip_handler.write(file_path, relative_path)
            
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            relative_path = os.path.relpath(dir_path, path)
            zip_handler.write(dir_path, relative_path)
        

def create_launcher(directory_path, program):
    # Creates a zip file to store the contents of directory_path
    temp_file = tempfile.TemporaryFile()
    zip_file = zipfile.ZipFile(temp_file, "w")
    
    # Zips the whole directory into the temp file
    zip_directory(directory_path, zip_file)
    zip_file.close()
    
    # Reads the zip file data
    temp_file.seek(0)
    data = temp_file.read()
    data = base64.encodebytes(data)
    
    # Calculates the hash of the directory of the program
    hash = dirhash.dirhash(directory_path, HASH_FOR_DIR, empty_dirs=True)
    
    # Creates the variables for the launcher
    program_directory = program[:-len(".exe")] if program.endswith(".exe") else program
    variables = VARIABLES.format(data, program, hash, HASH_FOR_DIR, LAUNCHER_EXE, program_directory)
    
    # Creates the lancher script
    with open(LAUNCHER_SCRIPT, "w") as runner:
        with open(LAUNCHER_TEMPLATE, "r") as template:
            runner.write(variables)
            runner.write(template.read())
    
    print()
    print("Created", LAUNCHER_SCRIPT)
    print()

    # Converts the script to exe using pyinstaller
    convert_to_exe()
    
def convert_to_exe():
    # Creates a temp directory
    temp_dir = tempfile.TemporaryDirectory()
    
    # Builds the paths for pyinstaller
    dist_dir = os.path.join(temp_dir.name, "dist")
    work_dir = os.path.join(temp_dir.name, "build")
    script = os.path.abspath(LAUNCHER_SCRIPT)
    
    # Runs pyinstaller to convert the script to EXE
    command = PYINSTALLER_COMMAND.format(sys.executable, script, dist_dir, work_dir, work_dir)
    subprocess.call(command, cwd=temp_dir.name)
    
    # Copies the EXE to the current directory
    command_output = os.path.join(dist_dir, LAUNCHER_EXE)
    shutil.copy(command_output, LAUNCHER_EXE)
    
    # Cleans up the temp directory
    temp_dir.cleanup()
    shutil.rmtree("__pycache__")
    
    print()
    print("Created", LAUNCHER_EXE)
    print()
    
    
def main():
    parser = argparse.ArgumentParser(description='Creates a runner to update program files')
    parser.add_argument('update_path', metavar='Path', type=str,
                        help='The path to the folder with the files. (ex: build\\exe.win-amd64-3.8)')
    parser.add_argument('program', metavar='Program', type=str,
                        help='The program name to run. Needs to be inside the given Path.')

    args = parser.parse_args()
    
    if sys.version_info.major < 3:
        print("This script is build for python 3. Use the python3 interpeter!")
        return
    
    if not os.path.isdir(args.update_path):
        print("Invalid path was given")
        return
    
    if not os.path.exists(os.path.join(args.update_path, args.program)):
        print("Invalid program was given. Is it inside the given path?")
        return
    
    create_launcher(args.update_path, args.program)
    

if __name__ == "__main__":
    main()