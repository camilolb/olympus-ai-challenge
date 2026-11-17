# Entrega · Asistente de Banco Nébula

Asistente RAG que responde preguntas sobre los productos y políticas de Banco Nébula usando solo sus documentos. Busca en ChromaDB con embeddings de MiniLM y redacta con Qwen 2.5 7B en Ollama.

## Cómo correrlo

### Con Docker

Ollama corre en el equipo (así usa la GPU). La base y la API corren en contenedores.

```bash
ollama pull qwen2.5:7b                                  # Ollama debe quedar abierto
docker compose up -d --build                            # chroma, api y chat con traza
docker compose exec app python -m scripts.indexar       # 23 fragmentos a Chroma
```

| Servicio | Dirección |
| --- | --- |
| API (Swagger) | http://127.0.0.1:8010/docs |
| Chat con traza | http://127.0.0.1:8020 |
| ChromaDB | http://127.0.0.1:8100 |

```bash
docker compose exec app python -m pytest -q
docker compose exec app python -m scripts.probar_preguntas
```

### Sin Docker

Los mismos pasos de RETO.md. Si no existe la variable `CHROMA_HOST`, la base queda embebida en `data/chroma/`.

## Arquitectura

```text
Indexación
  data/documentos (5 TXT) + data/tablas (Excel) ──► 23 fragmentos
  ──► MiniLM: 384 números normalizados ──► Chroma (coseno), upsert con id doc::sección::subfragmento

Consulta
  POST /ask ──► rag.preguntar
                 ├─ recuperar ──► busqueda.buscar: k vigentes (where estado != OBSOLETO)
                 │              └► si es_historica: otra búsqueda para sumar obsoletos
                 ├─ hay_respaldo: ¿el fragmento más cercano está a ≤ 0.6?
                 │      no ──► "No encuentro esa información en los documentos disponibles."
                 └─ llm.generar ──► construir_mensajes ──► Ollama /api/chat (qwen2.5:7b, temperatura 0)
           ◄── { pregunta, respuesta, fuentes_recuperadas[id, archivo, estado, distancia, fragmento] }
```

| Archivo | Qué hace |
| --- | --- |
| `src/busqueda.py` | Vectores con MiniLM, colección en Chroma, `indexar()` y `buscar()` |
| `src/llm.py` | Reglas para el modelo, armado del mensaje y llamada a Ollama |
| `src/rag.py` | `preguntar()`: recuperar, decidir si hay respaldo, generar y armar las fuentes |
| `traza/` | Chat que corre el flujo real y muestra cada función con su entrada, salida y tiempo |

## Decisiones

| Decisión | Por qué |
| --- | --- |
| Distancia coseno con vectores normalizados | MiniLM no entrega vectores normalizados, y con la distancia l2 que usa Chroma por defecto los números no se pueden interpretar. Con coseno van de 0 (mismo sentido) a 1 (sin relación). |
| Ids fijos, `upsert` y borrado de sobrantes | Reindexar no duplica: `/health` sigue en 23 después de indexar dos veces. Si se borra un documento, sus fragmentos también salen. |
| `embedding_function=None` en la colección | Los vectores los calcula MiniLM. Así Chroma nunca usa su modelo por defecto, que es otro. |
| Filtro `estado != OBSOLETO` | El catálogo tiene estado `VIGENTE EN EL PERÍODO`. Con un filtro `== VIGENTE` se perdían todas las tasas. |
| Dos búsquedas en preguntas históricas | En una sola lista, los fragmentos de 2025 desplazaban el plazo de 2026 y en P03 el modelo terminaba deduciendo el dato. Ahora los vigentes tienen sus k cupos y los obsoletos se suman aparte. |
| Umbral de 0.6 como compuerta | Si nada se parece, no se llama al modelo (P10 queda a 0.62). Primero lo usé como filtro fragmento por fragmento y cortaba textos útiles en el borde: en «¿Qué cambió entre 2025 y 2026 en la cuota inicial?», POL-CVH-2026 §1 quedaba a 0.61. Ahora solo se mira el más cercano. |
| P07 la resuelve el modelo | Su mejor fragmento está a 0.45, igual que preguntas que sí tienen respuesta. Ningún umbral la separa, así que se abstiene por las reglas. |
| Reglas en `system`, datos en `user` | Los fragmentos van dentro de etiquetas `<fragmento>` con referencia, estado y vigencia. Si un documento trae `</fragmento>`, se neutraliza para que no pueda cerrar la etiqueta y hacerse pasar por instrucción. |
| Fecha de hoy en el mensaje | El catálogo solo vale del 1 al 30 de noviembre de 2026. Sin la fecha, el modelo no puede saber si una tasa está vigente. |
| Temperatura 0 | La misma pregunta con el mismo contexto da la misma respuesta. Así se puede comparar entre corridas. |
| Errores con mensaje claro | Ollama apagado: `RuntimeError` con la dirección, que la API devuelve como 503. Índice vacío: 503 con el comando para indexar. |

## Evidencia

```text
$ python -m scripts.validar_datos
TXT: 19 | Excel: 4 | Total: 23
✅ Documentos, metadatos y chunking validados

$ python -m pytest -q
13 passed
```

Las pruebas nuevas cubren:
- ids únicos y estables;
- que un documento no pueda cerrar su etiqueta;
- que Ollama apagado dé un error claro;
- que no se llame al modelo sin respaldo;
- que con respaldo el modelo reciba todos los fragmentos;
- que una pregunta actual no traiga obsoletos;
- que una histórica sí los traiga, ordenados;
- el formato de las fuentes;
- que se rechace una pregunta vacía.

Resultado de las 10 preguntas públicas. El detalle completo con fuentes está en `evidencia/preguntas_publicas.json`, porque `data/resultados/` está ignorado por git.

| Pregunta | Respuesta | Cita |
| --- | --- | --- |
| P01 saldo mínimo Cuenta Brisa | COP 0 ✓ | POL-CAB-2026 §2 |
| P02 cuota inicial vigente | 25 % ✓ | POL-CVH-2026 §1 |
| P03 cambios 2025 → 2026 | 2 → 3 SMMLV, 20 → 25 %, 25 → 20 años ✓ | 2025 §1, 2026 §1, 2026 §2 |
| P04 tasa del crédito de vivienda | 13,2 % E.A. ✓ | CAT-PROD-2026-11 · CRE-VIV-HOR |
| P05 ¿asesor pide OTP? | No ✓ | SEG-2026 §1 |
| P06 operación no reconocida | Bloquear, reportar, número de caso; revisión en máximo 2 días hábiles ✓ | SEG-2026 §2 y §3 |
| P07 tasa de diciembre de 2027 | No hay información ✓ (lo decide el modelo) | — |
| P08 documentos de un independiente | Identidad, autorización, extractos, declaración y avalúo ✓ | POL-CVH-2026 §3 |
| P09 cuota de manejo y tasa Brisa | COP 0 y 1,5 % ✓ | La cita de la cuota es imprecisa (ver limitaciones) |
| P10 transferencia a Japón | No hay información ✓ (no llega al modelo) | — |

En un Mac con Ollama en la GPU, las 10 preguntas tardan unos 80 segundos.

## Limitaciones y mejoras

- **Umbral:** el 0.6 está calibrado con solo 10 preguntas. Con preguntas nuevas puede quedarse corto o pasarse.
- **`es_historica()`:** decide por palabras clave. «¿Qué versión aplica hoy?» la marca como histórica; no rompe nada, solo suma obsoletos al contexto.
- **Citas:** un modelo de 7B a veces cita mal. En P09 atribuye la cuota a POL-CAB-2026 §4 cuando el dato está en el catálogo. Mejora: comparar las citas contra las fuentes recuperadas y quitar las que no correspondan.
- **Recuperación:** los fragmentos son cortos y se parecen entre sí, así que el clave a veces sale quinto (P05). Mejora: búsqueda híbrida (palabras + vectores) o un reranker.
- **Detalles de la API original:** `/batch` falla completo si falla una pregunta, y una pregunta con solo espacios devuelve 503 cuando debería ser 400.
- **Sin streaming:** la respuesta llega completa, sin ir mostrándose a medida que se escribe.
- **Vigencia del catálogo:** desde el 1 de diciembre de 2026 el catálogo sale de vigencia. El modelo recibe la fecha del día para poder aclararlo, pero no lo probé con una fecha de diciembre.
