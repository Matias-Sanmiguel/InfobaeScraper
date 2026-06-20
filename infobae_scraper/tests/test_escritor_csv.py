import csv
from pathlib import Path
from modelos.esquema import Noticia, Autor, Tema, Verificacion, ResultadoArticulo
from salida.escritor_csv import EscritorCSV


def _resultado_muestra() -> ResultadoArticulo:
    noticia = Noticia(
        noticia_id="abc123",
        url="https://www.infobae.com/america/mundo/2026/06/20/nota/",
        titulo="Título de prueba",
        cuerpo="El texto del cuerpo.",
        fecha_publicacion="2026-06-20T10:00:00",
        fecha_modificacion="2026-06-20T11:00:00",
        seccion="america/mundo",
        imagen_portada="https://img.infobae.com/foto.jpg",
    )
    return ResultadoArticulo(
        noticia=noticia,
        autores=[Autor(autor_id="au1", nombre="Juan Pérez")],
        temas=[Tema(tema_id="te1", nombre="Irán")],
        verificaciones=[
            Verificacion(verificacion_id="ve1", texto="El 80% pasa por ahí.", tipo="estadistica", verificado=False, fuente_citada="")
        ],
    )


def test_crea_archivos_csv(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    archivos = [f.name for f in tmp_path.iterdir()]
    assert "noticias.csv" in archivos
    assert "medios.csv" in archivos
    assert "temas.csv" in archivos
    assert "autores.csv" in archivos
    assert "verificaciones.csv" in archivos
    assert "rel_publica.csv" in archivos
    assert "rel_menciona.csv" in archivos
    assert "rel_escrito_por.csv" in archivos
    assert "rel_verifica.csv" in archivos


def test_noticias_csv_contiene_datos(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    filas = list(csv.DictReader(open(tmp_path / "noticias.csv", encoding="utf-8")))
    assert len(filas) == 1
    assert filas[0]["noticia_id"] == "abc123"
    assert filas[0]["titulo"] == "Título de prueba"


def test_medios_csv_contiene_infobae(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    escritor.guardar(_resultado_muestra())
    filas = list(csv.DictReader(open(tmp_path / "medios.csv", encoding="utf-8")))
    assert any(f["nombre"] == "Infobae" for f in filas)
    assert len(filas) == 1


def test_rel_publica_vincula_medio_a_noticia(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    filas = list(csv.DictReader(open(tmp_path / "rel_publica.csv", encoding="utf-8")))
    assert filas[0]["medio_id"] == "infobae"
    assert filas[0]["noticia_id"] == "abc123"


def test_temas_y_relacion_menciona(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    temas = list(csv.DictReader(open(tmp_path / "temas.csv", encoding="utf-8")))
    menciona = list(csv.DictReader(open(tmp_path / "rel_menciona.csv", encoding="utf-8")))
    assert temas[0]["nombre"] == "Irán"
    assert menciona[0]["noticia_id"] == "abc123"
    assert menciona[0]["tema_id"] == "te1"


def test_verificaciones_y_relacion_verifica(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    vers = list(csv.DictReader(open(tmp_path / "verificaciones.csv", encoding="utf-8")))
    verifica = list(csv.DictReader(open(tmp_path / "rel_verifica.csv", encoding="utf-8")))
    assert vers[0]["tipo"] == "estadistica"
    assert verifica[0]["verificacion_id"] == "ve1"
    assert verifica[0]["noticia_id"] == "abc123"


def test_guardar_dos_veces_appenda_filas(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    resultado2 = _resultado_muestra()
    resultado2.noticia.noticia_id = "def456"
    escritor.guardar(resultado2)
    filas = list(csv.DictReader(open(tmp_path / "noticias.csv", encoding="utf-8")))
    assert len(filas) == 2


def test_autores_y_temas_sin_duplicados(tmp_path):
    escritor = EscritorCSV(str(tmp_path))
    escritor.guardar(_resultado_muestra())
    resultado2 = _resultado_muestra()
    resultado2.noticia.noticia_id = "def456"
    escritor.guardar(resultado2)
    autores = list(csv.DictReader(open(tmp_path / "autores.csv", encoding="utf-8")))
    temas = list(csv.DictReader(open(tmp_path / "temas.csv", encoding="utf-8")))
    rel_escrito = list(csv.DictReader(open(tmp_path / "rel_escrito_por.csv", encoding="utf-8")))
    rel_menciona = list(csv.DictReader(open(tmp_path / "rel_menciona.csv", encoding="utf-8")))
    assert len(autores) == 1
    assert len(temas) == 1
    assert len(rel_escrito) == 2
    assert len(rel_menciona) == 2
