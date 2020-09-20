
import os
import zipfile
import subprocess
import socket
import argparse

import PySimpleGUI as sg

from Updater import settings
from Updater import constructs
from Updater import registry
from Updater import updater


def progressive_extract(zip_handler, silent):
    # Calculates the total uncompressed size
    uncompress_size = sum((file.file_size for file in zip_handler.infolist()))
    
    extracted_size = 0
    for file in zip_handler.infolist():
        # Extracts the current file
        zip_handler.extract(file, path=settings.SOFTWARE_PATH)
        
        # Calculates the total extracted size
        extracted_size += file.file_size
        
        # Updates the progress bar
        should_continue = True
        if not silent:
            should_continue = sg.one_line_progress_meter('Updating...', extracted_size, uncompress_size,
                                                         "extraction_bar",
                                                         "Applying update...", orientation="horizontal",
                                                         no_titlebar=True, grab_anywhere=True)
                            
        # Checks if finished or canceled
        if extracted_size >= uncompress_size:
            return True
        if not should_continue:
            # The user has pressed the cancel button
            result = sg.popup_yes_no("Canceling the update might break your program and render it useless.\nAre you sure you want to cancel?", title="Are you sure?")
            if result == "Yes":
                return False
    
    return True


def progressive_copy(src, dest, silent):
    result = True
    chunk_size = 1024 * 1024
    file_size = os.stat(src).st_size
    total_bytes = 0

    src = open(src, "rb")
    dest = open(dest, "wb")

    while total_bytes < file_size:
        chunk = src.read(chunk_size)
        dest.write(chunk)
        should_continue = True
        if not silent:
            should_continue = sg.one_line_progress_meter('Updating...', total_bytes, file_size,
                                                         "copying_bar",
                                                         "Downloading update...", orientation="horizontal",
                                                         no_titlebar=True, grab_anywhere=True)
        # Checks if finished or canceled
        if total_bytes >= file_size:
            break
        if not should_continue:
            # The user has pressed the cancel button
            output = sg.popup_yes_no(
                "Canceling the update might break your program and render it useless.\nAre you sure you want to cancel?",
                title="Are you sure?")
            if output == "Yes":
                result = False
                break

    src.close()
    dest.close()
    return result


def cleanup_old_updates():
    current_version_registry = updater.Version.get_current_version().get_update_registry_path()
    all_sub_values = registry.get_all_sub_values()
    all_sub_values = [v for v in all_sub_values if v.startswith(settings.UPDATE_REGISTRY_FORMAT) and v != current_version_registry]

    for update_registry in all_sub_values:
        file = registry.get_value(update_registry)
        try:
            os.remove(file)
        except PermissionError:
            # File is in use
            continue
        except FileNotFoundError:
            pass
        registry.delete(update_registry)


def update(update_file_path, silent):
    update_file = zipfile.ZipFile(update_file_path, "r")
    
    # Extracts the update
    try:
        result = progressive_extract(update_file, silent)
    except PermissionError:
        # probably program is running or permission is denied
        error_message = "Failed to update due to PermissionError. The program might be running or launcher has insufficient permissions."
        if silent:
            print(error_message)
        else:
            sg.popup_error(error_message, title="Error")
        return False
    return result


def check_for_update():
    # Builds the request update message
    request_update_dict = dict(
        type=constructs.MessageType.REQUEST_UPDATE,
        crc32=0
    )
    request_update_message = constructs.REQUEST_UPDATE_MESSAGE.build(request_update_dict)

    # Updates the crc
    request_update_dict["crc32"] = constructs.calculate_crc(request_update_message)
    request_update_message = constructs.REQUEST_UPDATE_MESSAGE.build(request_update_dict)

    ip_address = registry.get_value(settings.UPDATING_SERVER_REGISTRY)
    port = registry.get_value(settings.PORT_REGISTRY)

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.settimeout(settings.CONNECTION_TIMEOUT)

    try:
        # Sends the message
        sender.sendto(request_update_message, (ip_address, port))
    except socket.error:
        print("Error: Failed to check for update")
    finally:
        sender.shutdown(2)
        sender.close()


def install_update(silent):
    # Checks if an update is available
    if updater.Version.is_updated():
        return

    # Checks if the update should be installed automatically
    automatic_installation = registry.get_value(settings.AUTO_INSTALLATIONS_REGISTRY)
    if automatic_installation == 0 and not silent:
        # Asks the user if they would like to update
        result = sg.popup_yes_no("A new update is available. Would you like to install it?", title="Update")
        if result != "Yes":
            return

    # Get the path of the update file
    version_registry = updater.Version.get_current_version().get_update_registry_path()
    update_filepath = registry.get_value(version_registry)

    # Replace the old update file with the new one
    error_message = None
    try:
        if not progressive_copy(update_filepath, settings.UPDATE_PATH, silent):
            # Update was canceled by the user
            return
    except PermissionError:
        error_message = f"Failed to replace update file {settings.UPDATE_PATH}. Insufficient permission or file is locked."
    except OSError:
        error_message = f"Failed to replace update file {settings.UPDATE_PATH}. Unknown OS Error."

    if error_message:
        if silent:
            print(error_message)
        else:
            sg.popup_error(error_message, title="Error")
        return

    # Version was updated! Update the registry
    updater.Version.get_current_version().update_installed_version()

    # Extracts the update
    update(settings.UPDATE_PATH, silent)


def setup(apply_update, check_update, update_file, no_launch, silent):
    if not silent:
        # Sets the GUI theme
        sg.theme('DarkAmber')

    if update_file is not None:
        if not os.path.exists(update_file):
            print(f"Update file {update_file} does not exist.")
            return False
        return update(update_file, silent)

    if check_update:
        check_for_update()
    if apply_update and not check_update:
        install_update(silent)

    cleanup_old_updates()
    return True


def run(no_launch):
    if not no_launch:
        # Runs the program
        program = os.path.join(settings.SOFTWARE_PATH, settings.PROGRAM)
        subprocess.Popen([program], cwd=settings.SOFTWARE_PATH)
    return True


def cleanup():
    pass


def main():
    parser = argparse.ArgumentParser(description="Launcher of the program. Checks for updates and applies them.")
    parser.add_argument("-a", "--apply_update", action="store_true",
                        help="Installs an update if available.")
    parser.add_argument("-c", "--check_update", action="store_true",
                        help="Queries the server if an update is available (the service will download it). Overrides -a.")
    parser.add_argument("-u", "--update_file", metavar="<Update Zip>", type=str,
                        help="Receives an update file and updates to it. Overrides -a and -c.")
    parser.add_argument("-n", "--no_launch", action="store_true",
                        help="Do not launch the program.")
    parser.add_argument("-s", "--silent", action="store_true",
                        help="Do not show GUI or wait for user input.")

    args = parser.parse_args()

    args_dict = vars(args)
    if setup(**args_dict):
        if run(args.no_launch):
            cleanup()


if __name__ == "__main__":
    main()
