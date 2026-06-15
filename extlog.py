#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ctypes
import time
import subprocess
import hashlib
import struct
from pathlib import Path
from datetime import datetime

__version__ = "1.0.2"

W = 100
SEP = "  " + "-" * 40

def check_and_install(package, import_name=None):
    name = import_name or package
    try:
        __import__(name)
        return True
    except ImportError:
        print(f"\n  [{package}] no esta instalado.")
        resp = input(f"  Instalar ahora con pip? (s/N): ").strip().lower()
        if resp == "s":
            print(f"  Instalando {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  [+] {package} instalado correctamente.")
                try:
                    __import__(name)
                    return True
                except ImportError:
                    print(f"  [!] No se pudo importar {package} tras instalar.")
                    return False
            else:
                print(f"  [!] Error al instalar {package}.")
                print(f"      {result.stderr.strip()[:120]}")
                return False
        print(f"  Seccion omitida.")
        return False

def resize_and_dock_window():
    try:
        kernel32 = ctypes.windll.kernel32
        user32   = ctypes.windll.user32
        os.system("mode con cols=100 lines=50")
        kernel32.SetConsoleTitleW("ANALISIS DE ARCHIVO - EXTLOG")
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

def header(title):
    return ["", f"  --- {title} ---"]

def get_magic_bytes(path):
    try:
        with open(path, "rb") as f:
            raw = f.read(16)
        return " ".join(f"{b:02X}" for b in raw)
    except Exception:
        return "N/D"

def detect_type_by_magic(magic):
    known = {
        "25 50 44 46": "PDF",
        "50 4B 03 04": "ZIP / Office / JAR",
        "52 61 72 21": "RAR",
        "37 7A BC AF": "7-Zip",
        "1F 8B":       "GZIP",
        "42 5A 68":    "BZIP2",
        "4D 5A":       "Ejecutable PE (EXE/DLL)",
        "7F 45 4C 46": "ELF (Linux)",
        "FF D8 FF":    "JPEG",
        "89 50 4E 47": "PNG",
        "47 49 46 38": "GIF",
        "49 49 2A 00": "TIFF",
        "D0 CF 11 E0": "Office antiguo (doc/xls/ppt)",
        "26 42 4D 4F": "MKV/EBML",
        "00 00 00":    "MP4/MOV (posible)",
        "49 44 33":    "MP3 con ID3",
        "FF FB":       "MP3",
        "4F 67 67 53": "OGG",
        "66 74 79 70": "MP4/M4V",
    }
    for sig, nombre in known.items():
        if magic.startswith(sig):
            return nombre
    return "Desconocido"

def detect_encoding(path):
    try:
        with open(path, "rb") as f:
            raw = f.read(4)
        if raw[:3] == b'\xef\xbb\xbf': return "UTF-8 BOM"
        if raw[:2] == b'\xff\xfe':     return "UTF-16 LE"
        if raw[:2] == b'\xfe\xff':     return "UTF-16 BE"
        for enc in ("utf-8", "latin-1", "cp1252", "cp850"):
            try:
                with open(path, "r", encoding=enc) as f:
                    f.read(1024)
                return enc.upper()
            except Exception:
                continue
        return "Binario/Desconocido"
    except Exception:
        return "N/D"

def compute_hashes(path):
    md5    = hashlib.md5()
    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()
    except Exception:
        return "N/D", "N/D"

def analyze_text(path, ext):
    lines = []
    try:
        enc    = detect_encoding(path)
        py_enc = "utf-8" if "UTF" in enc else "latin-1"
        with open(path, "r", encoding=py_enc, errors="replace") as f:
            all_lines = f.readlines()
        total = len(all_lines)
        lines.append(f"  Encoding     : {enc}")
        lines.append(f"  Total lineas : {total:,}")

        if ext == ".csv":
            header_row = all_lines[0].strip() if all_lines else ""
            cols = len(header_row.split(","))
            lines.append(f"  Columnas CSV : {cols}")
            lines.append(f"  Filas datos  : {total - 1:,}")
            lines.append(f"  Cabecera     : {header_row[:80]}")
        elif ext == ".json":
            import json
            try:
                with open(path, "r", encoding=py_enc, errors="replace") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    lines.append(f"  Tipo JSON    : Objeto")
                    lines.append(f"  Claves raiz  : {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    lines.append(f"  Tipo JSON    : Array")
                    lines.append(f"  Elementos    : {len(data):,}")
            except Exception as e:
                lines.append(f"  JSON parse   : Error - {e}")
        elif ext == ".xml":
            import xml.etree.ElementTree as ET
            try:
                tree = ET.parse(path)
                root_el = tree.getroot()
                lines.append(f"  Tag raiz     : {root_el.tag}")
                lines.append(f"  Hijos dir.   : {len(list(root_el))}")
            except Exception as e:
                lines.append(f"  XML parse    : Error - {e}")

        lines.append("")
        lines.append(f"  Preview (primeras 20 lineas):")
        lines.append(SEP)
        for i, l in enumerate(all_lines[:20], 1):
            lines.append(f"  {i:>3}  {l.rstrip()[:W - 8]}")
        if total > 20:
            lines.append(f"  ... ({total - 20} lineas mas)")
        lines.append(SEP)
    except Exception as e:
        lines.append(f"  Error        : {e}")
    return lines

def analyze_image(path):
    lines = []
    magic = get_magic_bytes(path)
    lines.append(f"  Magic bytes  : {magic}")
    lines.append(f"  Tipo real    : {detect_type_by_magic(magic)}")

    if not check_and_install("pillow", "PIL"):
        lines.append("")
        lines.append(f"  Para mas detalle instalar: pip install pillow")
        return lines
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        img = Image.open(path)
        lines.append(f"  Dimensiones  : {img.width} x {img.height} px")
        lines.append(f"  Modo color   : {img.mode}")
        lines.append(f"  Formato      : {img.format}")
        try:
            dpi = img.info.get("dpi", "N/D")
            lines.append(f"  DPI          : {dpi}")
        except Exception:
            pass
        try:
            exif_data = img._getexif()
            if exif_data:
                lines.append(f"  EXIF:")
                useful = ["Make","Model","DateTime","Software",
                          "ExposureTime","FNumber","ISOSpeedRatings"]
                for tag_id, val in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in useful:
                        lines.append(f"    {tag:<20}: {str(val)[:60]}")
            else:
                lines.append(f"  EXIF         : No disponible")
        except Exception:
            lines.append(f"  EXIF         : No disponible")
    except Exception as e:
        lines.append(f"  Error        : {e}")
    return lines

def analyze_exe(path):
    lines = []
    magic = get_magic_bytes(path)
    lines.append(f"  Magic bytes  : {magic}")

    try:
        with open(path, "rb") as f:
            dos = f.read(64)
        if dos[:2] == b'MZ':
            offset = struct.unpack("<I", dos[60:64])[0]
            with open(path, "rb") as f:
                f.seek(offset + 4)
                machine = struct.unpack("<H", f.read(2))[0]
            arch_map = {0x8664:"x64 (AMD64)",0x014c:"x86 (i386)",
                        0xAA64:"ARM64",0x01c4:"ARM"}
            lines.append(f"  Arquitectura : {arch_map.get(machine, f'0x{machine:04X}')}")
            lines.append(f"  Formato      : PE (Portable Executable)")
        else:
            lines.append(f"  Formato      : No es PE valido")
    except Exception as e:
        lines.append(f"  PE parse     : Error - {e}")

    try:
        import win32api
        info = win32api.GetFileVersionInfo(str(path), "\\")
        ms   = info["FileVersionMS"]
        ls   = info["FileVersionLS"]
        ver  = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
        lines.append(f"  Version      : {ver}")
        try:
            lang, cp = win32api.GetFileVersionInfo(
                str(path), r"\VarFileInfo\Translation")[0]
            key = f"\\StringFileInfo\\{lang:04X}{cp:04X}\\"
            for field in ["CompanyName","FileDescription","ProductName","OriginalFilename"]:
                try:
                    val = win32api.GetFileVersionInfo(str(path), key + field)
                    if val:
                        lines.append(f"  {field:<16}: {val}")
                except Exception:
                    pass
        except Exception:
            pass
    except ImportError:
        lines.append(f"  Para mas detalle instalar: pip install pywin32")
    except Exception:
        lines.append(f"  Version      : Sin informacion de version")
    return lines

def analyze_pdf(path):
    lines = []
    magic = get_magic_bytes(path)
    lines.append(f"  Magic bytes  : {magic}")
    lines.append(f"  Tipo real    : {detect_type_by_magic(magic)}")

    if not check_and_install("pypdf"):
        lines.append("")
        lines.append(f"  Para mas detalle instalar: pip install pypdf")
        return lines
    try:
        import pypdf
        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
        lines.append(f"  Paginas      : {len(reader.pages)}")
        lines.append(f"  Encriptado   : {'Si' if reader.is_encrypted else 'No'}")
        meta = reader.metadata
        if meta:
            for field in ["/Title","/Author","/Creator","/Producer","/CreationDate"]:
                val = meta.get(field, "")
                if val:
                    lines.append(f"  {field[1:]:<14}: {str(val)[:70]}")
    except Exception as e:
        lines.append(f"  Error        : {e}")
    return lines

def analyze_zip(path):
    lines = []
    magic = get_magic_bytes(path)
    lines.append(f"  Magic bytes  : {magic}")
    lines.append(f"  Tipo real    : {detect_type_by_magic(magic)}")
    try:
        import zipfile
        with zipfile.ZipFile(path, "r") as zf:
            entries = zf.infolist()
            total   = len(entries)
            total_c = sum(e.compress_size for e in entries)
            total_u = sum(e.file_size for e in entries)
            ratio   = (1 - total_c / total_u) * 100 if total_u > 0 else 0
            lines.append(f"  Entradas     : {total:,}")
            lines.append(f"  Tam. real    : {format_size(total_u)}")
            lines.append(f"  Tam. comprim.: {format_size(total_c)}")
            lines.append(f"  Ratio compres: {ratio:.1f}%")
            lines.append("")
            lines.append(f"  Contenido (primeras 50 entradas):")
            lines.append(SEP)
            lines.append(f"  {'NOMBRE':<55} {'TAMANO':>10}  FECHA")
            for e in entries[:50]:
                name  = e.filename if len(e.filename) <= 54 else e.filename[:51] + "..."
                fecha = f"{e.date_time[0]}-{e.date_time[1]:02d}-{e.date_time[2]:02d}"
                lines.append(f"  {name:<55} {format_size(e.file_size):>10}  {fecha}")
            if total > 50:
                lines.append(f"  ... ({total - 50} entradas mas)")
            lines.append(SEP)
    except Exception as e:
        lines.append(f"  Error        : {e}")
    return lines

def analyze_rar(path):
    lines = []
    magic = get_magic_bytes(path)
    lines.append(f"  Magic bytes  : {magic}")
    lines.append(f"  Tipo real    : {detect_type_by_magic(magic)}")

    if not check_and_install("rarfile"):
        lines.append("")
        lines.append(f"  Para mas detalle instalar: pip install rarfile")
        lines.append(f"  (requiere WinRAR instalado en el sistema)")
        return lines
    try:
        import rarfile
        with rarfile.RarFile(path) as rf:
            entries = rf.infolist()
            total   = len(entries)
            total_u = sum(e.file_size for e in entries if not e.is_dir())
            lines.append(f"  Entradas     : {total:,}")
            lines.append(f"  Tam. real    : {format_size(total_u)}")
            lines.append("")
            lines.append(f"  Contenido (primeras 50 entradas):")
            lines.append(SEP)
            lines.append(f"  {'NOMBRE':<55} {'TAMANO':>10}")
            for e in entries[:50]:
                name = e.filename if len(e.filename) <= 54 else e.filename[:51] + "..."
                lines.append(f"  {name:<55} {format_size(e.file_size):>10}")
            if total > 50:
                lines.append(f"  ... ({total - 50} entradas mas)")
            lines.append(SEP)
    except Exception as e:
        lines.append(f"  Error        : {e}")
    return lines

def analyze_generic(path):
    lines = []
    magic = get_magic_bytes(path)
    tipo  = detect_type_by_magic(magic)
    lines.append(f"  Magic bytes  : {magic}")
    lines.append(f"  Tipo real    : {tipo}")
    lines.append(f"  Extension    : sin categoria conocida")
    lines.append("")
    lines.append(f"  Este tipo de archivo no tiene analizador especifico.")
    lines.append(f"  Los datos basicos (tamano, fechas, hashes) estan en")
    lines.append(f"  la seccion de metadatos generales.")
    return lines

def build_report(file_path):
    path = Path(file_path)
    now  = datetime.now()
    W2   = W
    lines = []

    lines.append("=" * W2)
    lines.append(f"   REPORTE EXTLOG v{__version__} PARA IA - ANALISIS DE ARCHIVO")
    lines.append("=" * W2)
    lines.append(f"  Archivo      : {path.name}")
    lines.append(f"  Ruta         : {path.parent}")
    lines.append(f"  Fecha/Hora   : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * W2)

    lines += header("METADATOS GENERALES")
    try:
        stat = path.stat()
        lines.append(f"  Nombre       : {path.name}")
        lines.append(f"  Extension    : {path.suffix.lower() if path.suffix else 'Sin extension'}")
        lines.append(f"  Tamano       : {format_size(stat.st_size)} ({stat.st_size:,} bytes)")
        lines.append(f"  Creacion     : {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Modificacion : {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Ultimo acceso: {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}")
        attrs = []
        try:
            import ctypes as ct
            a = ct.windll.kernel32.GetFileAttributesW(str(path))
            if a != -1:
                if a & 0x1:  attrs.append("Solo lectura")
                if a & 0x2:  attrs.append("Oculto")
                if a & 0x4:  attrs.append("Sistema")
                if a & 0x20: attrs.append("Archivo")
        except Exception:
            pass
        lines.append(f"  Atributos    : {', '.join(attrs) if attrs else 'Normal'}")
    except Exception as e:
        lines.append(f"  Error stat   : {e}")

    lines += header("HASHES")
    print("  Calculando hashes...")
    md5, sha256 = compute_hashes(path)
    lines.append(f"  MD5          : {md5}")
    lines.append(f"  SHA256       : {sha256}")

    ext = path.suffix.lower()

    TEXT_EXTS = {".txt",".log",".py",".js",".ts",".html",".css",".php",
                 ".bat",".ps1",".cmd",".sh",".json",".xml",".csv",
                 ".ini",".cfg",".yaml",".yml",".md",".rst",".toml"}
    IMAGE_EXTS = {".jpg",".jpeg",".png",".gif",".bmp",".webp",".ico",".tiff",".tif"}
    EXE_EXTS   = {".exe",".dll",".msi",".ocx",".sys"}
    PDF_EXTS   = {".pdf"}
    ZIP_EXTS   = {".zip",".docx",".xlsx",".pptx",".jar",".apk",".odt"}
    RAR_EXTS   = {".rar"}

    if ext in TEXT_EXTS:
        lines += header("ANALISIS - TEXTO")
        lines += analyze_text(path, ext)
    elif ext in IMAGE_EXTS:
        lines += header("ANALISIS - IMAGEN")
        lines += analyze_image(path)
    elif ext in EXE_EXTS:
        lines += header("ANALISIS - EJECUTABLE")
        lines += analyze_exe(path)
    elif ext in PDF_EXTS:
        lines += header("ANALISIS - PDF")
        lines += analyze_pdf(path)
    elif ext in ZIP_EXTS:
        lines += header("ANALISIS - COMPRIMIDO ZIP")
        lines += analyze_zip(path)
    elif ext in RAR_EXTS:
        lines += header("ANALISIS - COMPRIMIDO RAR")
        lines += analyze_rar(path)
    else:
        lines += header("ANALISIS - TIPO GENERICO")
        lines += analyze_generic(path)

    lines.append("")
    lines.append("=" * W2)
    lines.append(f"  FIN DEL REPORTE EXTLOG v{__version__} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * W2)

    return "\n".join(lines)

def copy_to_clipboard(text):
    try:
        subprocess.run("clip", input=text.encode("utf-8"), check=True, shell=True)
        return True
    except Exception:
        return False

def write_log(file_path, report):
    path       = Path(file_path)
    now        = datetime.now()
    name_clean = "".join([c if c.isalnum() else "_" for c in path.stem])
    log_dir    = Path(os.environ["USERPROFILE"]) / ".ialogpack" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_name   = f"extlog_{name_clean}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
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
    if p.is_file():
        return p
    try:
        import ctypes as ct
        buf = ct.create_unicode_buffer(32768)
        ct.windll.kernel32.GetLongPathNameW(raw, buf, 32768)
        long = buf.value
        if long:
            p2 = Path(long)
            if p2.is_file():
                return p2
    except Exception:
        pass
    return p

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    resize_and_dock_window()

    if len(sys.argv) < 2:
        print("Uso: extlog.py <ruta_archivo>")
        input("\nPresione Enter para salir...")
        sys.exit(1)

    raw_arg = " ".join(sys.argv[1:])
    target  = resolve_path(raw_arg)

    if not target.is_file():
        print(f"Error: No se encontro el archivo.")
        print(f"Ruta recibida: {raw_arg}")
        print(f"Ruta resuelta: {target}")
        input("\nPresione Enter para salir...")
        sys.exit(1)

    print("=" * W)
    print(f"   REPORTE EXTLOG v{__version__} PARA IA - ANALISIS DE ARCHIVO")
    print("=" * W)
    print(f"  Analizando: {target.name}")
    print("  Por favor espere...\n")

    start   = time.time()
    report  = build_report(target)
    elapsed = time.time() - start

    print(report)
    print(f"\n  Tiempo de analisis: {elapsed:.3f} seg")

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
