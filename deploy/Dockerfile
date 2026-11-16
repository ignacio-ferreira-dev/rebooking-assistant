# Service image for ECS Fargate (or any container platform). Build from the repo root:
#   docker build -f deploy/Dockerfile -t rebooking-assistant:local .
# The root Dockerfile stays as the exercise's dev image used by `docker compose run --rm check`.
FROM python:3.12.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -q -r requirements.txt

# Only what the service needs: no tests, no exercise checks, no local tooling.
COPY assistant/ assistant/
COPY service.py .

# Never run as root inside the task.
RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=2)"

# exec form: python is PID 1 and receives SIGTERM from `docker stop` / ECS directly.
CMD ["python", "service.py"]
