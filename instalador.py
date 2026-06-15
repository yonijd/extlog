#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path

__version__ = "1.1.0"

TOOL_NAME   = "extlog"
EXTLOG_SCRIPT = "extlog.py"
EXTDIRLOG_SCRIPT = "extdirlog.py"

PARENT_NAME = "01_ialogpack"
TOOLS = [
    {
        "script": EXTLOG_SCRIPT,
        "menu_number": "4_extlog",
        "label": "Analizar Archivo (extlog)",
        "icon": "imageres.dll,78",
        "locations": [(r"Software\Classes\*\shell", "%1")],
    },
    {
        "script": EXTDIRLOG_SCRIPT,
        "menu_number": "5_extdirlog",
        "label": "Analizar Archivos de Carpeta (extdirlog)",
        "icon": "imageres.dll,22",
        "locations": [
            (r"Software\Classes\Directory\shell", "%1"),
            (r"Software\Classes\Directory\Background\shell", "%V"),
        ],
    },
]

DEPS_RECOMMENDED = [
    ("pillow",  "PIL",    "imagenes jpg, png, gif, bmp, webp"),
    ("pypdf",   "pypdf",  "archivos PDF"),
]
DEPS_OPTIONAL = [
    ("rarfile", "rarfile", "archivos RAR  (requiere WinRAR instalado)"),
]

def check_deps():
    print("\n[4/4] Verificando dependencias...")

    faltantes = []
    for pkg, imp, desc in DEPS_RECOMMENDED:
        try:
            __import__(imp)
            print(f"  [OK] {pkg:<12} - {desc}")
        except ImportError:
            print(f"  [--] {pkg:<12} - {desc}  << RECOMENDADA")
            faltantes.append((pkg, imp, desc))

    for pkg, imp, desc in DEPS_OPTIONAL:
        try:
            __import__(imp)
            print(f"  [OK] {pkg:<12} - {desc}")
        except ImportError:
            print(f"  [  ] {pkg:<12} - {desc}  (opcional)")

    if not faltantes:
        print("\n  Todas las dependencias recomendadas estan instaladas.")
        return

    print(f"\n  Faltan {len(faltantes)} dependencia(s) recomendada(s).")
    resp = input("  Instalar ahora? (s/N): ").strip().lower()
    if resp != "s":
        print("  Podra instalarlas despues con: pip install pillow pypdf")
        return

    for pkg, imp, desc in faltantes:
        print(f"\n  Instalando {pkg}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  [+] {pkg} instalado correctamente.")
        else:
            print(f"  [!] Error al instalar {pkg}:")
            print(f"      {result.stderr.strip()[:120]}")

def get_paths():
    profile  = Path(os.environ["USERPROFILE"])
    prod_dir = profile / ".ialogpack"
    logs_dir = prod_dir / "logs"
    src_dir  = Path(__file__).parent
    return src_dir, prod_dir, logs_dir

def copy_scripts(src_dir, prod_dir, logs_dir):
    prod_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    copied = {}
    for tool in TOOLS:
        script = tool["script"]
        src = src_dir / script
        dst = prod_dir / script
        if not src.exists():
            print(f"ERROR: No se encuentra {script}")
            sys.exit(1)
        shutil.copy2(src, dst)
        copied[script] = dst
        print(f"+ {script} copiado a: {dst}")
    return copied

def ensure_parent_menu(reg_path):
    parent_path  = f"{reg_path}\\{PARENT_NAME}"
    created = False
    try:
        parent_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, parent_path, 0, winreg.KEY_WRITE)
    except FileNotFoundError:
        parent_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, parent_path, 0, winreg.KEY_WRITE)
        created = True
    winreg.SetValueEx(parent_key, "MUIVerb",                0, winreg.REG_SZ, "IALogPack")
    winreg.SetValueEx(parent_key, "Icon",                   0, winreg.REG_SZ, "cmd.exe")
    winreg.SetValueEx(parent_key, "SubCommands",            0, winreg.REG_SZ, "")
    try:
        winreg.DeleteValue(parent_key, "ExtendedSubCommandsKey")
    except FileNotFoundError:
        pass
    winreg.CloseKey(parent_key)
    shell_path = f"{parent_path}\\shell"
    shell_key  = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, shell_path, 0, winreg.KEY_WRITE)
    winreg.CloseKey(shell_key)
    status = "creado" if created else "actualizado"
    print(f"+ Menu padre {status}: {parent_path}")

def register_submenu(reg_path, var, tool, dst):
    cmd          = f'cmd.exe /k python "{dst}" "{var}"'
    parent_path  = f"{reg_path}\\{PARENT_NAME}"
    submenu_path = f"{parent_path}\\shell\\{tool['menu_number']}"
    cmd_path     = f"{submenu_path}\\command"
    submenu_key  = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, submenu_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(submenu_key, "",     0, winreg.REG_SZ, tool["label"])
    winreg.SetValueEx(submenu_key, "Icon", 0, winreg.REG_SZ, tool["icon"])
    winreg.CloseKey(submenu_key)
    cmd_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, cmd_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(cmd_key)
    print(f"+ Submenu registrado: {submenu_path} (var: {var})")

def main():
    print("=" * 60)
    print(f"   INSTALADOR - {TOOL_NAME.upper()} v{__version__}")
    print("=" * 60)

    src_dir, prod_dir, logs_dir = get_paths()

    print(f"\n[1/3] Copiando scripts...")
    copied = copy_scripts(src_dir, prod_dir, logs_dir)

    for tool in TOOLS:
        dst = copied[tool["script"]]
        for reg_path, var in tool["locations"]:
            print(f"\n[2/3] Verificando menu padre en: {reg_path}")
            ensure_parent_menu(reg_path)
            print(f"[3/3] Registrando submenu...")
            register_submenu(reg_path, var, tool, dst)

    check_deps()

    print("\n" + "=" * 60)
    print(f"   INSTALACION COMPLETADA - {TOOL_NAME.upper()}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")
