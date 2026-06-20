from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from scraper.parseador_articulo import (
    extraer_seccion,
    extraer_meta,
    extraer_cuerpo,
    extraer_autores,
    extraer_temas,
    clasificar_oracion,
    extraer_verificaciones,
    parsear_articulo,
)

HTML_MUESTRA = """
<html>
<head>
  <meta property="og:title" content="Título de prueba" />
  <meta property="og:image" content="https://img.infobae.com/foto.jpg" />
  <meta property="article:published_time" content="2026-06-20T10:00:00-03:00" />
  <meta property="article:modified_time" content="2026-06-20T11:00:00-03:00" />
  <meta property="article:author" content="Juan Pérez" />
</head>
<body>
  <div class="article-body">
    El régimen de Irán anunció el cierre del estrecho de Ormuz.
    "Cerraremos el estrecho", dijo el portavoz según Reuters.
    El 80% del petróleo del Golfo pasa por ese punto.
  </div>
  <a class="tag">Irán</a>
  <a class="tag">Estrecho de Ormuz</a>
  <a class="author-name">Juan Pérez</a>
</body>
</html>
"""


def _soup() -> BeautifulSoup:
    return BeautifulSoup(HTML_MUESTRA, "lxml")


def test_extraer_seccion_dos_segmentos():
    url = "https://www.infobae.com/america/mundo/2026/06/20/nota/"
    assert extraer_seccion(url) == "america/mundo"


def test_extraer_seccion_un_segmento():
    url = "https://www.infobae.com/economia/2026/06/20/nota/"
    assert extraer_seccion(url) == "economia"


def test_extraer_meta_og_title():
    soup = _soup()
    assert extraer_meta(soup, "og:title") == "Título de prueba"


def test_extraer_meta_faltante_retorna_string_vacio():
    soup = _soup()
    assert extraer_meta(soup, "og:nonexistent") == ""


def test_extraer_cuerpo_devuelve_texto():
    soup = _soup()
    cuerpo = extraer_cuerpo(soup)
    assert "Irán" in cuerpo
    assert len(cuerpo) > 10


def test_extraer_autores_desde_clase():
    soup = _soup()
    autores = extraer_autores(soup)
    assert "Juan Pérez" in autores


def test_extraer_temas_desde_clase_tag():
    soup = _soup()
    temas = extraer_temas(soup)
    assert "Irán" in temas
    assert "Estrecho de Ormuz" in temas


def test_clasificar_oracion_cita_con_dijo():
    tipo, fuente = clasificar_oracion('"Cerraremos el estrecho", dijo el portavoz.')
    assert tipo == "cita"


def test_clasificar_oracion_estadistica():
    tipo, fuente = clasificar_oracion("El 80% del petróleo del Golfo pasa por ese punto.")
    assert tipo == "estadistica"


def test_clasificar_oracion_segun_extrae_fuente():
    tipo, fuente = clasificar_oracion("El cierre fue confirmado según Reuters.")
    assert tipo == "cita"
    assert "Reuters" in fuente


def test_clasificar_oracion_sin_clasificar():
    tipo, fuente = clasificar_oracion("El estrecho tiene una longitud de doscientos kilómetros.")
    assert tipo == "sin_clasificar"


def test_extraer_verificaciones_genera_lista():
    cuerpo = (
        "El régimen de Irán anunció el cierre del estrecho de Ormuz. "
        '"Cerraremos el estrecho", dijo el portavoz según Reuters. '
        "El 80% del petróleo del Golfo pasa por ese punto."
    )
    verificaciones = extraer_verificaciones(cuerpo)
    assert len(verificaciones) >= 2
    tipos = {v.tipo for v in verificaciones}
    assert "cita" in tipos or "estadistica" in tipos


def test_parsear_articulo_llama_requests(mocker):
    respuesta_mock = MagicMock()
    respuesta_mock.text = HTML_MUESTRA
    respuesta_mock.raise_for_status = MagicMock()
    mocker.patch("scraper.parseador_articulo.requests.get", return_value=respuesta_mock)
    mocker.patch("scraper.parseador_articulo.time.sleep")

    url = "https://www.infobae.com/america/mundo/2026/06/20/nota-ejemplo/"
    resultado = parsear_articulo(url, delay=0)

    assert resultado.noticia.titulo == "Título de prueba"
    assert resultado.noticia.seccion == "america/mundo"
    assert resultado.noticia.imagen_portada == "https://img.infobae.com/foto.jpg"
    assert len(resultado.temas) == 2
