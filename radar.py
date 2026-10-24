from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse, urldefrag
from html.parser import HTMLParser
import json
import unicodedata

ROSARIO = "https://www.rosario.gob.ar/inicio/compras-y-licitaciones"
CLAVES = ("licitacion", "concurso", "contratacion", "compra directa",
          "cotizacion", "pliego", "convocatoria", "compra agil")
EXCLUIR = ("buscar", "inicio", "contacto", "informacion general",
           "compras y licitaciones", "normativa", "tramites")

def normalizar(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def cargar(nombre):
    p = Path(nombre)
    if not p.exists():
        print("FALTA:", nombre, flush=True)
        return []
    return [s.strip() for s in p.read_text(encoding="utf-8").splitlines()
            if s.strip() and not s.lstrip().startswith("#")]

class Enlaces(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.href = None
        self.texto = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.texto = []

    def handle_data(self, data):
        if self.href is not None:
            self.texto.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            if self.href:
                self.items.append((" ".join(" ".join(self.texto).split()), self.href))
            self.href = None
            self.texto = []

def descargar(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as r:
        if "html" not in r.headers.get("Content-Type", "").lower():
            return []
        html = r.read(2000000)
        charset = r.headers.get_content_charset() or "utf-8"
        final = r.geturl()
    parser = Enlaces()
    parser.feed(html.decode(charset, errors="replace"))
    return [(titulo, urldefrag(urljoin(final, href))[0])
            for titulo, href in parser.items]

def ejecutar():
    print("INICIANDO RADAR DE LICITACIONES", flush=True)
    print("Fecha:", datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")))
    fuentes = list(dict.fromkeys(
        [u for u in cargar("fuentes.txt") if u.startswith(("https://", "http://"))]
        + [ROSARIO]))
    patrones = [normalizar(p) for p in cargar("patrones.txt") if len(p) >= 5]
    claves = CLAVES + tuple(patrones)
    visitadas, candidatos = set(), {}
    correctas = fallidas = 0
    for origen in fuentes:
        print("FUENTE:", origen, flush=True)
        dominio = urlparse(origen).netloc.lower()
        pendientes = [(origen, 0)]
        procesadas = 0
        while pendientes and procesadas < 12:
            pagina, nivel = pendientes.pop(0)
            if pagina in visitadas:
                continue
            visitadas.add(pagina)
            procesadas += 1
            try:
                enlaces = descargar(pagina)
                correctas += 1
                print("OK:", pagina, "enlaces:", len(enlaces), flush=True)
            except Exception as e:
                fallidas += 1
                print("ERROR:", pagina, str(e), flush=True)
                continue
            for titulo, destino in enlaces:
                parsed = urlparse(destino)
                if parsed.scheme not in ("http", "https"):
                    continue
                nombre = normalizar(titulo).strip()
                ruta = normalizar(parsed.path)
                if (len(nombre) >= 12 and nombre not in EXCLUIR
                        and any(k in nombre or k in ruta for k in claves)):
                    candidatos.setdefault(destino, {
                        "titulo": titulo, "url": destino, "fuente": origen})
                if (nivel < 2 and parsed.netloc.lower() == dominio
                        and destino not in visitadas
                        and not ruta.endswith((".pdf", ".zip", ".doc", ".docx"))
                        and any(k in nombre or k in ruta for k in CLAVES)):
                    if destino not in [u for u, _ in pendientes]:
                        pendientes.append((destino, nivel + 1))
    archivo = Path("radar_estado.json")
    anteriores = {}
    if archivo.exists():
        anteriores = json.loads(archivo.read_text(encoding="utf-8"))
        if not isinstance(anteriores, dict):
            raise ValueError("Historial invalido")
    nuevas = [v for u, v in candidatos.items() if u not in anteriores]
    anteriores.update(candidatos)
    archivo.write_text(json.dumps(anteriores, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    Path("licitaciones_nuevas.json").write_text(
        json.dumps(nuevas, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CANDIDATOS NUEVOS:", len(nuevas), flush=True)
    for i, item in enumerate(nuevas, 1):
        print(i, item["titulo"], item["url"], flush=True)
    print("RESUMEN: paginas OK:", correctas, "errores:", fallidas,
          "candidatos:", len(candidatos), flush=True)
    print("AVISO: candidatos sin verificar pliegos ni fechas.")
    print("PROCESO FINALIZADO", flush=True)

if __name__ == "__main__":
    ejecutar()
