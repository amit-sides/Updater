
import os
import sys
import tempfile
import zipfile
import subprocess
import base64
import dirhash
import PySimpleGUI as sg

UPDATE_ZIP = "update.zip"

def dir_updated():
    try:
        # Calculates the hash for the directory, while ignoring the launcher.exe and update.zip
        hash = dirhash.dirhash(EXTRACTION_DIRECTORY, HASH_USED, 
                        ignore=[LAUNCHER_NAME, UPDATE_ZIP], empty_dirs=True)
    except ValueError as e:
        if "Nothing to hash" in e.args[0] or "No such directory" in e.args[0]:
            return False
        raise e
    # Compares the calculated hash to the hash given to the launcher
    return DIR_HASH == hash
    
def progressive_extract(zip_handler, path):
    # Sets the GUI theme
    sg.theme('DarkAmber')
    
    # Calculates the total uncompressed size
    uncompress_size = sum((file.file_size for file in zip_handler.infolist()))
    
    extracted_size = 0
    for file in zip_handler.infolist():
        # Extracts the current file
        zip_handler.extract(file, path=path)
        
        # Calculates the total extracted size
        extracted_size += file.file_size
        
        # Updates the progress bar
        should_continue = sg.one_line_progress_meter('Updating...', extracted_size, uncompress_size, "extraction_bar", 
                            "Applying update...", orientation="horizontal", no_titlebar=True, grab_anywhere=True)
                            
        # Checks if finished or canceled
        if extracted_size >= uncompress_size:
            return True
        if not should_continue:
            # The user has pressed the cancel button
            result = sg.popup_yes_no("Canceling the update might break your program and render it useless.\nAre you sure you want to cancel?", title="Are you sure?")
            if result == "Yes":
                return False
    
    return True

def update():
    # Creates a temp file to read the update zip from
    tmp_file = tempfile.TemporaryFile()
    tmp_file.write(base64.decodebytes(COMPRESSED_UPDATE))
    zip = zipfile.ZipFile(tmp_file, "r")
    
    # Extracts the update
    try:
        result = progressive_extract(zip, EXTRACTION_DIRECTORY)
    except PermissionError:
        # probably program is running or permission is denied
        return False
    return result

def setup():
    # Checks if the directory is updated using hash
    if dir_updated():
        # If the directory is updated, just run the program
        return True
    
    # Needs to update the directory, extract the update...
    return update()
    
def run():
    # Runs the program
    program = os.path.join(EXTRACTION_DIRECTORY, PROGRAM)
    subprocess.Popen([program], cwd=EXTRACTION_DIRECTORY)
    return True
    
def cleanup():
    pass

def main():
    # For debugging purposes:
    # Run "launcher.exe zip" to write a zip file that contains the update to update.zip
    if len(sys.argv) > 1 and sys.argv[1] == "zip":
        with open(UPDATE_ZIP, "wb") as f:
            f.write(base64.decodebytes(COMPRESSED_UPDATE))
        return
    
    # Start the launcher, update files if needed, and start the program
    if setup():
        if run():
            cleanup()


if __name__ == "__main__":
    main()