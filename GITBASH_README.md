# 🐳 Lancement Docker avec Git Bash

## 🎯 Scripts disponibles pour Git Bash

### ✅ **Script Principal** : `start_docker.sh`
```bash
./start_docker.sh
```
Lance tout le système IoT+IA avec Docker Compose.

### 🧪 **Script de Test** : `test_docker.sh`  
```bash
./test_docker.sh
```
Vérifie que Docker est bien configuré avant le lancement.

## 🚀 **Démarrage Rapide**

1. **Ouvrir Git Bash** dans le dossier du projet

2. **Tester la configuration** :
   ```bash
   ./test_docker.sh
   ```

3. **Lancer le système** :
   ```bash
   ./start_docker.sh
   ```

4. **Accéder au dashboard** : http://localhost:8501

## 🔧 **Commandes Utiles Git Bash**

### Vérifier le statut
```bash
docker compose ps
```

### Voir les logs
```bash
docker compose logs -f
```

### Arrêter proprement
```bash
# Ctrl+C dans le terminal du script
# OU
docker compose down
```

### Reconstruction complète
```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

## 🐛 **Dépannage Git Bash**

### Problème de permissions
```bash
chmod +x start_docker.sh
chmod +x test_docker.sh
```

### Docker non disponible
1. Vérifier que Docker Desktop est démarré
2. Redémarrer Git Bash
3. Vérifier PATH avec `echo $PATH`

### Ports occupés
```bash
# Voir les ports utilisés
netstat -an | grep ":8000\|:8501\|:1883"

# Libérer les ports
docker compose down
```

### Problème de fin de ligne (CRLF/LF)
```bash
# Convertir si nécessaire
dos2unix start_docker.sh
dos2unix test_docker.sh
```

## 📁 **Structure des Scripts**

```
.
├── start_docker.sh     # 🚀 Script principal de lancement
├── test_docker.sh      # 🧪 Script de vérification
├── start_docker.py     # 🐍 Version Python (alternative)
├── start_docker.bat    # 💻 Version Windows CMD
└── docker-compose.yml  # 🐳 Configuration Docker
```

## 🎨 **Fonctionnalités du Script Shell**

- ✅ **Couleurs** : Logs colorés pour meilleure lisibilité
- ✅ **Vérifications** : Docker, Compose, fichiers
- ✅ **Health Checks** : Attente services prêts
- ✅ **Arrêt Propre** : Cleanup avec Ctrl+C
- ✅ **Logs Temps Réel** : Suivi des services
- ✅ **Gestion Erreurs** : Messages clairs

## 🏁 **Résultat Attendu**

```
🐳 DÉMARRAGE SYSTÈME IoT+IA DOCKER
============================================================
[INFO] 🔍 Vérification de Docker...
[SUCCESS] ✅ Docker et Docker Compose disponibles
[INFO] 🧹 Nettoyage des conteneurs existants...
[INFO] 🔨 Construction des images Docker...
[SUCCESS] ✅ Images construites avec succès
[INFO] 🚀 Démarrage des services...
[SUCCESS] ✅ Services démarrés avec succès
[SUCCESS] ✅ Backend API prêt!
[SUCCESS] ✅ Dashboard prêt!

🎉 SYSTÈME DOCKER DÉMARRÉ AVEC SUCCÈS!
============================================================
🌐 Dashboard Temps Réel: http://localhost:8501
🔧 API Backend: http://localhost:8000
📡 MQTT Broker: localhost:1883
🏭 Simulateur: 3 machines IoT conteneurisées
============================================================
```

---

## 🎯 **Une Seule Commande**

```bash
./start_docker.sh
```

**Et votre système IoT+IA complet est opérationnel !** 🚀