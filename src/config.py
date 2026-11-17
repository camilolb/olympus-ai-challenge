from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTOS = ROOT / 'data' / 'documentos'
CATALOGO = ROOT / 'data' / 'tablas' / 'catalogo_productos_2026_11.xlsx'
CHROMA_PATH = ROOT / 'data' / 'chroma'
CHROMA_HOST = os.environ.get('CHROMA_HOST')  # sin valor: base embebida en CHROMA_PATH
CHROMA_PORT = int(os.environ.get('CHROMA_PORT', '8000'))
COLLECTION_NAME = 'banco_nebula'
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434')
LLM_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')
OLLAMA_TIMEOUT_S = float(os.environ.get('OLLAMA_TIMEOUT_S', '120'))
LLM_TEMPERATURA = 0.0  # respuestas repetibles: mismo contexto, misma respuesta

# Búsqueda
METRICA_DISTANCIA = 'cosine'  # 0 = mismo sentido, 1 = sin relación
ESTADO_OBSOLETO = 'OBSOLETO'
# Calibrado con las preguntas públicas: las que tienen respuesta encuentran algo por
# debajo de 0.43; P10 (sin respuesta) no baja de 0.62. Más allá de este valor no se llama
# al modelo. P07 (0.45) no se separa por distancia: esa la resuelve el modelo con sus reglas.
DISTANCIA_MAXIMA_RELEVANTE = 0.6
