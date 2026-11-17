"""Chat con traza: ejecuta el flujo real de src/ y cuenta cada paso mientras ocurre.

No cambia src/. Envuelve sus funciones: cada llamada emite un evento de inicio y otro
de fin (entrada, salida y duración) que la página recibe por Server-Sent Events.
Fuera de una petición de traza las envolturas no hacen nada.
"""
import contextvars
import itertools
import json
import queue
import threading
import time
from pathlib import Path

import requests
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse

from src import busqueda, documentos, llm, rag
from src.config import (
    COLLECTION_NAME, DISTANCIA_MAXIMA_RELEVANTE, ESTADO_OBSOLETO, LLM_MODEL,
    LLM_TEMPERATURA, OLLAMA_URL,
)

K_POR_DEFECTO = 7
K_MAXIMO = 15
LARGO_VISTA_PREVIA = 160
MUESTRA_VECTOR = 8
NS_POR_SEGUNDO = 1e9
MS_POR_SEGUNDO = 1000
TIMEOUT_SALUD_S = 3
FIN = object()

_emitir = contextvars.ContextVar('emitir', default=None)
_padre = contextvars.ContextVar('padre', default=None)
_ids = itertools.count(1)


def ms_desde(t0: float) -> float:
    return round((time.perf_counter() - t0) * MS_POR_SEGUNDO, 1)


def instrumentar(modulo, nombre: str, entrada, salida) -> None:
    """Reemplaza modulo.nombre por una versión que avisa al empezar y al terminar."""
    original = getattr(modulo, nombre)
    funcion = f'{original.__module__}.{original.__qualname__}'

    def envoltura(*args, **kwargs):
        emitir = _emitir.get()
        if emitir is None:
            return original(*args, **kwargs)
        id_ = next(_ids)
        emitir({'tipo': 'inicio', 'id': id_, 'padre': _padre.get(), 'funcion': funcion,
                'entrada': entrada(*args, **kwargs)})
        token = _padre.set(id_)
        t0 = time.perf_counter()
        try:
            resultado = original(*args, **kwargs)
        except Exception as exc:
            emitir({'tipo': 'error', 'id': id_, 'ms': ms_desde(t0), 'error': f'{type(exc).__name__}: {exc}'})
            raise
        finally:
            _padre.reset(token)
        emitir({'tipo': 'fin', 'id': id_, 'ms': ms_desde(t0), 'salida': salida(resultado)})
        return resultado

    setattr(modulo, nombre, envoltura)


# ---------- resúmenes legibles de entradas y salidas ----------

def vista(texto: str) -> str:
    return texto if len(texto) <= LARGO_VISTA_PREVIA else texto[:LARGO_VISTA_PREVIA].rstrip() + '…'


def resumen_hallazgos(hallazgos: list[dict]) -> list[dict]:
    return [{
        'ref': busqueda.referencia(h['metadatos']),
        'estado': h['metadatos']['estado'],
        'distancia': round(h['distancia'], 4),
        'texto': vista(h['contenido']),
    } for h in hallazgos]


def resumen_vectores(vectores: list[list[float]]) -> dict:
    primero = vectores[0] if vectores else []
    return {'vectores': len(vectores), 'dimensiones': len(primero),
            'muestra': [round(x, 4) for x in primero[:MUESTRA_VECTOR]]}


def resumen_coleccion(col) -> dict:
    return {'nombre': col.name, 'fragmentos': col.count(), 'metrica': (col.metadata or {}).get('hnsw:space')}


def resumen_ollama(r: dict) -> dict:
    escritura_s = r.get('eval_duration', 0) / NS_POR_SEGUNDO
    escritos = r.get('eval_count') or 0
    return {
        'respuesta': r.get('message', {}).get('content', ''),
        'tokens_leidos': r.get('prompt_eval_count'),
        'tokens_escritos': escritos,
        'tokens_por_segundo': round(escritos / escritura_s, 1) if escritura_s else None,
        'segundos_cargando_modelo': round(r.get('load_duration', 0) / NS_POR_SEGUNDO, 2),
        'segundos_total': round(r.get('total_duration', 0) / NS_POR_SEGUNDO, 2),
    }


def resumen_carga(docs: list[dict]) -> dict:
    ejemplo = docs[0] if docs else {'contenido': '', 'metadatos': {}}
    return {'fragmentos': len(docs), 'ejemplo': {'contenido': vista(ejemplo['contenido']), 'metadatos': ejemplo['metadatos']}}


def filtro_where(incluir_obsoletos: bool):
    return None if incluir_obsoletos else {'estado': {'$ne': ESTADO_OBSOLETO}}


# Se envuelve el nombre donde lo busca quien llama: rag.buscar es la búsqueda que usa rag.
instrumentar(rag, 'preguntar', lambda pregunta, k=K_POR_DEFECTO: {'pregunta': pregunta, 'k': k},
             lambda r: {'respuesta': r['respuesta'], 'fuentes': len(r['fuentes_recuperadas'])})
instrumentar(rag, 'recuperar', lambda pregunta, k: {'pregunta': pregunta, 'k': k}, resumen_hallazgos)
instrumentar(rag, 'es_historica', lambda pregunta: {'pregunta': pregunta}, lambda r: {'historica': r})
instrumentar(rag, 'buscar',
             lambda pregunta, k=K_POR_DEFECTO, incluir_obsoletos=False: {
                 'k': k, 'incluir_obsoletos': incluir_obsoletos, 'where': filtro_where(incluir_obsoletos)},
             resumen_hallazgos)
instrumentar(rag, 'hay_respaldo',
             lambda hallazgos: {'umbral': DISTANCIA_MAXIMA_RELEVANTE, 'hallazgos': resumen_hallazgos(hallazgos)},
             lambda r: {'respaldo': r})
instrumentar(rag, 'generar', lambda pregunta, hallazgos: {'pregunta': pregunta, 'fragmentos': len(hallazgos)},
             lambda texto: {'respuesta': texto})
instrumentar(busqueda, 'coleccion', lambda: {'nombre': COLLECTION_NAME}, resumen_coleccion)
instrumentar(busqueda, 'vectorizar', lambda textos: {'textos': len(textos), 'primero': vista(textos[0])},
             resumen_vectores)
instrumentar(busqueda, 'indexar', lambda docs: {'fragmentos': len(docs)}, lambda n: {'indexados': n})
instrumentar(llm, 'construir_mensajes', lambda pregunta, hallazgos: {'fragmentos': len(hallazgos)},
             lambda mensajes: {'mensajes': mensajes})
instrumentar(llm, 'llamar_ollama',
             lambda mensajes: {'url': f'{OLLAMA_URL}/api/chat', 'modelo': LLM_MODEL,
                               'temperatura': LLM_TEMPERATURA, 'mensajes': len(mensajes)},
             resumen_ollama)
instrumentar(documentos, 'cargar_txt', lambda: {'carpeta': 'data/documentos'}, resumen_carga)
instrumentar(documentos, 'cargar_excel', lambda: {'archivo': 'data/tablas'}, resumen_carga)
instrumentar(documentos, 'cargar_todo', lambda: {}, lambda docs: {'fragmentos': len(docs)})


def transmitir(trabajo) -> StreamingResponse:
    """Corre el trabajo en un hilo propio y entrega sus eventos a medida que salen."""
    cola: queue.Queue = queue.Queue()
    t0 = time.perf_counter()

    def emitir(evento: dict) -> None:
        cola.put({**evento, 't': ms_desde(t0)})

    def correr() -> None:
        _emitir.set(emitir)  # cada hilo tiene su propio contexto: las trazas no se mezclan
        try:
            emitir({'tipo': 'resultado', 'datos': trabajo()})
        except Exception as exc:
            emitir({'tipo': 'fallo', 'error': f'{type(exc).__name__}: {exc}'})
        finally:
            cola.put(FIN)

    threading.Thread(target=correr, daemon=True).start()

    def eventos():
        while (evento := cola.get()) is not FIN:
            yield f'data: {json.dumps(evento, ensure_ascii=False, default=str)}\n\n'
        yield f'data: {json.dumps({"tipo": "listo", "t": ms_desde(t0)})}\n\n'

    return StreamingResponse(eventos(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache'})


app = FastAPI(title='Banco Nébula · traza')


@app.get('/')
def pagina():
    return FileResponse(Path(__file__).with_name('index.html'))


@app.get('/estado')
def estado():
    try:
        fragmentos = busqueda.coleccion().count()
    except Exception as exc:
        fragmentos = f'error: {exc}'
    try:
        modelos = [m['name'] for m in requests.get(f'{OLLAMA_URL}/api/tags', timeout=TIMEOUT_SALUD_S).json()['models']]
        ollama = LLM_MODEL in modelos
    except requests.RequestException:
        ollama = False
    return {'fragmentos': fragmentos, 'modelo': LLM_MODEL, 'ollama': ollama,
            'umbral': DISTANCIA_MAXIMA_RELEVANTE, 'k': K_POR_DEFECTO, 'k_maximo': K_MAXIMO}


@app.get('/traza/preguntar')
def traza_preguntar(pregunta: str = Query(min_length=1), k: int = Query(K_POR_DEFECTO, ge=1, le=K_MAXIMO)):
    return transmitir(lambda: rag.preguntar(pregunta, k=k))


@app.get('/traza/indexar')
def traza_indexar():
    return transmitir(lambda: {'indexados': busqueda.indexar(documentos.cargar_todo())})
