"""Embeddings, almacenamiento y recuperación vectorial.

Contrato requerido:
- indexar(documentos): agrega los documentos a la colección de Chroma y devuelve su cantidad.
- buscar(pregunta, k, incluir_obsoletos): devuelve una lista ordenada de hallazgos.

Cada hallazgo debe tener: contenido (str), metadatos (dict), distancia (float).
"""
from functools import lru_cache

from src.config import (
    CHROMA_HOST, CHROMA_PATH, CHROMA_PORT, COLLECTION_NAME, EMBEDDING_MODEL,
    ESTADO_OBSOLETO, METRICA_DISTANCIA,
)


def cliente_chroma():
    import chromadb
    if CHROMA_HOST:
        return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


@lru_cache(maxsize=1)
def _modelo():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def vectorizar(textos: list[str]) -> list[list[float]]:
    """El mismo modelo para documentos y preguntas. Se normaliza para comparar por coseno."""
    return _modelo().encode(textos, normalize_embeddings=True).tolist()


def coleccion():
    # Los vectores se calculan aquí, no dentro de Chroma: por eso embedding_function=None.
    return cliente_chroma().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={'hnsw:space': METRICA_DISTANCIA},
        embedding_function=None,
    )


def id_fragmento(metadatos: dict) -> str:
    """Identificador estable: el mismo fragmento siempre recibe el mismo id."""
    return f"{metadatos['doc_id']}::{metadatos['seccion']}::{metadatos['subfragmento']}"


def referencia(metadatos: dict) -> str:
    """Cómo se cita un fragmento: POL-CVH-2026 §1 o CAT-PROD-2026-11 · AHO-BRISA."""
    if metadatos.get('tipo') == 'txt':
        return f"{metadatos['doc_id']} §{metadatos['seccion']}"
    return f"{metadatos['doc_id']} · {metadatos['seccion']}"


def indexar(documentos: list[dict]) -> int:
    """Generar embeddings, persistirlos en Chroma, devolver cantidad indexada."""
    if not documentos:
        return 0
    ids = [id_fragmento(d['metadatos']) for d in documentos]
    if len(set(ids)) != len(ids):
        raise ValueError('Hay fragmentos con el mismo identificador')

    textos = [d['contenido'] for d in documentos]
    col = coleccion()
    # upsert reemplaza lo que ya existe: reindexar no duplica.
    col.upsert(
        ids=ids,
        embeddings=vectorizar(textos),
        documents=textos,
        metadatas=[d['metadatos'] for d in documentos],
    )
    sobrantes = set(col.get(include=[])['ids']) - set(ids)
    if sobrantes:  # fragmentos de documentos que ya no existen
        col.delete(ids=list(sobrantes))
    return len(ids)


def buscar(pregunta: str, k: int = 7, incluir_obsoletos: bool = False) -> list[dict]:
    """Recuperar hasta k fragmentos relevantes, filtrando obsoletos si corresponde."""
    if not pregunta.strip():
        raise ValueError('La pregunta está vacía')
    col = coleccion()
    total = col.count()
    if total == 0:
        raise RuntimeError('El índice está vacío. Ejecuta: python -m scripts.indexar')

    filtro = None if incluir_obsoletos else {'estado': {'$ne': ESTADO_OBSOLETO}}
    r = col.query(
        query_embeddings=vectorizar([pregunta]),
        n_results=min(k, total),
        where=filtro,
        include=['documents', 'metadatas', 'distances'],
    )
    return [
        {'contenido': texto, 'metadatos': meta, 'distancia': float(dist)}
        for texto, meta, dist in zip(r['documents'][0], r['metadatas'][0], r['distances'][0])
    ]
