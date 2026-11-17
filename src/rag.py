"""Orquestación de la búsqueda y la generación."""
import re

from src.busqueda import buscar, referencia
from src.config import DISTANCIA_MAXIMA_RELEVANTE, ESTADO_OBSOLETO
from src.llm import SIN_INFORMACION, generar


def es_historica(pregunta: str) -> bool:
    """Heurística inicial proporcionada, puede modificarse si se justifica."""
    return bool(re.search(
        r'\b2025\b|hist[oó]ric|obsolet|versi[oó]n|compar|cambi[oó]|diferencia',
        pregunta.lower()
    ))


def recuperar(pregunta: str, k: int) -> list[dict]:
    """Vigentes siempre. Si la pregunta es histórica, se suman los obsoletos aparte:
    en una sola lista una versión desplaza a la otra y la comparación queda coja."""
    vigentes = buscar(pregunta, k=k)
    if not es_historica(pregunta):
        return vigentes
    obsoletos = [
        h for h in buscar(pregunta, k=k, incluir_obsoletos=True)
        if h['metadatos']['estado'] == ESTADO_OBSOLETO
    ]
    return sorted(vigentes + obsoletos, key=lambda h: h['distancia'])


def hay_respaldo(hallazgos: list[dict]) -> bool:
    """¿Algo se parece lo suficiente a la pregunta? Se mira solo el más cercano: filtrar
    fragmento por fragmento descartaba textos útiles que quedaban justo en el borde."""
    return any(h['distancia'] <= DISTANCIA_MAXIMA_RELEVANTE for h in hallazgos)


def fuente(hallazgo: dict) -> dict:
    m = hallazgo['metadatos']
    return {
        'id': referencia(m),
        'archivo': m['fuente'],
        'estado': m['estado'],
        'distancia': round(hallazgo['distancia'], 4),
        'fragmento': hallazgo['contenido'],
    }


def preguntar(pregunta: str, k: int = 7) -> dict:
    """Devolver {pregunta, respuesta, fuentes_recuperadas}."""
    pregunta = pregunta.strip()
    if not pregunta:
        raise ValueError('La pregunta está vacía')

    hallazgos = recuperar(pregunta, k)
    # Si nada se parece lo suficiente, no se le pregunta al modelo: no hay de dónde responder.
    respuesta = generar(pregunta, hallazgos) if hay_respaldo(hallazgos) else SIN_INFORMACION
    return {
        'pregunta': pregunta,
        'respuesta': respuesta,
        'fuentes_recuperadas': [fuente(h) for h in hallazgos],
    }
