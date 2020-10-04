from cx_Freeze import setup, Executable

gui = Executable(
            script="ex.py",
            base="Win32GUI"
            )

build_exe_options = dict(
                        include_files = ["text.txt"]
                        )

setup(
    name = "ExampleProgram",
    version = "1.0",
    description = "Example Program yey",
    options = dict(build_exe=build_exe_options),
    executables = [gui]
    )