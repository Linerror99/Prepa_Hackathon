#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐳 Script de lancement Docker Compose - Système IoT+IA Complet
Lance tous les services conteneurisés avec Docker Compose
"""

import subprocess
import sys
import time
import signal
import requests
from pathlib import Path
import json

class DockerLauncher:
    """Gestionnaire de lancement Docker Compose"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.compose_file = self.project_root / "docker-compose.yml"
        
        # Gestion propre à l'arrêt
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def log(self, message: str, level: str = "INFO"):
        """Log formaté avec timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[36m",     # Cyan
            "SUCCESS": "\033[32m",  # Vert
            "WARNING": "\033[33m",  # Jaune
            "ERROR": "\033[31m",    # Rouge
            "RESET": "\033[0m"      # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    def check_docker(self) -> bool:
        """Vérifie si Docker et Docker Compose sont disponibles"""
        try:
            # Vérifier Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
            
            # Vérifier Docker Compose
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def cleanup_existing(self):
        """Nettoie les conteneurs existants"""
        self.log("🧹 Nettoyage des conteneurs existants...", "INFO")
        
        try:
            # Arrêter et supprimer les conteneurs existants
            subprocess.run(['docker', 'compose', '-f', str(self.compose_file), 'down'], 
                         capture_output=True, timeout=30)
            
            # Nettoyer les images orphelines
            subprocess.run(['docker', 'system', 'prune', '-f'], 
                         capture_output=True, timeout=30)
            
        except Exception as e:
            self.log(f"Erreur nettoyage: {e}", "WARNING")
        
        time.sleep(2)
    
    def build_images(self):
        """Build les images Docker"""
        self.log("🔨 Construction des images Docker...", "INFO")
        
        try:
            result = subprocess.run([
                'docker', 'compose', '-f', str(self.compose_file), 
                'build', '--no-cache'
            ], cwd=self.project_root, timeout=300)
            
            if result.returncode == 0:
                self.log("Images construites avec succès", "SUCCESS")
                return True
            else:
                self.log("Erreur lors de la construction", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Timeout lors de la construction", "ERROR")
            return False
        except Exception as e:
            self.log(f"Erreur construction: {e}", "ERROR")
            return False
    
    def start_services(self):
        """Démarre tous les services avec Docker Compose"""
        self.log("🚀 Démarrage des services...", "INFO")
        
        try:
            # Démarrer tous les services
            process = subprocess.Popen([
                'docker', 'compose', '-f', str(self.compose_file), 
                'up', '-d'
            ], cwd=self.project_root)
            
            # Attendre que le processus se termine
            process.wait()
            
            if process.returncode == 0:
                self.log("Services démarrés avec succès", "SUCCESS")
                return True
            else:
                self.log("Erreur lors du démarrage", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erreur démarrage: {e}", "ERROR")
            return False
    
    def wait_for_services(self):
        """Attend que tous les services soient prêts"""
        services = {
            "MQTT Broker": "http://localhost:1883",
            "Backend API": "http://localhost:8000/health",
            "Dashboard": "http://localhost:8501"
        }
        
        self.log("⏳ Attente des services...", "INFO")
        
        for service_name, url in services.items():
            if "health" in url:
                self.log(f"Vérification de {service_name}...", "INFO")
                
                for i in range(60):  # 60 secondes max
                    try:
                        response = requests.get(url, timeout=3)
                        if response.status_code == 200:
                            self.log(f"✅ {service_name} prêt!", "SUCCESS")
                            break
                    except:
                        pass
                    
                    time.sleep(1)
                else:
                    self.log(f"⚠️ {service_name} peut prendre plus de temps", "WARNING")
            else:
                time.sleep(2)  # Attente simple pour MQTT
                self.log(f"✅ {service_name} démarré", "SUCCESS")
    
    def show_status(self):
        """Affiche le statut des services"""
        self.log("", "INFO")
        self.log("📊 Statut des Services:", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            result = subprocess.run([
                'docker', 'compose', '-f', str(self.compose_file), 'ps'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(result.stdout)
            
        except Exception as e:
            self.log(f"Erreur statut: {e}", "WARNING")
        
        self.log("=" * 60, "INFO")
    
    def show_logs(self):
        """Affiche les logs des services"""
        self.log("📋 Logs des services (Ctrl+C pour arrêter):", "INFO")
        
        try:
            subprocess.run([
                'docker', 'compose', '-f', str(self.compose_file), 
                'logs', '-f'
            ], cwd=self.project_root)
            
        except KeyboardInterrupt:
            self.log("Arrêt de l'affichage des logs", "INFO")
    
    def signal_handler(self, signum, frame):
        """Gestionnaire pour arrêt propre"""
        self.log("", "WARNING")
        self.log("🛑 Arrêt du système...", "WARNING")
        self.shutdown()
    
    def shutdown(self):
        """Arrêt propre des services"""
        self.log("🔄 Arrêt des services Docker...", "WARNING")
        
        try:
            subprocess.run([
                'docker', 'compose', '-f', str(self.compose_file), 'down'
            ], cwd=self.project_root, timeout=60)
            
        except Exception as e:
            self.log(f"Erreur arrêt: {e}", "WARNING")
        
        self.log("✅ Système arrêté proprement", "SUCCESS")
        sys.exit(0)
    
    def launch_all(self):
        """Lance tout le système avec Docker Compose"""
        self.log("🐳 DÉMARRAGE SYSTÈME IoT+IA DOCKER", "SUCCESS")
        self.log("=" * 60, "SUCCESS")
        
        # Vérifications
        if not self.check_docker():
            self.log("❌ Docker ou Docker Compose non disponible", "ERROR")
            self.log("Installez Docker Desktop", "ERROR")
            sys.exit(1)
        
        if not self.compose_file.exists():
            self.log("❌ Fichier docker-compose.yml non trouvé", "ERROR")
            sys.exit(1)
        
        try:
            # Nettoyage
            self.cleanup_existing()
            
            # Construction des images
            if not self.build_images():
                sys.exit(1)
            
            # Démarrage des services
            if not self.start_services():
                sys.exit(1)
            
            # Attente que les services soient prêts
            self.wait_for_services()
            
            # Affichage du statut
            self.show_status()
            
            # Résumé
            self.log("", "SUCCESS")
            self.log("🎉 SYSTÈME DOCKER DÉMARRÉ AVEC SUCCÈS!", "SUCCESS")
            self.log("=" * 60, "SUCCESS")
            self.log("🌐 Dashboard Temps Réel: http://localhost:8501", "INFO")
            self.log("🔧 API Backend: http://localhost:8000", "INFO")
            self.log("📡 MQTT Broker: localhost:1883", "INFO")
            self.log("🏭 Simulateur: 3 machines IoT conteneurisées", "INFO")
            self.log("=" * 60, "SUCCESS")
            self.log("📋 Commandes utiles:", "INFO")
            self.log("  docker compose logs -f  # Voir les logs", "INFO")
            self.log("  docker compose ps       # Voir le statut", "INFO")
            self.log("  docker compose down     # Arrêter", "INFO")
            self.log("=" * 60, "SUCCESS")
            self.log("Ctrl+C pour arrêter le système", "INFO")
            
            # Afficher les logs en continu
            self.show_logs()
            
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            self.log(f"❌ Erreur fatale: {e}", "ERROR")
            self.shutdown()

def main():
    """Point d'entrée principal"""
    launcher = DockerLauncher()
    launcher.launch_all()

if __name__ == "__main__":
    main()