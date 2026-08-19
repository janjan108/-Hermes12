FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir git+https://github.com/NousResearch/hermes-agent.git

COPY start.sh .
RUN chmod +x start.sh

ENV PYTHONUNBUFFERED=1

CMD ["./start.sh"]
