# Installer

This program is the **installer**. This script should be ran by the developer on the updating server.

It allows the developer to do the following actions:

* Generate and display RSA keys (the keys will be used to sign update messages).
* Create and deploy updates.
* Broadcast new updating server information to clients.
* Create a `setup.exe` file, so the clients can easily install the program and all of it's component (including the **updater** service, and the launcher).

Below you can find an example of some of the commands the installer allows the developer to run:

* For a full explanation of each command, using `--help` flag for the command you would like to explore.
* For a brief usage of how to use the installer, see sections `Setup` and `Usage` below.

<img src="..\Images\installer_usage.png" alt="installer_usage.png" style="zoom: 80%;" />

## Requirements

* Windows machine (Tested on Windows 10 Pro 64 bit - version 2004, OS Build 19041.508)
* Python 3 (Tested on Python 3.8.2 - 64bit)
* Pip for python 3 (Tested with version 20.2.3)
* C++ Build Tools for Visual Studio (Tested with 2019)
* Inno Setup (Tested with version 6.0.5)
* Python packages (install using requirements.txt):
  * pycryptodome (Tested with version 3.9.8)
  * construct (Tested with version 2.10.56)
  * validators (Tested with version 0.18.1)
  * netifaces (Tested with version 0.10.9)
  * colorama (Tested with version 0.4.3)

## Setup

1. Install python 3 and pip, if you don't have it already.

2. Download VS Build tools from [here](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16) and install it, if you don't already have it.

   * Select "C++ build tools", and on the right panel only check the 3 first checkboxes: `MSVC`, `Windows 10 SDK`, `C++ CMake`.

3. Run the following command to install the required python packages:

   ```batch
   python3 -m pip install -r requirements.txt
   ```

4. Follow the instructions in `Setup` section of `Updater\README.md`.

5. Follow the instructions in `Setup` section of `Launcher\README.md`.

6. Install `Inno Setup` from [jrsoftware.org](https://jrsoftware.org/isdl.php).

7. Update the constant `INNO_SETUP_INSTALL_FOLDER` in `installer.py` (line 31) according to the installation folder of `Inno Setup`.

   * The default value is `C:\Program Files (x86)\Inno Setup 6`.

8. You now should be ready to run the script and use it! (see usage below).

## Usage

#### 	Creating a setup

* To create a `setup.exe` for a new software, follow these instruction on the updating server (The computer which will be used as the primary server to announce updates):

  1. In the file `Updater\settings.py`, update the `SOFTWARE_NAME` and `PROGRAM` (lines 20,21) to the correct values according to your software's name.

     * `PROGRAM` should be `SOFTWARE_NAME` with a suffix of `.exe` (can also be lowercased or uppercased since Windows is not case-sensitive).

     * Those settings will be used afterwards in the instruction bellow as `<SOFTWARE_NAME>` and `<PROGRAM>`.

  2. Run the following commands in `cmd` as `Administrator` (current working directory should be `Server`).

  3. Just to make sure, clean any previous files using the command: `python3 installer.py setup clean`.

  4.  Copy all the files of your software to some folder, let's say `..\Program\build` (relative to the `Server` folder)

     * This folder will be called `<software_folder>` from now on. On my machine it is: `..\Program\build\exe.win-amd64-3.8`.
     * Note that the `PROGRAM` setting you set in first instruction should be located at `<software_folder>\<PROGRAM>`.

  5. Finally, create the `setup.exe` using `python3 installer.py setup create -s <software_folder> <SOFTWARE_NAME> <major> <minor> -i <SERVER_DNS> -p <PORT> `.

     * Major and minor are the numbers of the version. For example, if your software's version is 13.7, the major is 13 and the minor is 7.

     * The `SERVER_DNS` should be the DNS or the IP of the updating server. The `PORT` will be the port all the services will listen on (defaults to 55555).

     * This command does a lot of things, the most important of them are:

       * Creating the `settings.json` file according to the settings from step 1.
       * Generating RSA keys and adding them to the registry (both private and public keys). The public key is also added to `settings.json` file.
       * Creating the `service.exe` for the **updater** using `PyInstaller`.
       * Creating the `launcher.exe` for the **launcher** using `PyInstaller`.
       * Using `Inno Setup`, it creates a `setup.exe` file out of the software files from step 4, `service.exe`, `launcher.exe`, and `settings.json`.

     * The output of `PyInstaller` and `Inno Setup` should be printed in blue. The output without the "blue parts" should look like this:

       <img src="..\Images\creating_setup.png" alt="creating_setup.png"  />

  6. Once the script has finished (give it some time), you should find your setup file in `Server\Output\<SOFTWARE_NAME>_<major>.<minor>_setup.exe`

     :warning:Important Note: After creating a setup, you would want to make sure not to create another one, or generate new RSA keys, because this will overriding the currently stored RSA keys and your updating server won't be able to serve any client.

  7. You should now run the setup file created and install it on the updating server, afterwards it will be able to serve other clients that install the software using the same setup file.

#### Deploying an update

* After you have created a setup, as a developer, you might want to deploy an update for your software. To do that, follow these instruction on the updating server (the same server that created the `setup.exe` file):

  1. Run the following commands in `cmd` as `Administrator` (current working directory should be `Server`).
  2. Copy all the files of your software's update to some folder, let's say `..\Program\build` (relative to the `Server` folder)
     * This folder will be called `<software_folder>` from now on. On my machine it is: `..\Program\build\exe.win-amd64-3.8`.
     * Note that the `PROGRAM` setting you set in first instruction should be located at `<software_folder>\<PROGRAM>` (The same `PROGRAM` that was set in step 1 of the setup creation).
  3. Create the update using `python3 installer.py update create <software_folder> <major> <minor>`.
     * Major and minor are the numbers of the version of the update. For example, if your software's version is 13.7, the major is 13 and the minor is 7.

  4. After you successfully ran the previous command, it should create a `update.zip` file at the directory of the **updater** `service`.

  5. To announce the clients of the new update, all you need to do is run `python3 installer.py update broadcast -s`.
     * The `-s` flag sets the `spread` flag in the message, so other clients will broadcast the message to clients on their LAN.
  6. That's it. The new update is deployed. If some client didn't get the announcement message, they can still query the updating server (or other clients) and receive the update on later time.

#### Other commands

* You can display or change the server information using `python3 installer.py server ...` 
* You can display or change the RSA keys using `python3 installer.py rsa ...`
* For full explanation, use the `--help` flag and find for yourself what you can do.

## Known Issues

* Since the launcher and the service work independently, If one of them tries to write or delete to a file the other reads from, they will encounter a permission error. The code should handle those errors and ignore them, but the files might stay there.
  * The code is built to minimize these collisions, and to try and delete those files on later occasion, but those collision are still possible.