# Launcher

This program is the **launcher** of the installed program. meaning, the user should run this program when they want to run the installed program.

The launcher is responsible for launching the program and installing the update that is downloaded by the **updater** service. It is also in charge of checking the update server for a new update (or more precisely, allowing the user to query the server for a new update) and deleting old update files.

![launcher.png](..\Images\launcher.png)

If the launcher detects the program runs an old version (if an update is available), it prompts the user about that and asks them if they want to update (Or, if the user checked the `Automatically update on next launch` checkbox, then the update is automatically installed without alerting the user). If the user chooses to update, the launcher copies the update file to save it, and applies it (extracting it to the program's location). All that is done with a neat progress bar:

![update.png](..\Images\update.png)

## Requirements

* Windows machine (Tested on Windows 10 Pro 64 bit - version 2004, OS Build 19041.508)
* Python 3 (Tested on Python 3.8.2 - 64bit)
* Pip for python 3 (Tested with version 20.2.3)
* Python packages (install using requirements.txt):
  * pysimplegui (Tested with version 4.29.0)
  * pyinstaller (Tested with version 4.0)

## Setup

1. Install python 3 and pip, if you don't have it already.

3. Run the following command to install the required python packages:

   ```batch
   python3 -m pip install -r requirements.txt
   ```

5. You now should be ready to run the script and use it! (see usage below)

## Usage

* The launcher can only be executed if it was installed on a computer using the setup.exe file created by the **installer**. If you still insist on running it without running the launcher, see the instructions bellow
  * The reason is because it uses some registry values that are created by the **updater** service and it uses a settings file that should be located in a specific location.
* Just like the **updater** service, because it needs to run on the client's computers without python installed, it should be converted to EXE as well.
  * The installer does it automatically when creating a new `setup.exe` file, so you wouldn't need to do it yourself.
  * To convert it manually (for some reason), you can run `pyinstaller -p ..\ --onefile -w laucher.py`
* To run the launcher manually (which you probably don't want to do):
  1. Convert the `launcher.py` script to EXE using the command: `pyinstaller -p ..\ --onefile -w laucher.py`
  2. Run the **updater** service using the instructions in `Updater\README.md` (Read `Setup` and `Usage` sections).
  3. Copy the `launcher.exe` created by the command from the `dist` folder to `C:\Program Files\<SOFTWARE_NAME>`.
  4. You should know be able to run the launcher from `C:\Program Files\<SOFTWARE_NAME>`. Make sure to run it as `Administrator` because, as noted above, it does use the registry to share some of it settings with the **updater** service.

## Known Issues

* Since the launcher is a python code packed as executable, using `PyInstaller`, it has a slow startup, and somewhat slow running time. But since it's not too terrible, I think it's fine, and unless we implement it using other language, we can't really do much with it.
* Sometimes `Windows Defender` (and maybe other AVs too) detects executables created by `PyInstaller` as suspicious, and as a result it scans them. This behavior causes the program to run **extremely** slow. So if it happens, make sure to disable your AV or set the launcher as exception.