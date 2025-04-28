# Utilisation d'une image Python comme base
FROM python:3.12.7

# Définition du répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .

# Mettre à jour libstdc++ pour éviter l'erreur avec bitsandbytes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libstdc++6 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation des dépendances
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le contenu du backend
COPY . .

# Exposer le port utilisé par l'application
EXPOSE 8000

# Lancer l'application avec Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
