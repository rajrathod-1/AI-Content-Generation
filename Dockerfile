FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf \
    FLASK_ENV=production \
    PORT=8080

WORKDIR /app

COPY requirements.production.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.production.txt

# Bake the embedding model into the image so cold starts don't download it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .
RUN useradd --create-home appuser && chown -R appuser /app /opt/hf
USER appuser

CMD ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120"]
