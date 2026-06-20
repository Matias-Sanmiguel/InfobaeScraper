from modelos.esquema import generar_id, Noticia, Autor, Tema, Verificacion, ResultadoArticulo


def test_generar_id_es_determinista():
    assert generar_id("https://infobae.com/nota") == generar_id("https://infobae.com/nota")


def test_generar_id_longitud_16():
    assert len(generar_id("cualquier texto")) == 16


def test_generar_id_distintos_inputs_distintos_ids():
    assert generar_id("a") != generar_id("b")


def test_noticia_se_crea_con_campos():
    n = Noticia(
        noticia_id="abc123",
        url="https://infobae.com/nota",
        titulo="Título",
        cuerpo="Texto del artículo",
        fecha_publicacion="2026-06-20T10:00:00",
        fecha_modificacion="2026-06-20T11:00:00",
        seccion="america/mundo",
        imagen_portada="https://img.infobae.com/foto.jpg",
    )
    assert n.titulo == "Título"
    assert n.seccion == "america/mundo"


def test_verificacion_verificado_false_por_defecto_no_aplica():
    v = Verificacion(
        verificacion_id="vid",
        texto="El 80% del petróleo pasa por ahí.",
        tipo="estadistica",
        verificado=False,
        fuente_citada="",
    )
    assert v.verificado is False
    assert v.tipo == "estadistica"


def test_resultado_articulo_agrupa_componentes():
    noticia = Noticia("id", "url", "titulo", "cuerpo", "fp", "fm", "sec", "img")
    autor = Autor(autor_id="aid", nombre="Juan Pérez")
    tema = Tema(tema_id="tid", nombre="Irán")
    ver = Verificacion("vid", "texto", "cita", False, "Reuters")
    r = ResultadoArticulo(noticia=noticia, autores=[autor], temas=[tema], verificaciones=[ver])
    assert r.noticia.titulo == "titulo"
    assert len(r.autores) == 1
    assert r.temas[0].nombre == "Irán"
