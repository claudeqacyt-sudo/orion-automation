# Guía de instalación desde cero

Seguí estos pasos en orden. No hace falta saber programar.

Abrir **PowerShell** (buscar "PowerShell" en el menú Inicio) y ejecutar los comandos de cada paso.

---

## Paso 1 — Instalar Python

```powershell
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
```

Esto descarga e instala Python 3.12 automáticamente.  
Cuando termine, **cerrar y volver a abrir PowerShell**.

**Verificar que funcionó:**
```powershell
python --version
```
Debe mostrar: `Python 3.12.x`

---

## Paso 2 — Instalar Git

```powershell
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
```

Cuando termine, **cerrar y volver a abrir PowerShell**.

**Verificar que funcionó:**
```powershell
git --version
```
Debe mostrar: `git version 2.x.x`

---

## Paso 3 — Descargar el proyecto

```powershell
cd $env:USERPROFILE\Desktop
git clone https://github.com/claudeqacyt-sudo/orion-automation.git
cd orion-automation
```

Esto descarga el proyecto en una carpeta llamada `orion-automation` en el Escritorio.

---

## Paso 4 — Preparar el entorno

Ejecutar estos comandos uno por uno (dentro de la carpeta `orion-automation`):

```powershell
# Crear entorno virtual
python -m venv venv
```

```powershell
# Habilitar scripts en PowerShell (solo la primera vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Cuando pregunte, escribir `S` y presionar Enter.

```powershell
# Activar el entorno virtual
venv\Scripts\activate
```
El prompt cambia y aparece `(venv)` al inicio — eso indica que está activo.

```powershell
# Instalar las dependencias
pip install -r requirements.txt
```
Esto puede tardar 1-2 minutos.

```powershell
# Instalar el browser
playwright install chromium
```
Esto puede tardar 1-2 minutos (descarga ~170 MB).

---

## Paso 5 — Configurar las credenciales

```powershell
# Crear el archivo de configuración
cp .env.example .env
```

```powershell
# Abrir el archivo para editarlo
notepad .env
```

En el Bloc de Notas, modificar estas tres líneas con los datos reales:
```
ORION_BASE_URL=https://vm-2k22-er-01.orioncontactcenter.com.ar
ADMIN_USERNAME=tu_usuario
ADMIN_PASSWORD=tu_contraseña
```

Guardar con **Ctrl+S** y cerrar el Bloc de Notas.

---

## Paso 6 — Conectarse a la VPN

Conectarse a la VPN antes de ejecutar los tests.  
Los tests se conectan al servidor Orion en la red interna — sin VPN no funcionan.

---

## Paso 7 — Ejecutar los tests

```powershell
python -m pytest tests/regression/ -v
```

Se abre un browser automáticamente y se ven los tests corriendo.  
Al finalizar muestra un resumen como este:

```
57 passed in 420s (0:07:00)
```

El reporte detallado queda en `reports\report.html` — hacer doble clic para abrirlo en el navegador.

---

## La próxima vez

La instalación (pasos 1 al 5) se hace **una sola vez**.  
Las próximas veces solo hace falta:

```powershell
# Abrir PowerShell y navegar al proyecto
cd $env:USERPROFILE\Desktop\orion-automation

# Activar el entorno virtual
venv\Scripts\activate

# Conectarse a la VPN y ejecutar
python -m pytest tests/regression/ -v
```

---

## Algo salió mal?

| Error | Solución |
|---|---|
| `python` no se reconoce | Cerrar y reabrir PowerShell después de instalar |
| `git` no se reconoce | Cerrar y reabrir PowerShell después de instalar |
| `winget` no se reconoce | Actualizar Windows desde Configuración → Windows Update |
| Error de permisos al activar venv | Ejecutar `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| No puede conectar al servidor | Verificar que la VPN está activa |
| Tests fallan por conteos incorrectos | El sistema Orion tiene datos distintos a los esperados |
