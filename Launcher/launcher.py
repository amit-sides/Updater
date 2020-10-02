
import sys
import os
import zipfile
import subprocess
import socket
import argparse

import PySimpleGUI as sg

sys.path.append("..")

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
        zip_handler.extract(file, path=settings.PROGRAM_PATH)

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
        total_bytes += len(chunk)
        should_continue = True
        if not silent:
            should_continue = sg.one_line_progress_meter('Updating...', total_bytes, file_size,
                                                         "copying_bar",
                                                         "Extracting update...", orientation="horizontal",
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
    all_sub_values = registry.get_all_sub_values(settings.REGISTRY_PATH)
    update_prefix = settings.UPDATE_REGISTRY_FORMAT.format("")
    all_sub_values = [settings.REGISTRY_PATH + "\\" + v for v in all_sub_values]
    all_sub_values = [v for v in all_sub_values if v.startswith(update_prefix) and v != current_version_registry]

    for update_registry in all_sub_values:
        file = registry.get_value(update_registry)
        try:
            os.remove(file)
        except PermissionError:
            # File is in use, don't delete registry if file wasn't deleted as well
            continue
        except FileNotFoundError:
            # File appears to be missing, should delete the registry...
            pass
        registry.delete(update_registry)


def update(update_file_path, silent):
    try:
        update_file = zipfile.ZipFile(update_file_path, "r")
    except zipfile.BadZipFile:
        error_message = "Invalid update file."
        if silent:
            print(error_message)
        else:
            sg.popup_error(error_message, title="Error")
        return False
    
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


def query_server():
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
        print(f"Sent a version query to the server: {ip_address}:{port}")
    except socket.error:
        print("Error: Failed to check for update")
    finally:
        sender.shutdown(2)
        sender.close()


def install_update(silent):
    # Checks if an update is available
    if updater.Version.is_updated():
        return "ERROR: No update is available."

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

    # Extracts the update
    if update(settings.UPDATE_PATH, silent):
        # Version was updated! Update the registry
        updater.Version.get_current_version().update_installed_version()
        return "Update installed successfully!"


def get_layout():
    automatic_installation = registry.get_value(settings.AUTO_INSTALLATIONS_REGISTRY)
    update_frame = [
        [sg.Button("Query server for update", key="-QUERY_SERVER-")],
        [sg.CB("Automatically update on next launch", key="-AUTO-", enable_events=True, default=automatic_installation)],
    ]

    installed_version = updater.Version.get_installed_version()
    update_version = updater.Version.get_current_version()

    layout = [[sg.Button("Launch", key="-LAUNCH-", size=(15, 2)), sg.Button("Update", key="-UPDATE-", size=(15, 2), disabled=(update_version <= installed_version))],
              [sg.T("Version: " + str(installed_version), key="-INSTALL_VERSION-", size=(15, 1)), sg.T("Update: " + str(update_version), key="-UPDATE_VERSION-", size=(15, 1))],
              [sg.Frame("Updater", update_frame)]]
    return layout


def update_layout(window):
    installed_version = updater.Version.get_installed_version()
    update_version = updater.Version.get_current_version()

    window["-UPDATE-"].update(disabled=(update_version <= installed_version))
    window["-INSTALL_VERSION-"].update("Version: " + str(installed_version))
    window["-UPDATE_VERSION-"].update("Update: " + str(update_version))


def check_for_update(window):
    installed_version = updater.Version.get_installed_version()
    update_version = updater.Version.get_current_version()

    if installed_version >= update_version:
        return

    # Checks if the update should be installed automatically
    automatic_installation = registry.get_value(settings.AUTO_INSTALLATIONS_REGISTRY)
    if automatic_installation == 0:
        # Asks the user if they would like to update
        result = sg.popup_yes_no(f"A new update is available. Would you like to install it?\n\nInstalled:\t {installed_version}\nUpdate: \t{update_version}", title="Update")
        if result != "Yes":
            return

    # Installs the update
    install_update(silent=False)

    update_layout(window)


def update_auto_installations(values):
    if values["-AUTO-"] is True:
        registry.set_value(settings.AUTO_INSTALLATIONS_REGISTRY, 1)
    else:
        registry.set_value(settings.AUTO_INSTALLATIONS_REGISTRY, 0)


def display_gui():
    layout = get_layout()

    window = sg.Window("Launcher", layout, finalize=True)

    check_for_update(window)

    should_launch = False
    while True:  # Event Loop
        event, values = window.read(timeout=1000)
        if event == sg.WIN_CLOSED or event == "Exit":
            break
        if event == "-UPDATE-":
            install_update(False)
            update_layout(window)
        elif event == "-LAUNCH-":
            should_launch = True
            break
        elif event == "-AUTO-":
            # Update registry to auto-update
            update_auto_installations(values)
        elif event == "-QUERY_SERVER-":
            query_server()
        elif event == "__TIMEOUT__":
            # Timeout has passed
            update_layout(window)

    window.close()
    return should_launch


def setup(apply_update, check_update, update_file, versions, no_launch, silent):
    settings.init_settings(save=False)

    if not silent:
        # Sets the GUI theme
        sg.theme('DarkAmber')

    if versions:
        installed_version = updater.Version.get_installed_version()
        update_version = updater.Version.get_current_version()
        print(f"Installed version: {installed_version}")
        print(f"Update version: {update_version}")
        return False

    if update_file is not None:
        if not os.path.exists(update_file):
            print(f"Update file {update_file} does not exist.")
            return False
        return update(update_file, silent)

    should_launch = True
    if check_update:
        query_server()
        should_launch = False
    elif apply_update:
        result = install_update(silent)
        if result:
            print(result)
        else:
            print("Error has occurred!")
        should_launch = False
    elif not silent:
        should_launch = display_gui()

    cleanup_old_updates()
    return should_launch


def run(no_launch):
    if not no_launch:
        # Runs the program
        program = os.path.join(settings.PROGRAM_PATH, settings.PROGRAM)
        subprocess.Popen([program], cwd=settings.PROGRAM_PATH)
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
    parser.add_argument("-v", "--versions", action="store_true",
                        help="Display versions information. Overrides -u, -a and -c.")
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
