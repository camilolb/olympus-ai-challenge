FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
# chromadb igual a la versión del servidor; torch solo CPU (Docker en Mac no usa la GPU).
RUN pip install --no-cache-dir --root-user-action=ignore \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      -r /tmp/requirements.txt chromadb==1.5.9
