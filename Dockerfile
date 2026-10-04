FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080

WORKDIR /app

COPY requirements.txt requirements.production.txt ./
RUN pip install --no-cache-dir -r requirements.production.txt

COPY . .
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

CMD ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120"]
