"""Lectura de documentos públicos sin ejecutar adjuntos ni extraer rutas de ZIP."""
from io import BytesIO
from pathlib import Path
import os
import re
import subprocess
import tempfile
import zipfile
from xml.etree import ElementTree


def docx(datos):
    with zipfile.ZipFile(BytesIO(datos)) as z:
        i=z.getinfo('word/document.xml')
        if i.file_size>32_000_000:raise ValueError('DOCX excede tamaño seguro')
        root=ElementTree.fromstring(z.read(i))
        return '\n'.join(' '.join(t.text or '' for t in p.iter() if t.tag.endswith('}t'))
                         for p in root.iter() if p.tag.endswith('}p'))


def pdf(datos,ocr=False,progreso=None):
    if not datos.startswith(b'%PDF-'):raise ValueError('Respuesta no es PDF')
    r=subprocess.run(['pdftotext','-layout','-','-'],input=datos,capture_output=True,check=True,timeout=35)
    texto=r.stdout.decode('utf-8')
    if texto.strip():return texto
    if not ocr:raise ValueError('PDF sin texto: requiere OCR; no se declara vacío')
    with tempfile.TemporaryDirectory() as d:
        source=Path(d)/'documento.pdf';source.write_bytes(datos)
        info=subprocess.run(['pdfinfo',str(source)],capture_output=True,text=True,check=True,timeout=5)
        m=re.search(r'^Pages:\s*(\d+)',info.stdout,re.M)
        if not m:raise ValueError('No se pudo obtener cantidad de páginas para OCR')
        paginas=[]
        for pagina in range(1,int(m[1])+1):
            prefix=Path(d)/'pagina'
            subprocess.run(['pdftoppm','-f',str(pagina),'-l',str(pagina),'-scale-to','1600','-singlefile','-png',str(source),str(prefix)],capture_output=True,check=True,timeout=15)
            result=subprocess.run(['tesseract',str(prefix)+'.png','stdout','-l','spa+eng'],capture_output=True,text=True,check=True,timeout=20,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
            paginas.append(result.stdout)
            if progreso:progreso('\n'.join(paginas))
        texto='\n'.join(paginas)
        if not texto.strip():raise ValueError('OCR sin texto reconocido')
        return texto


def leer(datos,tipo,url,ocr=False,progreso=None):
    if datos.startswith(b'%PDF-') or 'pdf' in tipo.lower():return pdf(datos,ocr,progreso)
    if tipo.lower().startswith(('image/jpeg','image/png')):
        if not ocr:raise ValueError('Imagen de publicación requiere OCR')
        with tempfile.TemporaryDirectory() as d:
            image=Path(d)/'publicacion';image.write_bytes(datos)
            r=subprocess.run(['tesseract',str(image),'stdout','-l','spa+eng'],capture_output=True,text=True,check=True,timeout=20,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
            if not r.stdout.strip():raise ValueError('Imagen sin texto reconocido')
            return r.stdout
    if datos.startswith(b'PK'):
        with zipfile.ZipFile(BytesIO(datos)) as z:
            if 'word/document.xml' in z.namelist():return docx(datos)
            if sum(i.file_size for i in z.infolist())>32_000_000:raise ValueError('ZIP excede tamaño seguro')
            textos=[]
            for i in z.infolist():
                nombre=i.filename.lower()
                if nombre.endswith(('.pdf','.docx','.txt')):
                    contenido=z.read(i)
                    textos.append(contenido.decode('utf-8') if nombre.endswith('.txt') else leer(contenido,'',nombre,ocr,progreso))
            if not textos:raise ValueError('ZIP sin documentos de contratación legibles')
            return '\n'.join(textos)
    raise ValueError('Formato de documento no admitido: '+tipo)
