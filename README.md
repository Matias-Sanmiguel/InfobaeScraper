# Infobae Scraper

Herramienta para recolectar artículos de Infobae y exportarlos en un formato compatible con Neo4j. Desarrollada para el proyecto de investigación sobre detección de desinformación digital.

---

## ¿Qué hace?

Dado un artículo o una sección de Infobae, el scraper extrae:

- Título, cuerpo, fecha de publicación y modificación
- Sección, autor (cuando está disponible) y temas etiquetados
- Oraciones del cuerpo clasificadas automáticamente como *cita*, *estadística* o *sin clasificar* — base para el análisis de verificabilidad

Todo queda guardado en CSVs listos para importar a Neo4j, y hay un script para cargar esos datos directamente en el Excel de la plantilla.

---

## Instalación

Requiere Python 3.11+ y Google Chrome instalado.

```bash
cd infobae_scraper
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Uso

### Scrapear un artículo individual

```bash
python main.py --url "https://www.infobae.com/america/mundo/2026/06/20/titulo-del-articulo/"
```

### Scrapear una sección completa

```bash
python main.py --seccion "/america/mundo/" --max 50
```

El scraper hace scroll automático en la página de la sección hasta recolectar la cantidad pedida de artículos.

### Opciones disponibles

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--url` | — | URL de un artículo individual |
| `--seccion` | — | Sección a crawlear (ej: `/economia/`) |
| `--max` | 50 | Máximo de artículos en modo sección |
| `--salida` | `datos/` | Directorio donde se guardan los CSVs |
| `--delay` | 2.0 | Segundos entre requests (no bajar de 2) |

Los CSVs quedan en la carpeta `datos/` (o la que indiques con `--salida`).

---

## Cargar los datos al Excel

Una vez que tenés los CSVs generados, podés volcarlos a la plantilla Excel:

```bash
python cargar_excel.py
```

Esto lee los archivos de `datos/`, cruza la información y genera `datos_infobae.xlsx` en la carpeta raíz del proyecto. La plantilla vacía está en `plantilla_datos_infobae.xlsx`.

Si los CSVs están en otra carpeta:

```bash
python cargar_excel.py --csvs mi_carpeta/ --salida mi_archivo.xlsx
```

---

## Archivos generados

El scraper produce estos CSVs, pensados para importarse directamente a Neo4j:

**Nodos**
- `noticias.csv` — artículos
- `medios.csv` — fuente (siempre Infobae)
- `autores.csv` — autores encontrados
- `temas.csv` — etiquetas/tags del artículo
- `verificaciones.csv` — oraciones extraídas del cuerpo

**Relaciones**
- `rel_publica.csv` — Medio → publica → Noticia
- `rel_escrito_por.csv` — Noticia → escrita por → Autor
- `rel_menciona.csv` — Noticia → menciona → Tema
- `rel_verifica.csv` — Verificacion → verifica → Noticia

---

## Importar a Neo4j

```cypher
LOAD CSV WITH HEADERS FROM 'file:///noticias.csv' AS row
CREATE (:Noticia {id: row.noticia_id, url: row.url, titulo: row.titulo, seccion: row.seccion});

LOAD CSV WITH HEADERS FROM 'file:///medios.csv' AS row
MERGE (:Medio {id: row.medio_id, nombre: row.nombre});

LOAD CSV WITH HEADERS FROM 'file:///autores.csv' AS row
MERGE (:Autor {id: row.autor_id, nombre: row.nombre});

LOAD CSV WITH HEADERS FROM 'file:///temas.csv' AS row
MERGE (:Tema {id: row.tema_id, nombre: row.nombre});

LOAD CSV WITH HEADERS FROM 'file:///verificaciones.csv' AS row
CREATE (:Verificacion {id: row.verificacion_id, texto: row.texto, tipo: row.tipo, verificado: toBoolean(row.verificado)});

LOAD CSV WITH HEADERS FROM 'file:///rel_publica.csv' AS row
MATCH (m:Medio {id: row.medio_id}), (n:Noticia {id: row.noticia_id})
CREATE (m)-[:PUBLICA]->(n);

LOAD CSV WITH HEADERS FROM 'file:///rel_escrito_por.csv' AS row
MATCH (n:Noticia {id: row.noticia_id}), (a:Autor {id: row.autor_id})
CREATE (n)-[:ESCRITO_POR]->(a);

LOAD CSV WITH HEADERS FROM 'file:///rel_menciona.csv' AS row
MATCH (n:Noticia {id: row.noticia_id}), (t:Tema {id: row.tema_id})
CREATE (n)-[:MENCIONA]->(t);

LOAD CSV WITH HEADERS FROM 'file:///rel_verifica.csv' AS row
MATCH (v:Verificacion {id: row.verificacion_id}), (n:Noticia {id: row.noticia_id})
CREATE (v)-[:VERIFICA]->(n);
```

Copiá los CSVs a la carpeta `import/` de tu instalación de Neo4j antes de correr estas queries.

---

## Tests

```bash
cd infobae_scraper
source venv/bin/activate
pytest tests/ -v
```

31 tests cubriendo los módulos principales.
