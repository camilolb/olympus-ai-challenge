from src.busqueda import id_fragmento, referencia
from src.documentos import cargar_todo


def test_ids_unicos_y_estables():
    docs = cargar_todo()
    ids = [id_fragmento(d['metadatos']) for d in docs]
    assert len(set(ids)) == len(ids)
    assert ids == [id_fragmento(d['metadatos']) for d in cargar_todo()]


def test_referencia_legible():
    txt = {'doc_id': 'POL-CVH-2026', 'seccion': '1', 'tipo': 'txt'}
    xlsx = {'doc_id': 'CAT-PROD-2026-11', 'seccion': 'AHO-BRISA', 'tipo': 'xlsx'}
    assert referencia(txt) == 'POL-CVH-2026 §1'
    assert referencia(xlsx) == 'CAT-PROD-2026-11 · AHO-BRISA'
