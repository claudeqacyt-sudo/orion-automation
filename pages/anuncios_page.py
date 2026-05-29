"""
anuncios_page.py - Page Object para el modulo Anuncios de Orion Contact Center
Selectores verificados contra HTML real de Orion v7.0 (10.1.10.150:8080)

Ruta de navegacion: menu top-level -> Anuncios (accionEjecutar_1)

DOM verificado:
  /inicio
  #carruselGestor          -> carousel Bootstrap (.carousel.slide)
    ol.carousel-indicators -> 3 indicadores (li)
    .carousel-inner        -> contenedor de slides
      .item                -> cada slide (3 en total)
        img                -> imagen de fondo
        .carousel-caption  -> h1 + p con el texto
    .left.carousel-control -> flecha anterior
    .right.carousel-control -> flecha siguiente

Estado base del sistema (verificado):
  Slides: 3
  Slide activo al cargar: indice 0 ("Bienvenido a ORION!")
"""
import time
from pages.base_page import BasePage


class AnunciosNav:
    """Navegacion al modulo Anuncios desde la pagina principal."""

    MENU_ANUNCIOS = "#accionEjecutar_1"

    def __init__(self, page):
        self.page = page

    def open_anuncios(self):
        """Abre Anuncios en nueva pestana. Retorna el Page de la nueva pestana."""
        self.page.locator(self.MENU_ANUNCIOS).wait_for(state='visible', timeout=10000)
        with self.page.context.expect_page(timeout=15000) as new_page_info:
            self.page.evaluate(f"document.querySelector('{self.MENU_ANUNCIOS}').click()")
        tab = new_page_info.value
        try:
            tab.wait_for_load_state('domcontentloaded', timeout=15000)
        except Exception:
            time.sleep(3)
        time.sleep(2)
        return tab


class AnunciosPage(BasePage):
    """
    Page Object para la seccion Anuncios (/inicio).

    Selectores verificados:
      #carruselGestor          -> carrusel principal
      ol.carousel-indicators   -> indicadores de posicion (3 li)
      .carousel-inner .item    -> slides individuales
      .left.carousel-control   -> boton anterior
      .right.carousel-control  -> boton siguiente
    """

    URL_PATH = "/inicio"

    CARRUSEL           = "#carruselGestor"
    CAROUSEL_INNER     = "#carruselGestor .carousel-inner"
    SLIDES             = "#carruselGestor .item"
    SLIDE_ACTIVO       = "#carruselGestor .item.active"
    INDICADORES        = "#carruselGestor ol.carousel-indicators li"
    BTN_PREV           = "#carruselGestor .left.carousel-control"
    BTN_NEXT           = "#carruselGestor .right.carousel-control"

    TOTAL_SLIDES = 3

    # Textos esperados de los slides (h1)
    TITULOS_SLIDES = [
        "Bienvenido a ORION!",
        "ORION",
        "desde tu PC o tablet",
    ]

    def __init__(self, page):
        super().__init__(page)

    def wait_for_load(self):
        self.page.locator(self.CARRUSEL).wait_for(state='visible', timeout=self.timeout)

    def verify_page_loaded(self):
        self.wait_for_load()

    def get_total_slides(self) -> int:
        return self.page.locator(self.SLIDES).count()

    def get_total_indicadores(self) -> int:
        return self.page.locator(self.INDICADORES).count()

    def get_indice_slide_activo(self) -> int:
        return self.page.evaluate("""
            () => {
                const slides = document.querySelectorAll('#carruselGestor .item');
                for (let i = 0; i < slides.length; i++) {
                    if (slides[i].classList.contains('active')) return i;
                }
                return -1;
            }
        """)

    def get_titulos_slides(self) -> list:
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('#carruselGestor .carousel-caption h1'))
                .map(h => h.innerText.trim())
        """)

    def slide_activo_tiene_imagen(self) -> bool:
        return self.page.evaluate("""
            () => {
                const activo = document.querySelector('#carruselGestor .item.active');
                return activo ? activo.querySelectorAll('img').length > 0 : false;
            }
        """)
