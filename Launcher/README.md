# Launcher

This program is the **launcher** of the installed program. meaning, the user should run this program when they want to run the installed program.

The launcher contains an update for the installed program. If it detects the program runs an old version, it automatically updates the program with a neat progress bar:

![update.png](screenshots\update.png)

# Creating The Launcher

When the developer creates the program, or when they want to deploy an update, they firstly need to create the launcher for it.

## Launcher for new program

Let's assume the developer has just created a new program called `Foo`, and all it's files are stored at `C:\Program Files\Foo`, including the executable which is `foo.exe`. Creating the launcher for the new program is as easy as running these commands:

```
pip3 install -r requirements.txt
python3 launcher_creator.py "C:\Program Files\Foo" foo.exe
```

## Launcher for update

When the developer wants to deploy an update, they need to recreate the launcher again the same way they did last time, and replace the new launcher with the old launcher in the end users' computers. If we consider the example for before, after the developer has updated the program's files in `C:\Program Files\Foo`, all they need to do is run this command again:

```
python3 launcher_creator.py "C:\Program Files\Foo" foo.exe
```

# Implementation

In-order to fully understand the launcher's work, I recommend you to take a look at it's source code, it's really not that long. But here are a few points I consider worth mentioning:

* Since the launcher is a python code packed as executable, using `PyInstaller`, it has a slow startup, and somewhat slow running time. But since it's not too terrible, I think it's fine (especially because it really does something only when an update is available).
* Sometimes `Windows Defender` (and maybe other AVs too) detects executables created by `PyInstaller` as suspicious, and as a result it scans them. This behavior causes the program to run **extremely** slow. So if it happens, make sure to disable your AV or set the launcher as exception.
  * This reason is the main reason why no one should ever use it in a real application, but for an education project it's a nice and quick implementation.
* The launcher detects a new update by calculating a hash of the entire program's directory (which includes all the files), and comparing it to a hash stored inside it (which was calculated by the developer when the launcher was created). This means settings and configurations should not be stored in it. Consider using `%AppData%` instead.
* The update files are stored inside the launcher as a long string of encoded base64 which represent a zip file. When the launcher applies a new update, it extracts all the files in the zip file to the programs directory (overriding old files).