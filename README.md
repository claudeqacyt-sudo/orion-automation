# Orion Contact Center — QA Automation

Suite de regresión automatizada para **Orion Contact Center v7.0** (CYT Comunicaciones).  
Construida con Python + Playwright + pytest.

---

## Requisitos previos

- **Python 3.12** instalado → https://www.python.org/downloads/
- **Git** instalado → https://git-scm.com/download/win
- Acceso a la red donde corre el servidor Orion

---

## Instalación (primera vez)

```bash
# 1. Clonar el repositorio
git clone https://github.com/claudeqacyt-sudo/orion-automation.git
cd orion-automation

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
#    Windows (PowerShell o CMD):
venv\Scripts\activate
#    Mac / Linux:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Instalar el browser de Playwright
playwright install chromium

# 6. Crear el archivo de configuración
#    PowerShell (Windows 11):
cp .env.example .env
#    CMD clásico:
copy .env.example .env
```

> **Nota Windows — PowerShell:** Si al activar el venv aparece un error de permisos,
> ejecutar primero: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 6. Editar el `.env` con los datos reales

Abrir el archivo `.env` y completar:

```
ORION_BASE_URL=https://vm-2k22-er-01.orioncontactcenter.com.ar   # URL del servidor Orion
ADMIN_USERNAME=cyt                        # Usuario administrador
ADMIN_PASSWORD=tu_password                # Contraseña
```

---

## Ejecutar la regresión

```bash
# Activar entorno virtual (si no está activo)
venv\Scripts\activate

# Ejecutar TODA la suite de regresión
python -m pytest tests/regression/ -v

# Ejecutar solo un módulo específico
python -m pytest tests/regression/usuarios/ -v
python -m pytest tests/regression/supervision/ -v
python -m pytest tests/regression/monitor/ -v

# Ejecutar un archivo específico
python -m pytest tests/regression/usuarios/test_gestion_perfiles.py -v

# Ver el browser mientras corre (modo headed)
python -m pytest tests/regression/ -v --headed
```

El reporte HTML se genera automáticamente en `reports/report.html`.

---

## Cobertura actual — Etapa 1 (usuario Administrador)

| Módulo | ID | Tests | Tiempo aprox. |
|---|---|---|---|
| Gestión de Perfiles | USR-001 | 11 | |
| Permisos de Perfiles | USR-002 | 9 | |
| Usuarios de Perfiles | USR-003 | 7 | |
| Usuarios de Clientes | USR-004 | 7 | |
| Bloqueo de Usuarios | USR-005 | 8 | |
| Monitor de Efectividad | MON-001 | 4 | |
| Notificar Usuarios | NTF-001 | 11 | |
| **Total** | | **57 tests** | **~7 min** |

---

## Estructura del proyecto

```
orion-automation/
├── pages/                        # Page Objects (POM)
│   ├── base_page.py              # Clase base
│   ├── login_page.py             # Login / Logout
│   ├── usuarios_page.py          # Modulo Usuarios (USR-001 a USR-005)
│   ├── monitor_page.py           # Monitor de Efectividad (MON-001)
│   └── supervision_page.py       # Supervision: Notificar Usuarios (NTF-001)
├── tests/
│   ├── smoke/                    # Test de humo (login basico)
│   └── regression/
│       ├── usuarios/             # USR-001 a USR-005
│       ├── monitor/              # MON-001
│       └── supervision/          # NTF-001
├── fixtures/
│   └── users.json                # Datos de prueba
├── utils/
│   └── helpers.py
├── conftest.py                   # Fixtures globales (login, sesion compartida)
├── pytest.ini                    # Configuracion de pytest
├── requirements.txt              # Dependencias
└── .env.example                  # Template de variables de entorno
```

---

## Requisitos para que los tests pasen

### Acceso de red
El servidor Orion está en una red interna. La máquina donde se ejecutan los tests debe estar **en la misma red local o conectada por VPN**. No funciona desde internet.

### Estado base del sistema
Los tests verifican datos concretos del sistema. Para que pasen, el servidor Orion debe tener exactamente:

| Dato | Valor esperado |
|---|---|
| Perfiles | 3 (Administrador, Supervisor, Agente) |
| Agentes | 5 (usuarios 1000 al 1004) |
| Clientes | 1 (Cliente generico) |
| Usuarios bloqueados | 0 |

Si se corre contra un servidor Orion con datos distintos, los tests que verifican conteos fallarán. En ese caso hay que ajustar las constantes en los page objects (`pages/usuarios_page.py`, etc.).

### Credenciales
El `.env` debe tener usuario y contraseña de un **administrador** del sistema Orion.

---

## Notas técnicas

- Los tests de regresión usan una **sesión compartida** (login único por ejecución).
- El servidor Orion tiene un **timeout de sesión de 130 segundos**. El conftest maneja esto automáticamente.
- Todos los tests que modifican datos **restauran el estado original** al terminar (try/finally).
- El archivo `.env` **nunca se commitea** — contiene credenciales reales.
