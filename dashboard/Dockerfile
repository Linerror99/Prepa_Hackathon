# Dockerfile pour Dashboard Streamlit
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV BACKEND_URL=http://backend:8000

# Exposer le port
EXPOSE 8501

# Créer le dossier de configuration Streamlit
RUN mkdir -p /app/.streamlit

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande de démarrage
CMD ["streamlit", "run", "app_live.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--global.suppressDeprecationWarnings=true"]
