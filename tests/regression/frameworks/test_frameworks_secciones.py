"""
tests/regression/frameworks/test_frameworks_secciones.py
Suite de regresion — Frameworks (puerto :444): TODAS las secciones

Verifica que cada pagina del modulo Orion Contact Center (Frameworks) carga
correctamente: sin errores de servidor y con contenido basico presente.

Secciones cubiertas:
  Monitor     — Monitores Globales, Monitor Chat, Online (fn), Lotes (fn)
  Reportes    — IVR, Desbordes, Nivel Servicio, Productividad (3),
                Ocupacion, Log Actividades, Por Agente, Mensual, Habilidades,
                Discador, Duracion Efectiva, Personalizados
  ACD         — Grupos y Agentes, Programacion, Colas ACD, Perfiles Recepcion,
                Perfiles Discado, Asignacion Discado, Rutas, Ruteo Inteligente,
                Pausas, Habilidades Config, Habilidades Asignacion
  Campanas    — ABM Campanas, Status, Subcategorias, Sincronizar,
                Segmentacion (Importar, Configurar, Borrar),
                Lotes (Crear, Cerrar, Borrar, Reagendar)
  Configurar  — Clientes, Prefijos, Codigos Finalizacion, Niveles Usuarios,
                Internos ABM, Internos Alta Masiva, Internos Baja Masiva,
                Monitores JS (fn: 4 funciones)
  Grabador    — /grabador.aspx
  Ayuda       — /documentacion.aspx
"""
import time

import pytest

pytestmark = [pytest.mark.regression, pytest.mark.frameworks]

FW_PORT = 444


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def fw_base(base_url):
    return f"{base_url.rstrip('/')}:{FW_PORT}"


@pytest.fixture(scope="module")
def fw_tab(shared_page, base_url, admin_credentials):
    """
    Abre el modulo Frameworks (puerto 444) UNA VEZ para todos los tests de secciones.
    Reutiliza la sesion cyt de shared_page.
    """
    from pages.login_page import LoginPage as _LP

    # Restaurar sesion cyt si fue alterada por tests previos
    for _intento in range(3):
        try:
            shared_page.goto(f"{base_url}/admincontactos", wait_until="load", timeout=20000)
        except Exception:
            pass
        if "/login" in shared_page.url:
            _lp = _LP(shared_page)
            try:
                _lp.navigate(base_url)
                _lp.login(admin_credentials["username"], admin_credentials["password"])
            except Exception:
                pass
            time.sleep(2)
        try:
            shared_page.locator("#accionEjecutar_4").wait_for(state="visible", timeout=15000)
            break
        except Exception:
            time.sleep(3)

    # Abrir Frameworks: Supervision > Orion Contact Center
    shared_page.evaluate("document.querySelector('#accionEjecutar_4').click()")
    time.sleep(1.5)
    with shared_page.context.expect_page(timeout=15000) as tab_info:
        shared_page.evaluate("document.querySelector('#accionEjecutar_44').click()")
    tab = tab_info.value
    tab.wait_for_load_state("domcontentloaded", timeout=20000)
    time.sleep(1)

    yield tab

    try:
        tab.close()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _navegar_verificar(tab, fw_base: str, path: str, descripcion: str = "") -> None:
    """
    Navega a fw_base+path y verifica carga basica:
      - Sin error del servidor (500/exception/404/403)
      - Body con contenido suficiente (> 100 chars)
    """
    tab.goto(f"{fw_base}{path}", wait_until="domcontentloaded", timeout=25000)
    time.sleep(0.5)

    body = tab.evaluate(
        "() => document.body ? document.body.innerText.toLowerCase() : ''"
    )
    label = descripcion or path

    assert not any(
        x in body
        for x in ["server error", "exception", "http 404", "http 403", "access denied"]
    ), f"{label}: error del servidor en {tab.url}"

    assert len(body) > 100, f"{label}: pagina parece vacia en {tab.url}"


def _fn_existe_en_inicio(tab, fw_base: str, nombre_fn: str) -> bool:
    """Verifica que una funcion JS existe en inicio.aspx de Frameworks."""
    tab.goto(f"{fw_base}/inicio.aspx", wait_until="domcontentloaded", timeout=20000)
    time.sleep(0.5)
    return tab.evaluate(f"() => typeof {nombre_fn} === 'function'")


# ─────────────────────────────────────────────────────────────────────────────
# Monitor
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWMonitor:

    def test_FRW_MON001_monitores_globales(self, fw_tab, fw_base):
        """FRW-MON-001: Monitor > Monitores Globales carga sin errores de servidor."""
        _navegar_verificar(fw_tab, fw_base, "/monitoresglobalescustom.aspx", "Monitores Globales")

    def test_FRW_MON002_monitor_chat(self, fw_tab, fw_base):
        """FRW-MON-002: Monitor > Monitor de Chat carga sin errores de servidor."""
        _navegar_verificar(fw_tab, fw_base, "/monitorchat.aspx", "Monitor de Chat")

    def test_FRW_MON003_fn_monitor_online_existe(self, fw_tab, fw_base):
        """FRW-MON-003: Monitor > Monitor On-line — la funcion JS levantaMonitorOnLine existe en el modulo."""
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaMonitorOnLine"), \
            "Funcion levantaMonitorOnLine no encontrada en inicio.aspx"

    def test_FRW_MON004_fn_monitor_lotes_existe(self, fw_tab, fw_base):
        """FRW-MON-004: Monitor > Monitor de Lotes — la funcion JS levantaMonitorDeLotes existe en el modulo."""
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaMonitorDeLotes"), \
            "Funcion levantaMonitorDeLotes no encontrada en inicio.aspx"


# ─────────────────────────────────────────────────────────────────────────────
# Reportes
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWReportes:

    def test_FRW_RPT001_ivr(self, fw_tab, fw_base):
        """FRW-RPT-001: Reportes > IVR — pagina de reporte IVR carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/reporteivr.aspx", "Reportes IVR")

    def test_FRW_RPT002_desbordes(self, fw_tab, fw_base):
        """FRW-RPT-002: Reportes > ACD > Desbordes — pagina de desbordes de cola carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/rptdesbordes.aspx", "Desbordes ACD")

    def test_FRW_RPT003_nivel_servicio(self, fw_tab, fw_base):
        """FRW-RPT-003: Reportes > Campanas > Nivel de Servicio — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/niveldeservicioentranteex.aspx", "Nivel de Servicio")

    def test_FRW_RPT004_productividad_acumulada(self, fw_tab, fw_base):
        """FRW-RPT-004: Reportes > Campanas > Productividad Acumulada — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/productividadacumulada.aspx", "Productividad Acumulada")

    def test_FRW_RPT005_productividad_por_fechas(self, fw_tab, fw_base):
        """FRW-RPT-005: Reportes > Campanas > Productividad Por Fechas — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/ProductividadPorCampania_RFecha.aspx", "Productividad Por Fechas")

    def test_FRW_RPT006_productividad_por_horas(self, fw_tab, fw_base):
        """FRW-RPT-006: Reportes > Campanas > Productividad Por Horas — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/ProductividadPorCampania_RHora.aspx", "Productividad Por Horas")

    def test_FRW_RPT007_ocupacion_telefonica(self, fw_tab, fw_base):
        """FRW-RPT-007: Reportes > Campanas > Ocupacion Telefonica — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/reporteocupacion.aspx", "Ocupacion Telefonica")

    def test_FRW_RPT008_log_actividades(self, fw_tab, fw_base):
        """FRW-RPT-008: Reportes > Agentes > Log de Actividades — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/logactividad.aspx", "Log de Actividades")

    def test_FRW_RPT009_por_agente_un_dia(self, fw_tab, fw_base):
        """FRW-RPT-009: Reportes > Agentes > Por Agente (Un Dia) — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/agenteundia.aspx", "Por Agente Un Dia")

    def test_FRW_RPT010_reporte_mensual_agente(self, fw_tab, fw_base):
        """FRW-RPT-010: Reportes > Agentes > Reporte Mensual por Agente — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/rptMensualXAgente.aspx", "Reporte Mensual Agente")

    def test_FRW_RPT011_reporte_habilidades(self, fw_tab, fw_base):
        """FRW-RPT-011: Reportes > Agentes > Reporte Por Habilidades (Skills) — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/templateRpt.aspx?NomRpt=ReportePorSkill", "Reporte Por Habilidades")

    def test_FRW_RPT012_discador(self, fw_tab, fw_base):
        """FRW-RPT-012: Reportes > Discador > Reporte Discador — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/ReporteDiscador.aspx", "Reporte Discador")

    def test_FRW_RPT013_duracion_efectiva(self, fw_tab, fw_base):
        """FRW-RPT-013: Reportes > Discador > Duracion Efectiva — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/rptduracionEfectiva.aspx", "Duracion Efectiva")

    def test_FRW_RPT014_reportes_personalizados(self, fw_tab, fw_base):
        """FRW-RPT-014: Reportes > Reportes Personalizados (Crystal Reports) — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/customcrystalrpt_reportes.aspx", "Reportes Personalizados")


# ─────────────────────────────────────────────────────────────────────────────
# ACD
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWACD:

    def test_FRW_ACD001_abm_grupos_agentes(self, fw_tab, fw_base):
        """FRW-ACD-001: ACD > Grupos y Agentes > ABM Grupos y Agentes — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/gruposagentes.aspx", "ABM Grupos y Agentes")

    def test_FRW_ACD002_programacion_agentes(self, fw_tab, fw_base):
        """FRW-ACD-002: ACD > Grupos y Agentes > Programacion de Agentes — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/agente_programacion.aspx", "Programacion de Agentes")

    def test_FRW_ACD003_colas_acd(self, fw_tab, fw_base):
        """FRW-ACD-003: ACD > Colas ACD — configuracion de colas carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/confcolasacd.aspx", "Colas ACD")

    def test_FRW_ACD004_perfiles_recepcion(self, fw_tab, fw_base):
        """FRW-ACD-004: ACD > Perfiles de Recepcion — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/perfilesrecepcion.aspx", "Perfiles de Recepcion")

    def test_FRW_ACD005_perfiles_discado(self, fw_tab, fw_base):
        """FRW-ACD-005: ACD > Perfiles de Discado — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/perfilesdiscado.aspx", "Perfiles de Discado")

    def test_FRW_ACD006_asignacion_discado(self, fw_tab, fw_base):
        """FRW-ACD-006: ACD > Asignacion de Perfil de Discado — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/asignacionperfildiscado.aspx", "Asignacion de Discado")

    def test_FRW_ACD007_rutas(self, fw_tab, fw_base):
        """FRW-ACD-007: ACD > Ruteo Inteligente > Rutas Disponibles — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/rutasdisponibles.aspx", "Rutas")

    def test_FRW_ACD008_ruteo_inteligente(self, fw_tab, fw_base):
        """FRW-ACD-008: ACD > Ruteo Inteligente > Configuracion de Ruteo — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/ruteointeligente2.aspx", "Ruteo Inteligente")

    def test_FRW_ACD009_configuracion_pausas(self, fw_tab, fw_base):
        """FRW-ACD-009: ACD > Configuracion de Pausas — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/confpausas.aspx", "Configuracion de Pausas")

    def test_FRW_ACD010_habilidades_configuracion(self, fw_tab, fw_base):
        """FRW-ACD-010: ACD > Habilidades > Configuracion de Skills — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/skillsconfiguracion.aspx", "Habilidades Configuracion")

    def test_FRW_ACD011_habilidades_asignacion(self, fw_tab, fw_base):
        """FRW-ACD-011: ACD > Habilidades > Asignacion de Skills a Agentes — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/skillsagentes.aspx", "Habilidades Asignacion")


# ─────────────────────────────────────────────────────────────────────────────
# Campanas
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWCampanas:

    def test_FRW_CMP001_abm_campanas(self, fw_tab, fw_base):
        """FRW-CMP-001: Campanas > ABM Campanas — alta, baja y modificacion de campanas carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/abmcampanas.aspx", "ABM Campanas")

    def test_FRW_CMP002_status_campanas(self, fw_tab, fw_base):
        """FRW-CMP-002: Campanas > Status Campanas — estado actual de campanas carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/statuscampania.aspx", "Status Campanas")

    def test_FRW_CMP003_abm_subcategorias(self, fw_tab, fw_base):
        """FRW-CMP-003: Campanas > ABM Subcategorias-Categorias — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/ABMSubCategorias.aspx", "ABM Subcategorias")

    def test_FRW_CMP004_sincronizar(self, fw_tab, fw_base):
        """FRW-CMP-004: Campanas > Sincronizar — sincronizacion de datos carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/sincronizar.aspx", "Sincronizar")

    def test_FRW_CMP005_importar_segmentacion(self, fw_tab, fw_base):
        """FRW-CMP-005: Campanas > Segmentacion > Importar Segmentacion — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/importador.aspx", "Importar Segmentacion")

    def test_FRW_CMP006_configurar_segmentacion(self, fw_tab, fw_base):
        """FRW-CMP-006: Campanas > Segmentacion > Configurar Segmentacion — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/configurarsegmentacion.aspx", "Configurar Segmentacion")

    def test_FRW_CMP007_borrar_segmentacion(self, fw_tab, fw_base):
        """FRW-CMP-007: Campanas > Segmentacion > Borrar Segmentacion — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/borrarsegmentacion.aspx", "Borrar Segmentacion")

    def test_FRW_CMP008_crear_lote(self, fw_tab, fw_base):
        """FRW-CMP-008: Campanas > Lotes > Crear Lote — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/crearlote.aspx", "Crear Lote")

    def test_FRW_CMP009_cerrar_lote(self, fw_tab, fw_base):
        """FRW-CMP-009: Campanas > Lotes > Cerrar/Finalizar Lote — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/cerrarlote.aspx", "Cerrar Lote")

    def test_FRW_CMP010_borrar_lote(self, fw_tab, fw_base):
        """FRW-CMP-010: Campanas > Lotes > Borrar Lote — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/borrarlote.aspx", "Borrar Lote")

    def test_FRW_CMP011_reagendar_contactos(self, fw_tab, fw_base):
        """FRW-CMP-011: Campanas > Lotes > Reagendar Contactos — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/reagendarllamados.aspx", "Reagendar Contactos")


# ─────────────────────────────────────────────────────────────────────────────
# Configurar
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWConfigurar:

    def test_FRW_CFG001_clientes(self, fw_tab, fw_base):
        """FRW-CFG-001: Configurar > Parametros CC > Clientes — ABM de clientes carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/abmclientes.aspx", "Clientes")

    def test_FRW_CFG002_prefijos(self, fw_tab, fw_base):
        """FRW-CFG-002: Configurar > Parametros CC > Prefijos — ABM de prefijos carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/prefijosabm.aspx", "Prefijos")

    def test_FRW_CFG003_codigos_finalizacion(self, fw_tab, fw_base):
        """FRW-CFG-003: Configurar > Parametros CC > Codigos de Finalizacion (Etiquetas) — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/abmetiquetas.aspx", "Codigos de Finalizacion")

    def test_FRW_CFG004_gestion_usuarios(self, fw_tab, fw_base):
        """FRW-CFG-004: Configurar > Usuarios > Gestion de Usuarios — carga sin errores como admin."""
        _navegar_verificar(fw_tab, fw_base, "/usuarios.aspx", "Gestion de Usuarios")

    def test_FRW_CFG004b_niveles_usuarios(self, fw_tab, fw_base):
        """FRW-CFG-005: Configurar > Usuarios > Niveles de Usuarios — permisos por pagina cargan sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/niveles_paginas.aspx", "Niveles de Usuarios")

    def test_FRW_CFG005_internos_abm(self, fw_tab, fw_base):
        """FRW-CFG-006: Configurar > Internos > ABM de Internos — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/Internos_ABM.aspx", "Internos ABM")

    def test_FRW_CFG006_internos_alta_masiva(self, fw_tab, fw_base):
        """FRW-CFG-007: Configurar > Internos > Alta Masiva de Internos — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/Internos_altamasiva.aspx", "Internos Alta Masiva")

    def test_FRW_CFG007_internos_baja_masiva(self, fw_tab, fw_base):
        """FRW-CFG-008: Configurar > Internos > Baja Masiva de Internos — carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/Internos_bajamasiva.aspx", "Internos Baja Masiva")

    def test_FRW_CFG008_fn_monitores_globales_abm(self, fw_tab, fw_base):
        """FRW-CFG-009: Configurar > Monitores > Globales > ABM — funcion JS de configuracion existe."""
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigABMMonGlobalesPers"), \
            "Funcion levantaConfigABMMonGlobalesPers no encontrada en inicio.aspx"

    def test_FRW_CFG009_fn_monitores_globales_config(self, fw_tab, fw_base):
        """FRW-CFG-010: Configurar > Monitores > Globales > Configuracion — funcion JS de umbrales existe."""
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigUmbMonGlobalesPers"), \
            "Funcion levantaConfigUmbMonGlobalesPers no encontrada en inicio.aspx"

    def test_FRW_CFG010_fn_monitor_agentes(self, fw_tab, fw_base):
        """FRW-CFG-011: Configurar > Monitores > Online de Agentes — funcion JS de configuracion existe."""
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigMonAgentes"), \
            "Funcion levantaConfigMonAgentes no encontrada en inicio.aspx"

    def test_FRW_CFG011_fn_monitor_efectividad(self, fw_tab, fw_base):
        """FRW-CFG-012: Configurar > Monitores > Monitor Efectividad — funcion JS de configuracion existe."""
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigMonEfectividad"), \
            "Funcion levantaConfigMonEfectividad no encontrada en inicio.aspx"


# ─────────────────────────────────────────────────────────────────────────────
# Grabador y Ayuda
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWGrabadorAyuda:

    def test_FRW_GRB001_grabador(self, fw_tab, fw_base):
        """FRW-GRB-001: Grabador — modulo de grabacion de llamadas carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/grabador.aspx", "Grabador")

    def test_FRW_AYU001_documentacion(self, fw_tab, fw_base):
        """FRW-AYU-001: Ayuda > Documentacion — pagina de ayuda del sistema carga sin errores."""
        _navegar_verificar(fw_tab, fw_base, "/documentacion.aspx", "Ayuda / Documentacion")
