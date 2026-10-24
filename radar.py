from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urldefrag, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import json
import re
import unicodedata

ZONA = ZoneInfo('America/Argentina/Buenos_Aires')
ARCHIVO_ESTADO = Path('radar_estado.json')
FUENTE_ROSARIO = 'https://www.rosario.gob.ar/inicio/compras-y-licitaciones'

MAX_PAGINAS_POR_FUENTE = 15
MAX_NIVEL = 2

EXTENSIONES = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip')

PALABRAS = (
    'licitacion', 'concurso', 'compra agil',
    'compra directa', 'contratacion', 'cotizacion',
    'segundo llamado', 'pliego', 'convocatoria'
)

EXCLUSIONES = (
    'normativa', 'informacion general', 'ir al contenido',
    'oferentes y/o adjudicatarios', 'terminos y condiciones',
    'pliego unico', 'pliego de condiciones generales',
    'buscar', 'contacto', 'inicio', 'licitaciones publicadas',
    'compras y licitaciones', 'contrataciones en evaluacion',
    'contrataciones para apertura'
)

PATRON_NUMERO = re.compile(
    r'(?<!\d)(?:\d{1,4}\s*[/\-]\s*20\d{2}|'
    r'(?:LP|CP|CA|CD|CM|LPU|LPR|EXP|EXPTE)'
    r'\s*[#º°.: -]*\d{1,9}'
    r'(?:\s*[/\-]\s*\d{2,4})?)(?!\d)',
    re.I
)


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto).lower())
    return ''.join(
        c for c in texto
        if not unicodedata.combining(c)
    )


def url_limpia(url):
    u = urlparse(urldefrag(url)[0])

    q = urlencode(sorted(
        (k, v)
        for k, v in parse_qsl(
            u.query, keep_blank_values=True
        )
        if not k.lower().startswith(
            ('utm_', 'fbclid', 'gclid')
        )
    ))

    return urlunparse((
        u.scheme.lower(),
        u.netloc.lower(),
        u.path.rstrip('/') or '/',
        '',
        q,
        ''
    ))


def leer_lineas(nombre):
    ruta = Path(nombre)

    if not ruta.exists():
        print('AVISO: no existe', nombre, flush=True)
        return []

    return [
        s.strip()
        for s in ruta.read_text(
            encoding='utf-8'
        ).splitlines()
        if s.strip()
        and not s.lstrip().startswith('#')
    ]


class Enlaces(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.activos = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.activos.append({
                'href': dict(attrs).get('href'),
                'texto': []
            })

    def handle_data(self, data):
        for a in self.activos:
            a['texto'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.activos:
            a = self.activos.pop()

            if a['href']:
                self.items.append((
                    ' '.join(
                        ' '.join(a['texto']).split()
                    ),
                    a['href']
                ))


def descargar(url):
    peticion = Request(
        url,
        headers={
            'User-Agent':
            'Mozilla/5.0 (compatible; RadarLicitaciones/2.0)'
        }
    )

    with urlopen(peticion, timeout=20) as respuesta:
        tipo = respuesta.headers.get(
            'Content-Type', ''
        ).lower()

        if 'html' not in tipo:
            return None, respuesta.geturl(), tipo

        contenido = respuesta.read(2_000_000)
        codificacion = (
            respuesta.headers.get_content_charset()
            or 'utf-8'
        )
        final = respuesta.geturl()

    parser = Enlaces()
    parser.feed(
        contenido.decode(
            codificacion, errors='replace'
        )
    )

    return parser.items, final, tipo


def candidato(titulo, destino):
    texto = normalizar(titulo).strip()

    ruta = normalizar(
        urlparse(destino).path
        + ' '
        + urlparse(destino).query
    )

    if len(texto) < 8:
        return False

    if any(
        texto == x or texto.startswith(x + ' ')
        for x in EXCLUSIONES
    ):
        return False

    if not any(
        p in texto or p in ruta
        for p in PALABRAS
    ):
        return False

    return bool(
        PATRON_NUMERO.search(texto)
        or PATRON_NUMERO.search(ruta)
    )


def cargar_estado():
    if not ARCHIVO_ESTADO.exists():
        return {
            'version': 2,
            'candidatos': {}
        }

    datos = json.loads(
        ARCHIVO_ESTADO.read_text(
            encoding='utf-8'
        )
    )

    if not isinstance(datos, dict):
        raise ValueError(
            'El historial no es un objeto JSON'
        )

    if 'candidatos' in datos:
        if not isinstance(
            datos['candidatos'], dict
        ):
            raise ValueError(
                'Historial de candidatos invalido'
            )
        return datos

    return {
        'version': 2,
        'candidatos': datos
    }


def guardar_json(nombre, datos):
    temporal = Path(nombre + '.tmp')

    temporal.write_text(
        json.dumps(
            datos,
            ensure_ascii=False,
            indent=2
        ),
        encoding='utf-8'
    )

    temporal.replace(nombre)


def ejecutar():
    ahora = datetime.now(ZONA).isoformat()

    print('INICIO RADAR', ahora, flush=True)

    fuentes = list(dict.fromkeys(
        url_limpia(u)
        for u in (
            leer_lineas('fuentes.txt')
            + [FUENTE_ROSARIO]
        )
        if u.startswith(
            ('https://', 'http://')
        )
    ))

    estado = cargar_estado()
    conocidos = estado['candidatos']

    encontrados = {}
    auditoria = []
    visitadas = set()

    for origen in fuentes:
        dominio = urlparse(origen).netloc
        pendientes = [(origen, 0)]

        procesadas = 0
        paginas_ok = 0
        errores = []
        no_html = 0

        while (
            pendientes
            and procesadas < MAX_PAGINAS_POR_FUENTE
        ):
            pagina, nivel = pendientes.pop(0)

            if pagina in visitadas:
                continue

            visitadas.add(pagina)
            procesadas += 1

            try:
                enlaces, final, tipo = descargar(
                    pagina
                )

                if enlaces is None:
                    no_html += 1
                    continue

                paginas_ok += 1

                print(
                    'OK',
                    pagina,
                    'enlaces',
                    len(enlaces),
                    flush=True
                )

            except (
                HTTPError,
                URLError,
                TimeoutError,
                OSError,
                ValueError
            ) as exc:

                errores.append({
                    'url': pagina,
                    'error': str(exc)
                })

                print(
                    'ERROR',
                    pagina,
                    str(exc),
                    flush=True
                )
                continue

            for titulo, href in enlaces:
                destino = url_limpia(
                    urljoin(final, href)
                )

                parsed = urlparse(destino)

                if parsed.scheme not in (
                    'http', 'https'
                ):
                    continue

                if candidato(titulo, destino):
                    encontrados.setdefault(
                        destino,
                        {
                            'titulo': titulo,
                            'url': destino,
                            'fuente': origen,
                            'primera_deteccion': ahora,
                            'estado':
                            'CANDIDATO_NO_VERIFICADO'
                        }
                    )

                ruta = normalizar(
                    parsed.path
                    + ' '
                    + parsed.query
                )

                if (
                    nivel < MAX_NIVEL
                    and parsed.netloc == dominio
                    and destino not in visitadas
                    and not parsed.path.lower().endswith(
                        EXTENSIONES
                    )
                    and any(
                        p in normalizar(titulo)
                        or p in ruta
                        for p in PALABRAS
                    )
                    and destino not in [
                        x for x, _ in pendientes
                    ]
                ):
                    pendientes.append(
                        (destino, nivel + 1)
                    )

        auditoria.append({
            'fuente': origen,
            'paginas_html_revisadas': paginas_ok,
            'paginas_no_html': no_html,
            'errores': errores,
            'paginas_pendientes_por_limite':
                len(pendientes),
            'estado': (
                'ERROR'
                if errores and not paginas_ok
                else (
                    'PARCIAL'
                    if errores or pendientes
                    else 'REVISADA'
                )
            )
        })

    nuevos = []

    for url, ficha in encontrados.items():
        if url not in conocidos:
            nuevos.append(ficha)
            conocidos[url] = ficha
        else:
            conocidos[url][
                'ultima_deteccion'
            ] = ahora

    estado['version'] = 2
    estado['ultima_ejecucion'] = ahora

    guardar_json(
        'radar_estado.json',
        estado
    )

    guardar_json(
        'licitaciones_nuevas.json',
        nuevos
    )

    guardar_json(
        'auditoria_fuentes.json',
        auditoria
    )

    print(
        'CANDIDATOS NO VISTOS (NO VERIFICADOS):',
        len(nuevos),
        flush=True
    )

    for ficha in nuevos:
        print(
            'PENDIENTE:',
            ficha['titulo'],
            ficha['url'],
            flush=True
        )

    print(
        'FUENTES:',
        len(fuentes),
        'PAGINAS HTML OK:',
        sum(
            x['paginas_html_revisadas']
            for x in auditoria
        ),
        flush=True
    )

    print(
        'ADVERTENCIA: no verifica pliegos, fechas '
        'ni novedad por expediente.',
        flush=True
    )


if __name__ == '__main__':
    ejecutar()
