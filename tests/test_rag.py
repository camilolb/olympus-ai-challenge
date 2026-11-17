import pytest

from src import rag
from src.config import DISTANCIA_MAXIMA_RELEVANTE, ESTADO_OBSOLETO

CERCA = DISTANCIA_MAXIMA_RELEVANTE - 0.2
LEJOS = DISTANCIA_MAXIMA_RELEVANTE + 0.2
CAMPOS_FUENTE = {'id', 'archivo', 'estado', 'distancia', 'fragmento'}


def hallazgo(doc_id: str, estado: str, distancia: float) -> dict:
    return {
        'contenido': f'texto de {doc_id}',
        'distancia': distancia,
        'metadatos': {'doc_id': doc_id, 'seccion': '1', 'tipo': 'txt',
                      'estado': estado, 'fuente': f'{doc_id}.txt'},
    }


VIGENTE = hallazgo('POL-CVH-2026', 'VIGENTE', CERCA)
OBSOLETO = hallazgo('POL-CVH-2025', ESTADO_OBSOLETO, CERCA - 0.1)


def buscar_falso(pregunta, k=7, incluir_obsoletos=False):
    return [OBSOLETO, VIGENTE] if incluir_obsoletos else [VIGENTE]


def test_lejos_no_llama_al_modelo(monkeypatch):
    monkeypatch.setattr(rag, 'buscar', lambda *a, **kw: [hallazgo('SER-2026', 'VIGENTE', LEJOS)])
    monkeypatch.setattr(rag, 'generar', lambda *_: pytest.fail('no debía llamar al modelo'))
    r = rag.preguntar('¿Comisión a Japón?')
    assert r['respuesta'] == rag.SIN_INFORMACION
    assert len(r['fuentes_recuperadas']) == 1


def test_con_respaldo_el_modelo_recibe_todo(monkeypatch):
    borde = hallazgo('POL-CVH-2026', 'VIGENTE', LEJOS)  # útil aunque esté pasado el umbral
    monkeypatch.setattr(rag, 'buscar', lambda *a, **kw: [VIGENTE, borde])
    recibidos = []
    monkeypatch.setattr(rag, 'generar', lambda p, h: recibidos.extend(h) or 'ok')
    rag.preguntar('¿Cuota inicial?')
    assert recibidos == [VIGENTE, borde]


def test_pregunta_actual_no_trae_obsoletos(monkeypatch):
    monkeypatch.setattr(rag, 'buscar', buscar_falso)
    monkeypatch.setattr(rag, 'generar', lambda p, h: 'ok')
    estados = {f['estado'] for f in rag.preguntar('¿Cuota inicial vigente?')['fuentes_recuperadas']}
    assert ESTADO_OBSOLETO not in estados


def test_pregunta_historica_suma_obsoletos_ordenados(monkeypatch):
    monkeypatch.setattr(rag, 'buscar', buscar_falso)
    monkeypatch.setattr(rag, 'generar', lambda p, h: 'ok')
    fuentes = rag.preguntar('¿Qué cambió entre 2025 y 2026?')['fuentes_recuperadas']
    assert [f['estado'] for f in fuentes] == [ESTADO_OBSOLETO, 'VIGENTE']
    assert all(set(f) == CAMPOS_FUENTE for f in fuentes)


def test_pregunta_vacia():
    with pytest.raises(ValueError):
        rag.preguntar('   ')
