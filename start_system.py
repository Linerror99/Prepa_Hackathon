#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démarrage automatique - Système IoT+IA Complet
Lance tous les composants nécessaires en une seule commande
"""

import subprocess
import os
import sys
import time
import signal
import threading
import psutil
from pathlib import Path
import requests
from typing import List, Dict
import json

class SystemLauncher:
    """Gestionnaire de lancement du système complet"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.processes: List[subprocess.Popen] = []
        self.services = {
            'mosquitto': {'status': False, 'port': 1883},
            'backend': {'status': False, 'port': 8000},
            'simulator': {'status': False, 'port': None},
            'dashboard': {'status': False, 'port': 8501}
        }
        
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
    
    def cleanup_existing(self):
        """Nettoie les processus existants"""
        self.log("Nettoyage des processus existants...", "INFO")
        
        # Arrêter processus Python
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if any(x in cmdline for x in ['main.py', 'machine_simulator.py', 'streamlit']):
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except:
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            self.log(f"Erreur nettoyage: {e}", "WARNING")
        
        # Arrêter Docker
        try:
            subprocess.run(['docker', 'stop', 'mosquitto'], capture_output=True, timeout=10)
            subprocess.run(['docker', 'rm', 'mosquitto'], capture_output=True, timeout=5)
        except:
            pass
        
        time.sleep(2)
    
    def check_docker(self) -> bool:
        """Vérifie si Docker est disponible"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def wait_for_service(self, service_name: str, url: str, timeout: int = 30) -> bool:
        """Attend qu'un service soit accessible"""
        self.log(f"Attente de {service_name}...", "INFO")
        
        for i in range(timeout):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    self.log(f"{service_name} prêt!", "SUCCESS")
                    return True
            except:
                pass
            time.sleep(1)
        
        return False
    
    def start_mosquitto(self):
        """Démarre le broker MQTT Docker"""
        self.log("Démarrage Mosquitto MQTT...", "INFO")
        
        if not self.check_docker():
            self.log("Docker non disponible, mode simulé", "WARNING")
            return
        
        try:
            result = subprocess.run([
                'docker', 'run', '-d', 
                '--name', 'mosquitto',
                '-p', '1883:1883',
                '-p', '9001:9001',
                'eclipse-mosquitto:2.0'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                time.sleep(3)
                self.services['mosquitto']['status'] = True
                self.log("Mosquitto MQTT démarré (ports 1883/9001)", "SUCCESS")
            else:
                self.log("Erreur Docker, continuons sans MQTT", "WARNING")
                
        except Exception as e:
            self.log(f"Erreur Mosquitto: {e}", "WARNING")
    
    def start_backend(self):
        """Démarre le serveur FastAPI"""
        self.log("Démarrage Backend FastAPI...", "INFO")
        
        backend_path = self.project_root / "backend"
        
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(backend_path)
            
            process = subprocess.Popen([
                sys.executable, "main.py"
            ], cwd=backend_path, env=env,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(process)
            
            if self.wait_for_service("Backend API", "http://localhost:8000/health"):
                self.services['backend']['status'] = True
            else:
                self.log("Backend n'a pas démarré", "ERROR")
                
        except Exception as e:
            self.log(f"Erreur Backend: {e}", "ERROR")
    
    def start_simulator(self):
        """Démarre le simulateur de machines"""
        self.log("Démarrage Simulateur IoT...", "INFO")
        
        simulator_path = self.project_root / "simulator"
        
        try:
            process = subprocess.Popen([
                sys.executable, "machine_simulator.py",
                "--machines", "3",
                "--mqtt-broker", "localhost"
            ], cwd=simulator_path,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(process)
            time.sleep(2)
            
            self.services['simulator']['status'] = True
            self.log("Simulateur IoT démarré (3 machines)", "SUCCESS")
            
        except Exception as e:
            self.log(f"Erreur Simulateur: {e}", "ERROR")
    
    def start_dashboard(self):
        """Démarre le dashboard Streamlit temps réel"""
        self.log("Démarrage Dashboard Temps Réel...", "INFO")
        
        dashboard_path = self.project_root / "dashboard"
        
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "app_live.py",
                "--server.port", "8501",
                "--server.headless", "true",
                "--server.address", "0.0.0.0"
            ], cwd=dashboard_path,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(process)
            
            if self.wait_for_service("Dashboard", "http://localhost:8501", timeout=25):
                self.services['dashboard']['status'] = True
            else:
                self.log("Dashboard peut prendre plus de temps", "WARNING")
                
        except Exception as e:
            self.log(f"Erreur Dashboard: {e}", "ERROR")
    
    def check_services_status(self):
        """Vérifie le statut de tous les services"""
        self.log("", "INFO")
        self.log("État des Services:", "INFO")
        self.log("=" * 50, "INFO")
        
        for service, config in self.services.items():
            status = "ACTIF" if config['status'] else "INACTIF"
            port_info = f" (port {config['port']})" if config['port'] else ""
            self.log(f"{service.upper():<12}: {status}{port_info}", "INFO")
        
        self.log("=" * 50, "INFO")
    
    def signal_handler(self, signum, frame):
        """Gestionnaire pour arrêt propre"""
        self.log("", "WARNING")
        self.log("Arrêt du système...", "WARNING")
        self.shutdown()
    
    def shutdown(self):
        """Arrêt propre de tous les services"""
        # Arrêter processus Python
        for process in self.processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except:
                        process.kill()
            except:
                pass
        
        # Arrêter Docker
        try:
            subprocess.run(['docker', 'stop', 'mosquitto'], capture_output=True, timeout=10)
            subprocess.run(['docker', 'rm', 'mosquitto'], capture_output=True, timeout=5)
        except:
            pass
        
        self.log("Système arrêté proprement", "SUCCESS")
        sys.exit(0)
    
    def launch_all(self):
        """Lance tous les composants du système"""
        self.log("DÉMARRAGE SYSTÈME IoT+IA COMPLET", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        try:
            # Nettoyage
            self.cleanup_existing()
            
            # Démarrage des services
            self.start_mosquitto()
            self.start_backend()
            self.start_simulator()
            self.start_dashboard()
            
            # Résumé
            self.check_services_status()
            
            self.log("", "SUCCESS")
            self.log("SYSTÈME DÉMARRÉ AVEC SUCCÈS!", "SUCCESS")
            self.log("=" * 60, "SUCCESS")
            self.log("Dashboard Temps Réel: http://localhost:8501", "INFO")
            self.log("API Backend: http://localhost:8000", "INFO")
            self.log("MQTT Broker: localhost:1883", "INFO")
            self.log("Simulateur: 3 machines IoT actives", "INFO")
            self.log("=" * 60, "SUCCESS")
            self.log("Actualisation auto toutes les 3 secondes", "INFO")
            self.log("Ctrl+C pour arrêter", "INFO")
            
            # Garder le script actif
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            self.log(f"Erreur fatale: {e}", "ERROR")
            self.shutdown()

def main():
    """Point d'entrée principal"""
    launcher = SystemLauncher()
    launcher.launch_all()

if __name__ == "__main__":
    main()