# Orion Contact Center — QA Automation

Suite de automatización de regresión para el sistema **Orion Contact Center v7.0** de CYT Comunicaciones.

## Stack tecnológico
- **Python** 3.12
- **Playwright** — Framework de automatización web
- **pytest** — Test runner
- **pytest-playwright** — Integración Playwright + pytest
- **pandas / openpyxl** — Validación de reportes exportados (CSV/Excel)
- **pytest-html** — Reportes HTML

## Estructura del proyecto

```
orion-automation/
├── tests/
│   ├── smoke/                   # Tests de humo (login, acceso básico)
│   └── regression/
│       ├── monitor/             # Monitor Online y Monitores Globales
│       ├── reports/             # Todos los reportes (IVR, Campañas, Discador)
│       ├── config/              # Configuración (Agentes, Colas, Habilidades)
│       └── campaigns/           # Campañas, Lotes, Segmentación
├── pages/                       # Page Object Model (POM)
│   ├── base_page.py
│   ├── login_page.py
│   └── monitor_page.py
├── fixtures/                    # Datos de prueba
│   └── users.json
├── utils/                       # Helpers y utilidades
│   └── helpers.py
├── reports/                     # Reportes generados (git-ignorado)
├── conftest.py                  # Configuración global de pytest
├── pytest.ini                   # Configuración de pytest
├── requirements.txt             # Dependencias Python
├── .env.example                 # Template de variables de entorno
└── .env                         # Variables de entorno (NO commitear)
```

## Configuración inicial

### 1. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar variables de entorno
```bash
copy .env.example .env
# Editar .env con la URL real y credenciales del sistema Orion
```

### 3. Completar selectores CSS
Abrir el sistema Orion con DevTools (F12) e inspeccionar los elementos para
actualizar los selectores en los archivos de `pages/`.

## Ejecución de tests

```bash
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar TODOS los tests
pytest

# Solo tests de SMOKE (para verificar que el ambiente funciona)
pytest -m smoke

# POC: Monitor Online
pytest tests/regression/monitor/test_monitor_online.py -v

# Con browser visible (no headless)
pytest --headed

# Con reporte HTML
pytest --html=reports/report.html --self-contained-html
```

## POC — Prueba de Concepto

El primer caso implementado es:
**REG-MON-001**: Login → Monitor Online → Verificar tabla de agentes → Logout

Ver: `tests/regression/monitor/test_monitor_online.py`

## Pasos pendientes antes de ejecutar
1. Completar `ORION_BASE_URL` en el archivo `.env`
2. Completar credenciales en `.env`
3. Ajustar selectores CSS en `pages/login_page.py` inspeccionando el HTML real
4. Ajustar selectores CSS en `pages/monitor_page.py`
5. Completar columnas reales en `MonitorPage.EXPECTED_COLUMNS`
