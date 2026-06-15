#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ctypes
import time
import subprocess
from pathlib import Path
from datetime import datetime
from collections import Counter

__version__ = "1.0.1"

W = 100

def resize_and_dock_window():
    try:
        kernel32 = ctypes.windll.kernel32
        user32   = ctypes.windll.user32
        os.system("mode con cols=100 lines=50")
        kernel32.SetConsoleTitleW("ANALISIS DE CARPETA - DIRLOG")
        time.sleep(0.05)
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            class RECT(ctypes.Structure):
                _fields_ = [("left",ctypes.c_int),("top",ctypes.c_int),
                             ("right",ctypes.c_int),("bottom",ctypes.c_int)]
            rect = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            sw = user32.GetSystemMetrics(0)
            user32.MoveWindow(hwnd, sw - w - 20, 20, w, h, True)
    except Exception:
        pass

def format_size(b):
    if b < 1024:        return f"{b} B"
    elif b < 1024**2:   return f"{b/1024:.2f} KB"
    elif b < 1024**3:   return f"{b/1024**2:.2f} MB"
    else:               return f"{b/1024**3:.2f} GB"

def load_extlog():
    prod_dir    = Path(os.environ["USERPROFILE"]) / ".ialogpack"
    extlog_path = prod_dir / "extlog.py"
    if not extlog_path.exists():
        print(f"[!] No se encontro extlog.py en {prod_dir}")
        print(f"    Instala extlog primero.")
        input("\nPresione Enter para salir...")
        sys.exit(1)
    import importlib.util
    sys.dont_write_bytecode = True
    spec   = importlib.util.spec_from_file_location("extlog", extlog_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def copy_to_clipboard(text):
    try:
        subprocess.run("clip", input=text.encode("utf-8"), check=True, shell=True)
        return True
    except Exception:
        return False

def write_log(folder_path, report):
    root       = Path(folder_path)
    now        = datetime.now()
    name_clean = "".join([c if c.isalnum() else "_" for c in root.name]) if root.name else "raiz"
    log_dir    = Path(os.environ["USERPROFILE"]) / ".ialogpack" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_name   = f"dirlog_{name_clean}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path   = log_dir / log_name
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[+] Log guardado en:")
        print(f"    {log_path}")
    except Exception as e:
        print(f"\n[!] No se pudo guardar el log: {e}")

def resolve_path(raw):
    raw = raw.strip().strip('"').strip("'")
    p = Path(raw)
    if p.is_dir():
        return p
    try:
        import ctypes as ct
        buf = ct.create_unicode_buffer(32768)
        ct.windll.kernel32.GetLongPathNameW(raw, buf, 32768)
        long = buf.value
        if long:
            p2 = Path(long)
            if p2.is_dir():
                return p2
    except Exception:
        pass
    return p

def build_report(folder_path, extlog):
    root  = Path(folder_path)
    now   = datetime.now()
    lines = []

    try:
        all_entries = sorted(root.iterdir(), key=lambda x: (x.is_dir(), x.name.lower()))
    except Exception as e:
        return f"Error al leer carpeta: {e}"

    files   = [e for e in all_entries if e.is_file()]
    folders = [e for e in all_entries if e.is_dir()]

    total_size = 0
    for f in files:
        try:
            total_size += f.stat().st_size
        except Exception:
            pass
    ext_count = Counter(f.suffix.lower() for f in files if f.suffix)

    lines.append("=" * W)
    lines.append(f"   REPORTE DIRLOG v{__version__} PARA IA - ANALISIS DE CARPETA")
    lines.append("=" * W)
    lines.append(f"  Carpeta      : {root.absolute()}")
    lines.append(f"  Fecha/Hora   : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Archivos     : {len(files):,}")
    lines.append(f"  Subcarpetas  : {len(folders):,}")
    lines.append(f"  Tamano total : {format_size(total_size)}")
    top_exts = "  ".join(f"{e}({n})" for e, n in ext_count.most_common(6))
    lines.append(f"  Tipos dom.   : {top_exts if top_exts else 'N/D'}")

    if folders:
        lines.append("")
        lines.append(f"  --- SUBCARPETAS (no analizadas) ---")
        for d in folders:
            try:
                sub_count = sum(1 for _ in d.iterdir())
                lines.append(f"    {d.name:<50} [{sub_count} elementos]")
            except Exception:
                lines.append(f"    {d.name}")

    lines.append("")
    lines.append("=" * W)
    lines.append(f"  ANALISIS INDIVIDUAL - {len(files)} ARCHIVOS")
    lines.append("=" * W)

    for i, f in enumerate(files, 1):
        print(f"  Analizando ({i}/{len(files)}): {f.name}")
        lines.append("")
        lines.append("#" * W)
        lines.append(f"  ARCHIVO {i}/{len(files)}: {f.name}")
        lines.append("#" * W)
        try:
            report_file = extlog.build_report(f)
            lines.append(report_file)
        except Exception as e:
            lines.append(f"  Error al analizar: {e}")

    lines.append("")
    lines.append("=" * W)
    lines.append(f"  FIN DEL REPORTE DIRLOG v{__version__} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Total archivos analizados: {len(files):,}")
    lines.append("=" * W)

    return "\n".join(lines)

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    resize_and_dock_window()

    if len(sys.argv) < 2:
        print("Uso: dirlog.py <ruta_carpeta>")
        input("\nPresione Enter para salir...")
        sys.exit(1)

    raw_arg = " ".join(sys.argv[1:])
    target  = resolve_path(raw_arg)

    if not target.is_dir():
        print(f"Error: No se encontro la carpeta.")
        print(f"Ruta recibida: {raw_arg}")
        input("\nPresione Enter para salir...")
        sys.exit(1)

    print("=" * W)
    print(f"   REPORTE DIRLOG v{__version__} PARA IA - ANALISIS DE CARPETA")
    print("=" * W)
    print(f"  Carpeta: {target.absolute()}")
    print("  Cargando extlog...")

    extlog = load_extlog()

    print("  Analizando archivos...\n")

    start   = time.time()
    report  = build_report(target, extlog)
    elapsed = time.time() - start

    print(report)
    print(f"\n  Tiempo total: {elapsed:.3f} seg")

    write_log(target, report)

    ok = copy_to_clipboard(report)
    print("\n[+] Reporte copiado al portapapeles." if ok else "\n[!] No se pudo copiar al portapapeles.")

    print("")
    input("Presione Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")
