import csv
from pathlib import Path
from dataclasses import asdict
from contextlib import contextmanager

from modelos.esquema import ResultadoArticulo, Noticia, Autor, Tema, Verificacion

MEDIO_ID = "infobae"
MEDIO_NOMBRE = "Infobae"


class EscritorCSV:
    def __init__(self, directorio_salida: str = "salida") -> None:
        self.directorio = Path(directorio_salida)
        self.directorio.mkdir(parents=True, exist_ok=True)
        self._autores_vistos: set[str] = set()
        self._temas_vistos: set[str] = set()
        self._inicializar_medios()

    def _ruta(self, nombre: str) -> Path:
        return self.directorio / nombre

    def _es_nuevo(self, nombre: str) -> bool:
        return not self._ruta(nombre).exists()

    @contextmanager
    def _csv(self, nombre: str, campos: list[str]):
        nuevo = self._es_nuevo(nombre)
        with open(self._ruta(nombre), "a", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            if nuevo:
                escritor.writeheader()
            yield escritor

    def _inicializar_medios(self) -> None:
        if self._es_nuevo("medios.csv"):
            with self._csv("medios.csv", ["medio_id", "nombre"]) as escritor:
                escritor.writerow({"medio_id": MEDIO_ID, "nombre": MEDIO_NOMBRE})

    def guardar(self, resultado: ResultadoArticulo) -> None:
        self._guardar_noticia(resultado.noticia)
        self._guardar_rel_publica(resultado.noticia.noticia_id)
        for autor in resultado.autores:
            self._guardar_autor(autor, resultado.noticia.noticia_id)
        for tema in resultado.temas:
            self._guardar_tema(tema, resultado.noticia.noticia_id)
        for verificacion in resultado.verificaciones:
            self._guardar_verificacion(verificacion, resultado.noticia.noticia_id)

    def _guardar_noticia(self, noticia: Noticia) -> None:
        campos = ["noticia_id", "url", "titulo", "cuerpo", "fecha_publicacion",
                  "fecha_modificacion", "seccion", "imagen_portada"]
        with self._csv("noticias.csv", campos) as escritor:
            escritor.writerow(asdict(noticia))

    def _guardar_rel_publica(self, noticia_id: str) -> None:
        with self._csv("rel_publica.csv", ["medio_id", "noticia_id"]) as escritor:
            escritor.writerow({"medio_id": MEDIO_ID, "noticia_id": noticia_id})

    def _guardar_autor(self, autor: Autor, noticia_id: str) -> None:
        if autor.autor_id not in self._autores_vistos:
            self._autores_vistos.add(autor.autor_id)
            with self._csv("autores.csv", ["autor_id", "nombre"]) as escritor:
                escritor.writerow(asdict(autor))
        with self._csv("rel_escrito_por.csv", ["noticia_id", "autor_id"]) as escritor:
            escritor.writerow({"noticia_id": noticia_id, "autor_id": autor.autor_id})

    def _guardar_tema(self, tema: Tema, noticia_id: str) -> None:
        if tema.tema_id not in self._temas_vistos:
            self._temas_vistos.add(tema.tema_id)
            with self._csv("temas.csv", ["tema_id", "nombre"]) as escritor:
                escritor.writerow(asdict(tema))
        with self._csv("rel_menciona.csv", ["noticia_id", "tema_id"]) as escritor:
            escritor.writerow({"noticia_id": noticia_id, "tema_id": tema.tema_id})

    def _guardar_verificacion(self, verificacion: Verificacion, noticia_id: str) -> None:
        campos = ["verificacion_id", "texto", "tipo", "verificado", "fuente_citada"]
        with self._csv("verificaciones.csv", campos) as escritor:
            escritor.writerow(asdict(verificacion))
        with self._csv("rel_verifica.csv", ["verificacion_id", "noticia_id"]) as escritor:
            escritor.writerow({"verificacion_id": verificacion.verificacion_id, "noticia_id": noticia_id})
