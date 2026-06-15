#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import winreg
from pathlib import Path

TOOL_NAME   = "extlog"
PARENT_NAME = "01_ialogpack"

SCRIPTS = [
    "extlog.py",
    "extdirlog.py",
]

REG_ENTRIES = [
    (r"Software\Classes\*\shell", "4_extlog"),
    (r"Software\Classes\Directory\shell", "5_extdirlog"),
    (r"Software\Classes\Directory\Background\shell", "5_extdirlog"),
]

def get_dst(script_name):
    return Path(os.environ["USERPROFILE"]) / ".ialogpack" / script_name

def remove_script(script_name):
    dst = get_dst(script_name)
    if dst.exists():
        dst.unlink()
        print(f"+ Eliminado: {dst}")
    else:
        print(f"= {script_name} no encontrado")

def remove_submenu(reg_path, menu_number):
    parent_path  = f"{reg_path}\\{PARENT_NAME}"
    submenu_path = f"{parent_path}\\shell\\{menu_number}"
    cmd_path     = f"{submenu_path}\\command"
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, cmd_path)
        print(f"+ Eliminado command: {cmd_path}")
    except Exception:
        pass
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, submenu_path)
        print(f"+ Eliminado submenu: {submenu_path}")
    except Exception:
        pass

def main():
    print("=" * 60)
    print(f"   DESINSTALADOR - {TOOL_NAME.upper()}")
    print("=" * 60)

    print(f"\n[1/2] Eliminando scripts...")
    for script_name in SCRIPTS:
        remove_script(script_name)

    print(f"\n[2/2] Eliminando submenus...")
    for reg_path, menu_number in REG_ENTRIES:
        remove_submenu(reg_path, menu_number)

    print("\n" + "=" * 60)
    print(f"   DESINSTALACION COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")
