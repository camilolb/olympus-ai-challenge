# Asistente de Banco Nébula

Responde preguntas sobre los productos y políticas de un banco ficticio usando solo sus documentos. Si la respuesta no está ahí, lo dice en vez de inventarla.

El enunciado original del reto está en [RETO.md](RETO.md).

## Cómo funciona

Cuando llega una pregunta:

1. Se buscan en Chroma los fragmentos de documento que más se parecen a la pregunta. Las políticas viejas de 2025 solo se traen si la pregunta habla del pasado.
2. Si ningún fragmento se parece lo suficiente, se responde "No encuentro esa información en los documentos disponibles" sin llamar al modelo.
3. Si hay algo útil, se le pasan los fragmentos a Qwen con unas reglas: responder en español, usar solo lo que dicen los documentos y citar de dónde sale cada dato.

La respuesta vuelve junto con las fuentes que se usaron.

## Chat con traza

Además de la API hice una página para ver qué pasa por dentro con cada pregunta. A la izquierda está el chat y a la derecha cada función que se va ejecutando, en orden y con lo que tardó.

![Chat y traza](capturas/01-chat-y-traza.png)

Si se toca una fila se ve lo que recibió y lo que devolvió. En la búsqueda salen los fragmentos que encontró, si están vigentes u obsoletos y la distancia a la pregunta (entre más cerca de 0, más se parecen).

![Búsqueda](capturas/02-busqueda.png)

Este es el mensaje tal cual le llega al modelo: las reglas arriba y los fragmentos abajo.

![Mensaje al modelo](capturas/03-mensaje-al-modelo.png)

Y esto devuelve Ollama: la respuesta, los tokens que leyó y escribió y lo que se demoró.

![Respuesta de Qwen](capturas/04-respuesta-de-qwen.png)

Si se pregunta algo que no está en los documentos, el fragmento más cercano queda a 0.62 y el límite es 0.6, así que se responde sin pasar por el modelo. Por eso tarda 132 ms y no 15 segundos.

![Sin información](capturas/05-sin-informacion.png)

## Cómo correrlo

Hace falta Docker y Ollama abierto en el equipo.

```bash
ollama pull qwen2.5:7b
docker compose up -d --build
docker compose exec app python -m scripts.indexar
```

Luego:

- Chat con traza: http://127.0.0.1:8020
- API: http://127.0.0.1:8010/docs

Para las pruebas y las 10 preguntas de práctica:

```bash
docker compose exec app python -m pytest -q
docker compose exec app python -m scripts.probar_preguntas
```

## Más detalle

En [ENTREGA.md](ENTREGA.md) explico por qué hice cada cosa, cómo salieron las 10 preguntas y qué falta mejorar.
