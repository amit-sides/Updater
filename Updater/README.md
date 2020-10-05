# Updater
This program runs as a windows service and listens for incoming notification or requests of new updates.

It runs a windows service that acts as a UDP server and listens on a given port. If it receives a message about a new update, it attempts to download it from the sender of the message, and after a successful download, it broadcasts the message to other computers so that they can download the update from it (and so the cycle continues...).

If the sender of a message didn't set the `spread` flag in the message, the service won't broadcast the received message forward to other computers.

If the service receives a message about an old version of update (an update he already has or older than that), it doesn't process this message, and broadcasts it. This way, broadcast messages aren't sent indefinitely and cause a broadcast storm.

Also, the update server can send an update for the information of the update server (for example, a change of domain name or port). This causes the service to change the update server stored in the registry, and also change the port that this service listens on. This should only be executed as last resort, since you can't be sure all the clients got the new information and they might be disconnected from all the other client forever (unless they manually fix the information mismatch).

Every message sent by the update server (new update message, new update server information message) is cryptographically signed using RSA, so an attacker should not be able to send a fake update to a client and create a backdoor to it's computer. If a message can also be sent by a client (and therefor can't be signed by the client), then the "signature" field acts as a CRC32 checksum for the message, making sure no error occurred during the transfer (of course, this type of messages can't cause harm to the receiver, apart from a DOS attack maybe).

All the messages supported by the service can be found at `messages.py`. They are built using the `construct` package in a (pretty) user-friendly format.

## Requirements

* Windows machine (Tested on Windows 10 Pro - version 2004, OS Build 19041.508)
* Python 3 (Tested on Python 3.8.2 - 64bit)
* Pip for python 3 (Tested with version 20.2.3)
* TODO: Build Tools?
* Python packages (install using requirements.txt):
  * pywin32 (Tested with version 228)
  * pycryptodome (Tested with version 3.9.8)
  * construct (Tested with version 2.10.56)
  * netifaces (Tested with version 0.10.9)
  * pyinstaller (Tested with version 4.0)

## Setup

1. Install python 3, if you don't have it already

2. TODO: Install Build Tools?

3. Run the following command to install the required python packages:

   ```batch
   python3 -m pip install -r requirements.txt
   ```

4. Copy the file`pywintypesXX.dll` (XX corresponds to your python's version, for example: `pywintypes38.dll`) from `<Python Install Folder>\site-packages\pywin32_system32` to `<Python Install Folder>\Lib\site-packages\win32`.

   * This step fixes a bug in python's windows service implementation. You might not need it, but I encountered it with the setups I used.

5. You now should be ready to run the script and use it! (see usage below)

## Usage

1. Firstly, update the settings in `settings.py` in the declaration of the variable `__values__` according to the information about your program (for example: SOFTWARE_NAME, PROGRAM, UPDATING_SERVER, ...)

   * You don't have to change everything, but make sure the values corresponds to your program and server (valid PROGRAM name, valid IP for UPDATING_SERVER, available port, etc...)

2.  Create the following folders:

   ```
   C:\Program Files\<SOFTWARE_NAME>
   C:\Program Files\<SOFTWARE_NAME>\Updater
   ```

3. Generate RSA keys using the installer: `python installer.py rsa generate`

   * If you already generated RSA keys, make sure they exist using `python installer.py rsa show`

4. Copy the `settings.json` file created by the installer in `Server\settings.json` to `C:\Program Files\<SOFTWARE_NAME>\Updater\settings.json`

5. Install the service: `python service.py install`

   * If it worked, you should check `services.msc` and find a service called `<SOFTWARE_NAME> Updater`.

6. Run the service: `python service.py`

   * If no error is shown, you should check `services.msc` and make sure the service is `Running`.

7. If everything went correctly, you should now see a `log.txt` file created by the server at `C:\Program Files\<SOFTWARE_NAME>\Updater\log.txt`

   * Make sure no errors were written to the log file.
   * The log file should display a message similar to this one: `27.09.2020 19:53:59 [INFO] run | Waiting for packet...`

8. If you encounter any problem with steps 6-7, you should run `python service.py debug`. This will run the service in debug mode and display information about crashes. Apart from that, you can run `python service.py -h` for more useful commands, and ask google for help.