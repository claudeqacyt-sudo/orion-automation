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
        _navegar_verificar(fw_tab, fw_base, "/monitoresglobalescustom.aspx", "Monitores Globales")

    def test_FRW_MON002_monitor_chat(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/monitorchat.aspx", "Monitor de Chat")

    def test_FRW_MON003_fn_monitor_online_existe(self, fw_tab, fw_base):
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaMonitorOnLine"), \
            "Funcion levantaMonitorOnLine no encontrada en inicio.aspx"

    def test_FRW_MON004_fn_monitor_lotes_existe(self, fw_tab, fw_base):
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaMonitorDeLotes"), \
            "Funcion levantaMonitorDeLotes no encontrada en inicio.aspx"


# ─────────────────────────────────────────────────────────────────────────────
# Reportes
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWReportes:

    def test_FRW_RPT001_ivr(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/reporteivr.aspx", "Reportes IVR")

    def test_FRW_RPT002_desbordes(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/rptdesbordes.aspx", "Desbordes ACD")

    def test_FRW_RPT003_nivel_servicio(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/niveldeservicioentranteex.aspx", "Nivel de Servicio")

    def test_FRW_RPT004_productividad_acumulada(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/productividadacumulada.aspx", "Productividad Acumulada")

    def test_FRW_RPT005_productividad_por_fechas(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/ProductividadPorCampania_RFecha.aspx", "Productividad Por Fechas")

    def test_FRW_RPT006_productividad_por_horas(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/ProductividadPorCampania_RHora.aspx", "Productividad Por Horas")

    def test_FRW_RPT007_ocupacion_telefonica(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/reporteocupacion.aspx", "Ocupacion Telefonica")

    def test_FRW_RPT008_log_actividades(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/logactividad.aspx", "Log de Actividades")

    def test_FRW_RPT009_por_agente_un_dia(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/agenteundia.aspx", "Por Agente Un Dia")

    def test_FRW_RPT010_reporte_mensual_agente(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/rptMensualXAgente.aspx", "Reporte Mensual Agente")

    def test_FRW_RPT011_reporte_habilidades(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/templateRpt.aspx?NomRpt=ReportePorSkill", "Reporte Por Habilidades")

    def test_FRW_RPT012_discador(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/ReporteDiscador.aspx", "Reporte Discador")

    def test_FRW_RPT013_duracion_efectiva(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/rptduracionEfectiva.aspx", "Duracion Efectiva")

    def test_FRW_RPT014_reportes_personalizados(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/customcrystalrpt_reportes.aspx", "Reportes Personalizados")


# ─────────────────────────────────────────────────────────────────────────────
# ACD
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWACD:

    def test_FRW_ACD001_abm_grupos_agentes(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/gruposagentes.aspx", "ABM Grupos y Agentes")

    def test_FRW_ACD002_programacion_agentes(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/agente_programacion.aspx", "Programacion de Agentes")

    def test_FRW_ACD003_colas_acd(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/confcolasacd.aspx", "Colas ACD")

    def test_FRW_ACD004_perfiles_recepcion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/perfilesrecepcion.aspx", "Perfiles de Recepcion")

    def test_FRW_ACD005_perfiles_discado(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/perfilesdiscado.aspx", "Perfiles de Discado")

    def test_FRW_ACD006_asignacion_discado(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/asignacionperfildiscado.aspx", "Asignacion de Discado")

    def test_FRW_ACD007_rutas(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/rutasdisponibles.aspx", "Rutas")

    def test_FRW_ACD008_ruteo_inteligente(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/ruteointeligente2.aspx", "Ruteo Inteligente")

    def test_FRW_ACD009_configuracion_pausas(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/confpausas.aspx", "Configuracion de Pausas")

    def test_FRW_ACD010_habilidades_configuracion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/skillsconfiguracion.aspx", "Habilidades Configuracion")

    def test_FRW_ACD011_habilidades_asignacion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/skillsagentes.aspx", "Habilidades Asignacion")


# ─────────────────────────────────────────────────────────────────────────────
# Campanas
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWCampanas:

    def test_FRW_CMP001_abm_campanas(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/abmcampanas.aspx", "ABM Campanas")

    def test_FRW_CMP002_status_campanas(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/statuscampania.aspx", "Status Campanas")

    def test_FRW_CMP003_abm_subcategorias(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/ABMSubCategorias.aspx", "ABM Subcategorias")

    def test_FRW_CMP004_sincronizar(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/sincronizar.aspx", "Sincronizar")

    def test_FRW_CMP005_importar_segmentacion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/importador.aspx", "Importar Segmentacion")

    def test_FRW_CMP006_configurar_segmentacion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/configurarsegmentacion.aspx", "Configurar Segmentacion")

    def test_FRW_CMP007_borrar_segmentacion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/borrarsegmentacion.aspx", "Borrar Segmentacion")

    def test_FRW_CMP008_crear_lote(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/crearlote.aspx", "Crear Lote")

    def test_FRW_CMP009_cerrar_lote(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/cerrarlote.aspx", "Cerrar Lote")

    def test_FRW_CMP010_borrar_lote(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/borrarlote.aspx", "Borrar Lote")

    def test_FRW_CMP011_reagendar_contactos(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/reagendarllamados.aspx", "Reagendar Contactos")


# ─────────────────────────────────────────────────────────────────────────────
# Configurar
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWConfigurar:

    def test_FRW_CFG001_clientes(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/abmclientes.aspx", "Clientes")

    def test_FRW_CFG002_prefijos(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/prefijosabm.aspx", "Prefijos")

    def test_FRW_CFG003_codigos_finalizacion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/abmetiquetas.aspx", "Codigos de Finalizacion")

    def test_FRW_CFG004_gestion_usuarios(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/usuarios.aspx", "Gestion de Usuarios")

    def test_FRW_CFG004b_niveles_usuarios(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/niveles_paginas.aspx", "Niveles de Usuarios")

    def test_FRW_CFG005_internos_abm(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/Internos_ABM.aspx", "Internos ABM")

    def test_FRW_CFG006_internos_alta_masiva(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/Internos_altamasiva.aspx", "Internos Alta Masiva")

    def test_FRW_CFG007_internos_baja_masiva(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/Internos_bajamasiva.aspx", "Internos Baja Masiva")

    def test_FRW_CFG008_fn_monitores_globales_abm(self, fw_tab, fw_base):
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigABMMonGlobalesPers"), \
            "Funcion levantaConfigABMMonGlobalesPers no encontrada en inicio.aspx"

    def test_FRW_CFG009_fn_monitores_globales_config(self, fw_tab, fw_base):
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigUmbMonGlobalesPers"), \
            "Funcion levantaConfigUmbMonGlobalesPers no encontrada en inicio.aspx"

    def test_FRW_CFG010_fn_monitor_agentes(self, fw_tab, fw_base):
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigMonAgentes"), \
            "Funcion levantaConfigMonAgentes no encontrada en inicio.aspx"

    def test_FRW_CFG011_fn_monitor_efectividad(self, fw_tab, fw_base):
        assert _fn_existe_en_inicio(fw_tab, fw_base, "levantaConfigMonEfectividad"), \
            "Funcion levantaConfigMonEfectividad no encontrada en inicio.aspx"


# ─────────────────────────────────────────────────────────────────────────────
# Grabador y Ayuda
# ─────────────────────────────────────────────────────────────────────────────

class TestFRWGrabadorAyuda:

    def test_FRW_GRB001_grabador(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/grabador.aspx", "Grabador")

    def test_FRW_AYU001_documentacion(self, fw_tab, fw_base):
        _navegar_verificar(fw_tab, fw_base, "/documentacion.aspx", "Ayuda / Documentacion")
