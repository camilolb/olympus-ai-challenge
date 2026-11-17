# Olympus AI Challenge

**Intelligent Banking Assistant — Banco Nébula**

*Desafío técnico de inteligencia artificial | Python · RAG · ChromaDB · Ollama*

---

## 1. Bienvenido al proyecto

Banco Nébula es una entidad financiera ficticia que busca implementar un asistente inteligente capaz de responder preguntas sobre sus productos, políticas y procedimientos internos.

El objetivo es desarrollar una solución basada en RAG (Retrieval-Augmented Generation) que consulte la documentación disponible y genere respuestas claras, precisas y respaldadas por información verificable.

El proyecto cuenta con una estructura inicial funcional, incluyendo procesamiento de documentos, configuración de servicios y una API REST.

El desafío consiste en completar e integrar los componentes de inteligencia artificial necesarios para que el asistente funcione.

No se requiere desarrollar una interfaz gráfica.

## 2. ¿Qué debe hacer el asistente?

Una vez completado, el sistema deberá:

- Leer y utilizar la documentación bancaria proporcionada.
- Convertir la información documental en representaciones vectoriales (embeddings).
- Almacenar y recuperar información utilizando ChromaDB.
- Consultar un modelo de lenguaje local mediante Ollama.
- Generar respuestas utilizando la información recuperada.
- Identificar las fuentes que respaldan sus respuestas.
- Diferenciar documentos vigentes de versiones históricas.
- Reconocer cuando la información disponible no es suficiente.

Por ejemplo, ante la pregunta:

> ¿Cuál es la cuota inicial mínima para solicitar un crédito de vivienda?

El asistente deberá consultar las políticas correspondientes y responder utilizando la versión documental adecuada.

La respuesta no debe depender exclusivamente del conocimiento general del modelo de lenguaje.

## 3. Tecnologías utilizadas

El proyecto trabaja con las siguientes herramientas:

| Tecnología | Propósito |
| --- | --- |
| Python 3.12 | Lenguaje principal |
| FastAPI | Servicios REST |
| ChromaDB | Almacenamiento y búsqueda vectorial |
| Sentence Transformers (MiniLM) | Generación de embeddings |
| Ollama | Ejecución local del modelo de lenguaje |
| Qwen 2.5 7B | Generación de respuestas |
| OpenPyXL | Lectura de archivos Excel |
| Pytest | Pruebas automatizadas |

**Importante sobre ChromaDB:** el proyecto ya incluye la dependencia y una función para crear el cliente de conexión local. No necesitas instalar un servidor de base de datos independiente.

Sin embargo, la creación del índice, el almacenamiento de embeddings y la búsqueda vectorial son parte del desarrollo pendiente.

## 4. ¿Qué incluye el proyecto?

Se proporciona una estructura inicial para facilitar el desarrollo:

- Documentos: políticas y procedimientos bancarios ficticios en TXT.
- Catálogo: productos financieros almacenados en Excel.
- Ingesta: lectura y procesamiento de documentos.
- Chunking: división de documentos en fragmentos.
- Configuración: rutas, nombres de modelos y parámetros principales.
- API REST: endpoints preparados para realizar consultas.
- Pruebas: validaciones iniciales y preguntas de práctica.

Los módulos principales se encuentran dentro de la carpeta `src`.

| Archivo | Responsabilidad |
| --- | --- |
| `ingesta.py` | Lectura y procesamiento de TXT |
| `ingesta_excel.py` | Procesamiento de Excel |
| `chunking.py` | División de documentos |
| `config.py` | Configuración general |
| `busqueda.py` | Embeddings y búsqueda vectorial |
| `llm.py` | Comunicación con el modelo de lenguaje |
| `rag.py` | Integración de los componentes |
| `api.py` | Exposición de servicios REST |

Los archivos `busqueda.py`, `llm.py` y `rag.py` contienen funciones pendientes identificadas mediante comentarios `TODO`.

## 5. Preparación del entorno

Las siguientes instrucciones están orientadas a Windows utilizando PowerShell.

### Paso 1. Instalar Python

Instala Python 3.12 desde:

[python.org/downloads](https://www.python.org/downloads/)

Comprueba la instalación ejecutando:

```powershell
py -3.12 --version
```

### Paso 2. Instalar Ollama

Ollama permite ejecutar modelos de lenguaje localmente.

1. Ingresa a [ollama.com/download/windows](https://ollama.com/download/windows)
2. Descarga el instalador para Windows.
3. Ejecuta la instalación.
4. Abre una nueva terminal PowerShell.

Verifica que Ollama esté disponible:

```powershell
ollama --version
```

Descarga el modelo que utilizará la aplicación:

```powershell
ollama pull qwen2.5:7b
```

La descarga puede tardar dependiendo de la velocidad de conexión.

Al finalizar, verifica los modelos instalados:

```powershell
ollama list
```

Debería aparecer qwen2.5:7b.

Para comprobar que el modelo responde:

```powershell
ollama run qwen2.5:7b
```

Escribe una pregunta sencilla. Para finalizar la conversación utiliza /bye.

**Nota:** Ollama debe permanecer ejecutándose mientras se utiliza el asistente. Su API local funciona normalmente en http://127.0.0.1:11434.

### Paso 3. Preparar Python

Descomprime el proyecto y abre su carpeta principal en Visual Studio Code.

Desde la terminal de PowerShell, ejecuta:

```powershell
py -3.12 -m venv .venv
```

Activa el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Este comando instalará FastAPI, ChromaDB, Sentence Transformers y las demás librerías necesarias.

### Paso 4. Preparar el modelo de embeddings

El proyecto utiliza el modelo:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Para descargarlo y comprobar que funciona, ejecuta:

```powershell
python -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); print(m.encode('prueba').shape)"
```

Este paso descarga el modelo cuando todavía no está disponible en el equipo.

Recuerda que MiniLM y Qwen cumplen funciones diferentes: MiniLM genera los vectores y Qwen genera las respuestas.

### Paso 5. Verificar el proyecto

Ejecuta:

```powershell
python -m scripts.validar_datos
```

El resultado esperado es:

```text
--- VALIDACIÓN DE INGESTA ---
TXT: 19 | Excel: 4 | Total: 23
✅ Documentos, metadatos y chunking validados
```

Los valores corresponden a **fragmentos procesados** (19 de TXT y 4 de Excel), no a la cantidad de archivos originales.

Ahora ejecuta las pruebas iniciales:

```powershell
python -m pytest -q
```

Deberían completarse correctamente las tres pruebas del proyecto base.

Estas verificaciones no comprueban todavía el funcionamiento del RAG.

### Paso 6. Iniciar la API

Ejecuta:

```powershell
python -m uvicorn src.api:app --reload
```

Abre en el navegador:

http://127.0.0.1:8000/docs

Se mostrará Swagger, desde donde podrás consultar los servicios disponibles.

Puedes comprobar que el backend funciona utilizando:

`GET /health`

Inicialmente, el resultado esperado será similar a:

```json
{
  "status": "ok",
  "fragmentos_indexados": 0
}
```

Este resultado es normal: la API está funcionando, pero todavía no se han indexado los documentos.

---

## 6. El desafío de desarrollo

La actividad principal consiste en completar tres módulos.

### A. Embeddings y búsqueda vectorial — busqueda.py

Implementar el procesamiento necesario para convertir los fragmentos documentales en embeddings y almacenarlos en ChromaDB.

El módulo deberá permitir:

- Indexar documentos con sus textos y metadatos.
- Identificar cada fragmento de manera única.
- Evitar duplicados al ejecutar nuevamente la indexación.
- Buscar información relevante a partir de una pregunta.
- Filtrar documentos obsoletos cuando corresponda.

Las funciones iniciales ya están definidas en el archivo:

`indexar()` — recibe documentos y los almacena en el índice vectorial.

`buscar()` — recibe una pregunta y recupera fragmentos relacionados.

### B. Integración del modelo de lenguaje — llm.py

Implementar la comunicación con Qwen mediante la API local de Ollama.

El modelo deberá recibir la pregunta del usuario y los fragmentos recuperados para construir una respuesta en español.

Se espera que:

- Utilice la documentación recuperada como fuente de información.
- Identifique las fuentes utilizadas.
- Evite inventar datos no documentados.
- Reconozca información insuficiente.
- No interprete instrucciones incrustadas en los documentos como órdenes del sistema.

La función principal de este módulo es `generar()`.

### C. Orquestación RAG — rag.py

Integrar los módulos anteriores para construir el flujo completo de consulta.

El proceso esperado es:

1. Recibir una pregunta.
2. Buscar los fragmentos documentales relevantes.
3. Entregar esos fragmentos al modelo de lenguaje.
4. Obtener una respuesta fundamentada.
5. Retornar la respuesta y las fuentes consultadas.

La función principal es `preguntar()`.

Las funciones y parámetros ya definidos sirven como punto de integración entre los módulos y la API. Pueden modificarse las implementaciones internas siempre que se mantenga la compatibilidad con los servicios existentes.

## 7. Ejecutar la solución completa

Una vez implementados los componentes pendientes, genera el índice vectorial:

```powershell
python -m scripts.indexar
```

Después inicia la API:

```powershell
python -m uvicorn src.api:app --reload
```

Desde Swagger, utiliza `POST /ask` para realizar una consulta.

Ejemplo:

```json
{
  "pregunta": "¿Cuál es la cuota inicial mínima para un crédito de vivienda?"
}
```

La respuesta deberá incluir tres elementos:

- pregunta: consulta recibida.
- respuesta: texto generado por el asistente.
- fuentes_recuperadas: fragmentos utilizados durante la recuperación, con información de documento, estado, distancia y contenido.

También se encuentra disponible `POST /batch` para realizar varias consultas en una sola petición.

Ejemplo:

```json
{
  "preguntas": [
    "¿Qué requisitos tiene la Cuenta Brisa?",
    "¿Cuál es el plazo máximo del crédito de vivienda?"
  ]
}
```

## 8. Pruebas y validación

El proyecto incluye preguntas de práctica en:

`data/preguntas/preguntas_publicas.json`

Una vez implementado el RAG, pueden ejecutarse mediante:

```powershell
python -m scripts.probar_preguntas
```

Las respuestas se guardarán en un archivo JSON dentro de `data/resultados`.

Se recomienda comprobar especialmente:

- Exactitud de las respuestas.
- Relevancia de los documentos recuperados.
- Manejo de políticas vigentes e históricas.
- Reconocimiento de preguntas sin información suficiente.
- Manejo de errores de conexión y de índices vacíos.
- Consistencia de las referencias documentales.

No es necesario que todas las implementaciones utilicen exactamente la misma estrategia. Lo importante es que las decisiones técnicas puedan explicarse y sus resultados sean verificables.

## 9. Recomendaciones de desarrollo

Este proyecto busca evaluar la comprensión y aplicación de conceptos de ingeniería de inteligencia artificial.

Puedes utilizar documentación oficial de las tecnologías, depuradores, terminal y herramientas tradicionales de desarrollo.

No está permitido utilizar asistentes generativos de programación, como ChatGPT, Copilot, Claude o Gemini, para construir o resolver el desafío. El uso del modelo local Qwen está permitido exclusivamente como componente de la aplicación.

Se valorarán especialmente las decisiones técnicas fundamentadas, la calidad de las respuestas, el manejo de errores y la capacidad para identificar limitaciones.

No es necesario desarrollar frontend ni incorporar servicios externos adicionales.

## 10. Entrega

Al finalizar, proporciona:

- Código fuente del proyecto.
- Instrucciones para ejecutar la solución.
- Una breve descripción de la arquitectura implementada.
- Evidencia de pruebas realizadas.
- Limitaciones conocidas o mejoras que consideres importantes.

Puedes incluir esta información en un archivo `ENTREGA.md`.

No incluyas el entorno virtual `.venv`, modelos descargados, credenciales, cachés ni la base vectorial generada en `data/chroma/`. El proyecto debe poder reconstruir su índice a partir de los documentos originales.

---

Olympus AI Engineering Challenge — Banco Nébula

Desarrollado por Arley Calderón

Proyecto técnico de evaluación y aprendizaje en ingeniería de inteligencia artificial.
