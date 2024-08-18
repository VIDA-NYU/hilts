#------------------------------------
FROM python:3.9-slim-bookworm as base
#------------------------------------

# RUN apt-get update \
#     && apt-get upgrade \
#     # && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

#-------------------------------------------
FROM node:18-bookworm-slim as client-builder
#-------------------------------------------

COPY client/package.json client/package-lock.json /app/client/
WORKDIR /app/client

RUN npm install

COPY client /app/client
RUN npm run build

#-------------------
FROM base as builder
#-------------------

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.6.1

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock /app/

RUN poetry config installer.max-workers 10 && \
    poetry config virtualenvs.in-project true
RUN poetry install --only=main --no-root

COPY mmdx /app/mmdx/
RUN poetry build
RUN poetry run pip install dist/mmdx-*.whl

#-----------------
FROM base as final
#-----------------

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

# Create non-root user and setup app directory
RUN useradd --create-home mmdx
RUN chown -R mmdx /app
USER mmdx

# Copy application files to the final image
COPY --chown=mmdx --from=builder /app/.venv /app/.venv
COPY --chown=mmdx --from=client-builder /app/client/dist/ /app/client/dist/
COPY --chown=mmdx client/public/ /app/client/public/

# Activate venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Download and cache the model inside the image
RUN <<EOF
python <<HEREDOC
from mmdx.model import ClipModel
model = ClipModel()
HEREDOC
EOF

# Setup env variables
ENV ENV=prod
ENV GUNICORN_CMD_ARGS="--workers=1 --threads=4 --worker-class=gthread --log-file=- --chdir /app/ --worker-tmp-dir /dev/shm --bind 0.0.0.0:5000"

# Run the application:
COPY server.py .
CMD ["gunicorn", "server:app"]
