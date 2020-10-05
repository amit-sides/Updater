# Program
This is an example program, used for demonstrating how the Updater works.

This is just a normal python program that displays a GUI prompt message with a version number. The text of the message shown is stored at `text.txt`.

The program should be converted to EXE so all the clients can run it without having python installed. This can be done using cxFreeze (see `Requirements` and `Usage` below on how to do it).

## Requirements

* Windows machine (Tested on Windows 10 Pro - version 2004, OS Build 19041.508)
* Python 3 (Tested on Python 3.8.2 - 64bit)
* Pip for python 3 (Tested with version 20.2.3)
* Python packages (install using requirements.txt):
  * pysimplegui (Tested with version 4.29.0)
  * cx-freeze 6.1 (version 6.2 didn't work correctly for me, but future version might fix the problem) (Tested with version 6.1)

## Setup

1. Install python 3 and pip, if you don't have it already.

3. Run the following command to install the required python packages:

   ```batch
   python3 -m pip install -r requirements.txt
   ```

5. You now should be ready to run the program and use it! (see usage below)

## Usage

1. To make sure the program works, run it: `python3 ex.py`

   * A GUI message should be displayed:

     ![example_program](..\Images\example_program.png)

2. To convert the script to EXE (aka "freeze" it), run the following command: `python3 cxsetup.py build`

3. Assuming the conversion to EXE worked, you should now see a folder under the `build` directory with a familiar name to `exe.win-amd64-3.8` (can be changed according to your system or python version). In this folder you can find all the files needed by the EXE of the script you just froze.

4. To make sure the conversion worked, run the `ex.exe` under `build\exe.win-amd64-3.8\ex.exe` and make sure the same GUI message is displayed.

   * PS, because it takes time to all the python modules to be loaded, the startup time of the EXE can be slower than the startup time of the script (depends on your system capabilities), we can't do much about it...