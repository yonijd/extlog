# ⚠️ ADVERTENCIA IMPORTANTE

## EXTLOG - Análisis de un solo archivo

**Sin advertencias especiales** - funciona bien con archivos individuales de cualquier tamaño (hasta 2GB).

---

## EXTDIRLOG - Análisis masivo de carpetas

### ⚠️ ¡CUIDADO! ⚠️

**NO USES EXTDIRLOG EN CARPETAS CON MUCHOS ARCHIVOS**

| Tamaño de carpeta | Tiempo estimado | Tamaño del reporte | Recomendación |
|-------------------|----------------|--------------------|---------------|
| < 20 archivos | 10-30 seg | ~1-2 MB | ✅ Seguro |
| 20-50 archivos | 1-3 minutos | ~2-5 MB | ⚠️ Con precaución |
| 50-100 archivos | 3-10 minutos | ~5-10 MB | ❌ No recomendado |
| > 100 archivos | > 20 minutos | > 10 MB | 🚫 PELIGROSO |

### Riesgos de usar en carpetas grandes:

1. **Tiempo excesivo** - Puede tardar horas
2. **Reporte gigantesco** - Puede saturar la memoria
3. **Portapapeles bloqueado** - Ctrl+V puede fallar o congelar el sistema
4. **IA no podrá procesarlo** - Excede los límites de tokens (ej: ChatGPT 128K tokens ≈ 200KB de texto)
5. **Puede colapsar la consola** - Algunos terminales no manejan bien megabytes de texto

### Alternativas recomendadas:

- **Para entender la estructura** → Usa `deeplog` o `listlog` (rápido, liviano)
- **Para analizar archivos específicos** → Usa `extlog` individualmente
- **Para carpetas grandes** → Usa `deeplog` primero, luego `extlog` selectivo

---

# EXTLOG - Análisis Profundo de un Archivo

## Descripción

Herramienta de análisis forense que examina en profundidad un solo archivo, extrayendo metadatos, hashes y contenido específico según su tipo.

## Características

- **Metadatos completos**: Tamaño, fechas (creación, modificación, acceso), atributos
- **Hashes criptográficos**: MD5 y SHA256
- **Detección por magic bytes**: Identifica el tipo real (no solo extensión)
- **Análisis específico por tipo**:
  - Texto: encoding, líneas, preview (20 líneas), parsing CSV/JSON/XML
  - Imagen: dimensiones, modo color, DPI, EXIF (cámara, fecha, etc.)
  - Ejecutable: arquitectura (x86/x64/ARM), versión, metadata PE
  - PDF: páginas, encriptación, metadata (título, autor)
  - ZIP/RAR: contenido, ratio compresión
- **Auto-copia al portapapeles**: Reporte listo para pegar en IA
- **Guardado automático**: Logs en `%USERPROFILE%\.ialogpack\logs\`

## Dependencias

### Recomendadas (se instalan automáticamente si falta):
- `pillow` - Análisis de imágenes (dimensiones, EXIF)
- `pypdf` - Análisis de PDFs (páginas, metadata)

### Opcionales:
- `rarfile` - Análisis de archivos RAR (requiere WinRAR instalado)
- `pywin32` - Metadata extendida de ejecutables

**Sin dependencias obligatorias** - Si faltan, el script pregunta si instalarlas.

## Instalación

```cmd
python instalador.py
```

## Uso

### Línea de comandos
```cmd
extlog.py "C:\ruta\archivo.pdf"
```

### Menú contextual (Windows)
1. Click derecho en **cualquier archivo**
2. Ir a `IALogPack`
3. Seleccionar `4_extlog`

## Ejemplo de salida

```
====================================================================================================
   REPORTE EXTLOG v1.0.2 PARA IA - ANALISIS DE ARCHIVO
====================================================================================================
  Archivo      : documento.pdf
  Ruta         : C:\Documentos
  Fecha/Hora   : 2026-06-14 10:30:00
====================================================================================================

  --- METADATOS GENERALES ---
  Nombre       : documento.pdf
  Extension    : .pdf
  Tamano       : 2.45 MB (2,567,890 bytes)
  Creacion     : 2026-06-10 08:00:00
  Modificacion : 2026-06-14 09:00:00
  Atributos    : Archivo

  --- HASHES ---
  MD5          : d41d8cd98f00b204e9800998ecf8427e
  SHA256       : e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

  --- ANALISIS - PDF ---
  Magic bytes  : 25 50 44 46 2D 31 2E 35...
  Tipo real    : PDF
  Paginas      : 15
  Encriptado   : No
  Title        : Informe Tecnico
  Author       : Juan Perez

====================================================================================================
  FIN DEL REPORTE EXTLOG v1.0.2 - 2026-06-14 10:30:05
====================================================================================================
```

## Tipos de archivo soportados

| Categoría | Extensiones |
|-----------|-------------|
| Texto | .txt, .log, .py, .js, .json, .xml, .csv, .md, .yaml, .toml, etc. |
| Imagen | .jpg, .png, .gif, .bmp, .webp, .ico, .tiff |
| Ejecutable | .exe, .dll, .msi, .ocx, .sys |
| PDF | .pdf |
| Comprimido | .zip, .rar, .jar, .apk, .docx, .xlsx, .pptx |
| Genérico | Cualquier otro (detección por magic bytes) |

## Archivos generados

Los logs se guardan en:
```
%USERPROFILE%\.ialogpack\logs\extlog_nombre_archivo_YYYY-MM-DD_HH-MM-SS.log
```

## Desinstalación

Ejecutar `desinstalador.py` desde esta carpeta.

---

# EXTDIRLOG - Análisis Masivo de una Carpeta

## ⚠️ REPETIMOS LA ADVERTENCIA ⚠️

**SOLO PARA CARPETAS PEQUEÑAS (< 20 ARCHIVOS)**

## Descripción

Aplica `extlog` a **cada archivo** dentro de una carpeta, concatenando todos los reportes en uno solo.

## Características

- Escanea todos los archivos de una carpeta (solo raíz, no recursivo)
- Genera reporte individual por cada archivo usando `extlog`
- Muestra resumen de la carpeta (total de archivos, carpetas, tamaño, tipos dominantes)
- Copia automáticamente al portapapeles (⚠️ cuidado con archivos grandes)

## Dependencias

- **`extlog.py`** debe estar instalado en `%USERPROFILE%\.ialogpack\`
- Las dependencias de `extlog` (pillow, pypdf) son heredadas

## Instalación

Se instala **junto con `extlog`** usando el mismo instalador:
```cmd
python instalador.py
```

## Uso

### Línea de comandos
```cmd
extdirlog.py "C:\ruta\carpeta"
```

### Menú contextual (Windows)
1. Click derecho en **carpeta**
2. Ir a `IALogPack`
3. Seleccionar `5_extdirlog`

## Ejemplo de salida (carpeta pequeña)

```
====================================================================================================
   REPORTE DIRLOG v1.0.1 PARA IA - ANALISIS DE CARPETA
====================================================================================================
  Carpeta      : C:\Proyectos\config
  Archivos     : 3
  Subcarpetas  : 0
  Tamano total : 45.23 KB

====================================================================================================
  ANALISIS INDIVIDUAL - 3 ARCHIVOS
====================================================================================================

####################################################################################################
  ARCHIVO 1/3: config.json
####################################################################################################
[Reporte completo de extlog para config.json]

####################################################################################################
  ARCHIVO 2/3: settings.ini
####################################################################################################
[Reporte completo de extlog para settings.ini]

...
```

## Comparativa

| Herramienta | Qué analiza | Velocidad | Reporte | Recomendado para |
|-------------|-------------|-----------|---------|------------------|
| **extlog** | 1 archivo | Rápido | Detallado | Archivos individuales |
| **extdirlog** | Todos los archivos de una carpeta | Muy lento | Gigantesco | < 20 archivos |
| **deeplog** | Estructura de carpetas | Lento | Mediano | Entender organización |
| **listlog** | Listado de nombres | Rápido | Pequeño | Vista rápida |

## Limitaciones

- ❌ **MUY LENTO** en carpetas con muchos archivos
- ❌ **Depende de `extlog` instalado**
- ❌ **No analiza subcarpetas** (solo raíz)
- ❌ **Reporte gigantesco** en carpetas grandes
- ❌ **Portapapeles puede fallar** con reportes > 10 MB
- ❌ **No hay barra de progreso**

## Desinstalación

Ejecutar `desinstalador.py` desde esta carpeta (elimina ambos: `extlog.py` y `extdirlog.py`).

---

## Licencia

MIT

## Versión

- extlog: 1.0.2
- extdirlog: 1.0.1

---

*Estas herramientas forman parte del paquete IALogPack.*
