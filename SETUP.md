# Guía de instalación desde cero

Seguí estos pasos en orden. No hace falta saber programar.

---

## Paso 1 — Instalar Python

1. Ir a **https://www.python.org/downloads/**
2. Hacer clic en el botón amarillo **"Download Python 3.12.x"**
3. Ejecutar el instalador descargado
4. **IMPORTANTE:** En la primera pantalla del instalador, tildar la opción **"Add Python to PATH"** antes de hacer clic en Install
5. Hacer clic en **"Install Now"**
6. Cuando termine, hacer clic en **"Close"**

**Verificar que funcionó:**
Abrir PowerShell (buscar "PowerShell" en el menú Inicio) y escribir:
```
python --version
```
Debe mostrar algo como `Python 3.12.x`

---

## Paso 2 — Instalar Git

1. Ir a **https://git-scm.com/download/win**
2. Descargar el instalador de 64-bit
3. Ejecutarlo y hacer clic en **"Next"** en todas las pantallas (las opciones por defecto están bien)
4. Al final hacer clic en **"Install"** y luego **"Finish"**

**Verificar que funcionó:**
En PowerShell escribir:
```
git --version
```
Debe mostrar algo como `git version 2.x.x`

> **Nota:** Si PowerShell da un error después de instalar Git, cerrarlo y volver a abrirlo.

---

## Paso 3 — Descargar el proyecto

En PowerShell, ejecutar estos comandos uno por uno:

```powershell
cd $env:USERPROFILE\Desktop
git clone https://github.com/claudeqacyt-sudo/orion-automation.git
cd orion-automation
```

Esto descarga el proyecto en una carpeta llamada `orion-automation` en el Escritorio.

---

## Paso 4 — Preparar el entorno

Seguir ejecutando en PowerShell (dentro de la carpeta `orion-automation`):

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
El prompt cambia y aparece `(venv)` al inicio — eso significa que está activo.

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

Ahora abrir el archivo `.env` con el Bloc de Notas:
```powershell
notepad .env
```

Modificar las siguientes líneas con los datos reales:
```
ORION_BASE_URL=http://10.1.10.150:8080
ADMIN_USERNAME=tu_usuario
ADMIN_PASSWORD=tu_contraseña
```

Guardar el archivo (Ctrl+S) y cerrar el Bloc de Notas.

---

## Paso 6 — Conectarse a la VPN

Conectarse a la VPN antes de ejecutar los tests.  
Los tests se conectan al servidor Orion en la red interna — sin VPN no van a funcionar.

---

## Paso 7 — Ejecutar los tests

Con la VPN activa y el entorno virtual activado `(venv)`, ejecutar:

```powershell
python -m pytest tests/regression/ -v
```

Se abre un browser automáticamente y se ven los tests corriendo.  
Al finalizar muestra un resumen como este:

```
57 passed in 420s (0:07:00)
```

El reporte detallado queda en: `reports\report.html`  
(hacer doble clic para abrirlo en el navegador)

---

## La próxima vez

La instalación (pasos 1 al 5) se hace una sola vez.  
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
| `python` no se reconoce | Reinstalar Python tildando "Add to PATH" |
| `git` no se reconoce | Cerrar y reabrir PowerShell después de instalar Git |
| Error de permisos al activar venv | Ejecutar `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| No puede conectar al servidor | Verificar que la VPN está activa |
| Tests fallan por conteos incorrectos | El sistema Orion tiene datos distintos a los esperados |
