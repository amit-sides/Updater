from cx_Freeze import setup, Executable

options = {
    'build_exe': {
        'includes': ["win32timezone"],
        "include_msvcr": True
    }
}


executables = [
    Executable('service.py', base='Console')
]

setup(name='Updater',
      version='1.0',
      executables=executables,
      options=options
      )