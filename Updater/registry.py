
import winreg

import settings


def exists(name):
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, settings.REGISTRY_PATH, 0, winreg.KEY_READ)
        value, reg_type = winreg.QueryValueEx(registry_key, name)
        return True
    except FileNotFoundError:
        return False
    finally:
        winreg.CloseKey(registry_key)


def delete(name):
    registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, settings.REGISTRY_PATH, 0, winreg.KEY_WRITE)
    winreg.DeleteValue(registry_key, name)
    winreg.CloseKey(registry_key)


def get_all_sub_values():
    registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, settings.REGISTRY_PATH, 0, winreg.KEY_READ)
    items_count = winreg.QueryInfoKey(registry_key)[1]

    items = []
    for i in range(items_count):
        item = winreg.EnumValue(registry_key, i)[0]
        items.append(item)

    winreg.CloseKey(registry_key)
    return items


def get_value(name):
    registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, settings.REGISTRY_PATH, 0, winreg.KEY_READ)
    value, reg_type = winreg.QueryValueEx(registry_key, name)
    winreg.CloseKey(registry_key)

    if reg_type == winreg.REG_DWORD:
        value = int(value)
    elif reg_type == winreg.REG_QWORD:
        value = int(value)
    elif reg_type == winreg.REG_BINARY:
        value = int.from_bytes(value, "big")

    return value


def set_value(name, value):
    registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, settings.REGISTRY_PATH, 0, winreg.KEY_WRITE)

    if type(value) is int:
        if value < 2 ** 32:
            reg_type = winreg.REG_DWORD
        elif value < 2 ** 64:
            reg_type = winreg.REG_QWORD
        else:
            reg_type = winreg.REG_BINARY
            value = value.to_bytes((value.bit_length() + 7) // 8, "big")
    else:
        reg_type = winreg.REG_SZ

    winreg.SetValueEx(registry_key, name, 0, reg_type, value)
    winreg.CloseKey(registry_key)
