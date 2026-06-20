import csv
from pathlib import Path
from dataclasses import asdict

from modelos.esquema import ResultadoArticulo, Noticia, Autor, Tema, Verificacion

MEDIO_ID = "infobae"
MEDIO_NOMBRE = "Infobae"


class EscritorCSV:
    def __init__(self, directorio_salida: str = "salida"):
        self.directorio = Path(directorio_salida)
        self.directorio.mkdir(parents=True, exist_ok=True)
        self._inicializar_medios()

    def _ruta(self, nombre: str) -> Path:
        return self.directorio / nombre

    def _es_nuevo(self, nombre: str) -> bool:
        return not self._ruta(nombre).exists()

    def _abrir_csv(self, nombre: str, campos: list[str]):
        nuevo = self._es_nuevo(nombre)
        archivo = open(self._ruta(nombre), "a", newline="", encoding="utf-8")
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        if nuevo:
            escritor.writeheader()
        return archivo, escritor

    def _inicializar_medios(self):
        if self._es_nuevo("medios.csv"):
            archivo, escritor = self._abrir_csv("medios.csv", ["medio_id", "nombre"])
            escritor.writerow({"medio_id": MEDIO_ID, "nombre": MEDIO_NOMBRE})
            archivo.close()

    def guardar(self, resultado: ResultadoArticulo):
        self._guardar_noticia(resultado.noticia)
        self._guardar_rel_publica(resultado.noticia.noticia_id)
        for autor in resultado.autores:
            self._guardar_autor(autor, resultado.noticia.noticia_id)
        for tema in resultado.temas:
            self._guardar_tema(tema, resultado.noticia.noticia_id)
        for verificacion in resultado.verificaciones:
            self._guardar_verificacion(verificacion, resultado.noticia.noticia_id)

    def _guardar_noticia(self, noticia: Noticia):
        campos = ["noticia_id", "url", "titulo", "cuerpo", "fecha_publicacion",
                  "fecha_modificacion", "seccion", "imagen_portada"]
        archivo, escritor = self._abrir_csv("noticias.csv", campos)
        escritor.writerow(asdict(noticia))
        archivo.close()

    def _guardar_rel_publica(self, noticia_id: str):
        archivo, escritor = self._abrir_csv("rel_publica.csv", ["medio_id", "noticia_id"])
        escritor.writerow({"medio_id": MEDIO_ID, "noticia_id": noticia_id})
        archivo.close()

    def _guardar_autor(self, autor: Autor, noticia_id: str):
        archivo, escritor = self._abrir_csv("autores.csv", ["autor_id", "nombre"])
        escritor.writerow(asdict(autor))
        archivo.close()
        archivo, escritor = self._abrir_csv("rel_escrito_por.csv", ["noticia_id", "autor_id"])
        escritor.writerow({"noticia_id": noticia_id, "autor_id": autor.autor_id})
        archivo.close()

    def _guardar_tema(self, tema: Tema, noticia_id: str):
        archivo, escritor = self._abrir_csv("temas.csv", ["tema_id", "nombre"])
        escritor.writerow(asdict(tema))
        archivo.close()
        archivo, escritor = self._abrir_csv("rel_menciona.csv", ["noticia_id", "tema_id"])
        escritor.writerow({"noticia_id": noticia_id, "tema_id": tema.tema_id})
        archivo.close()

    def _guardar_verificacion(self, verificacion: Verificacion, noticia_id: str):
        campos = ["verificacion_id", "texto", "tipo", "verificado", "fuente_citada"]
        archivo, escritor = self._abrir_csv("verificaciones.csv", campos)
        escritor.writerow(asdict(verificacion))
        archivo.close()
        archivo, escritor = self._abrir_csv("rel_verifica.csv", ["verificacion_id", "noticia_id"])
        escritor.writerow({"verificacion_id": verificacion.verificacion_id, "noticia_id": noticia_id})
        archivo.close()
