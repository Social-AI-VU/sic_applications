FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        procps \
        gcc \
        python3-dev \
        portaudio19-dev \
        libturbojpeg0 \
    && rm -rf /var/lib/apt/lists/*

COPY social-interaction-cloud /tmp/social-interaction-cloud
RUN pip install --no-cache-dir "/tmp/social-interaction-cloud[openai-gpt]" \
    && rm -rf /tmp/social-interaction-cloud

WORKDIR /app

CMD ["run-gpt"]
