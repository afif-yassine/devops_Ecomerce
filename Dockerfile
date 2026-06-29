# syntax=docker/dockerfile:1
# Image de base slim pour reduire la taille et la surface d'attaque.
FROM python:3.11-slim

# Empeche Python de bufferiser stdout/stderr et d'ecrire des .pyc.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1) Copier et installer les dependances AVANT le code source.
#    -> maximise la reutilisation du cache de couches Docker :
#       le code change souvent, les dependances rarement.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Copier le code source (couche invalidee uniquement quand src/ change).
COPY src/ ./src/

EXPOSE 8000

# Demarrage de l'API avec Uvicorn.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
