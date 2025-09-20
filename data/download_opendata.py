#!/usr/bin/env python3
"""
Script pour télécharger et préparer les Open Data industriels pour le hackathon IoT
Dataset principal : AI4I 2020 Predictive Maintenance Dataset (UCI)
"""

import os
import requests
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Tuple
import zipfile
import io

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenDataDownloader:
    """Classe pour télécharger et préparer les données industrielles"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Créer les dossiers si nécessaire
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def download_ai4i_dataset(self) -> str:
        """
        Télécharge le dataset AI4I 2020 Predictive Maintenance depuis UCI
        
        Returns:
            str: Chemin vers le fichier téléchargé
        """
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"
        filename = self.raw_dir / "ai4i2020.csv"
        
        logger.info(f"Téléchargement du dataset AI4I depuis {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Dataset AI4I téléchargé avec succès : {filename}")
            return str(filename)
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors du téléchargement : {e}")
            # Si le téléchargement échoue, on crée un dataset de démonstration
            return self._create_demo_dataset()
    
    def _create_demo_dataset(self) -> str:
        """
        Crée un dataset de démonstration si le téléchargement échoue
        Basé sur la structure réelle du dataset AI4I
        """
        logger.info("Création d'un dataset de démonstration...")
        
        # Structure du vrai dataset AI4I
        np.random.seed(42)
        n_samples = 10000
        
        data = {
            'UDI': range(1, n_samples + 1),
            'Product ID': [f"M{i%5}{np.random.randint(10000, 99999)}" for i in range(n_samples)],
            'Type': np.random.choice(['L', 'M', 'H'], n_samples, p=[0.6, 0.3, 0.1]),
            'Air temperature [K]': np.random.normal(300, 2, n_samples),
            'Process temperature [K]': np.random.normal(310, 1.5, n_samples),
            'Rotational speed [rpm]': np.random.normal(1500, 100, n_samples),
            'Torque [Nm]': np.random.normal(40, 10, n_samples),
            'Tool wear [min]': np.random.exponential(100, n_samples),
            'Machine failure': np.random.binomial(1, 0.034, n_samples),  # ~3.4% comme le vrai dataset
            'TWF': np.random.binomial(1, 0.009, n_samples),  # Tool Wear Failure
            'HDF': np.random.binomial(1, 0.012, n_samples),  # Heat Dissipation Failure
            'PWF': np.random.binomial(1, 0.004, n_samples),  # Power Failure
            'OSF': np.random.binomial(1, 0.006, n_samples),  # Overstrain Failure
            'RNF': np.random.binomial(1, 0.003, n_samples)   # Random Failure
        }
        
        # Ajuster les corrélations pour plus de réalisme
        df = pd.DataFrame(data)
        
        # Machine failure = OR de tous les types de pannes
        df['Machine failure'] = (df['TWF'] | df['HDF'] | df['PWF'] | df['OSF'] | df['RNF']).astype(int)
        
        filename = self.raw_dir / "ai4i2020_demo.csv"
        df.to_csv(filename, index=False)
        
        logger.info(f"Dataset de démonstration créé : {filename}")
        return str(filename)
    
    def analyze_dataset(self, filepath: str) -> Dict:
        """
        Analyse les patterns dans le dataset
        
        Args:
            filepath: Chemin vers le fichier CSV
            
        Returns:
            Dict: Statistiques et patterns découverts
        """
        logger.info(f"Analyse du dataset : {filepath}")
        
        df = pd.read_csv(filepath)
        
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'failure_rate': df['Machine failure'].mean(),
            'failure_types': {
                'TWF': df['TWF'].sum(),
                'HDF': df['HDF'].sum(), 
                'PWF': df['PWF'].sum(),
                'OSF': df['OSF'].sum(),
                'RNF': df['RNF'].sum()
            },
            'statistics': df.describe().to_dict()
        }
        
        logger.info(f"Analyse terminée :")
        logger.info(f"  - {analysis['shape'][0]} échantillons, {analysis['shape'][1]} variables")
        logger.info(f"  - Taux de panne global : {analysis['failure_rate']:.3f}")
        logger.info(f"  - Types de pannes : {analysis['failure_types']}")
        
        return analysis
    
    def create_failure_scenarios(self, filepath: str) -> pd.DataFrame:
        """
        Extrait les scénarios de panne réels du dataset
        
        Args:
            filepath: Chemin vers le fichier CSV
            
        Returns:
            pd.DataFrame: Scénarios de pannes avec contexte
        """
        logger.info("Extraction des scénarios de panne...")
        
        df = pd.read_csv(filepath)
        
        # Sélectionner uniquement les cas de panne
        failures = df[df['Machine failure'] == 1].copy()
        
        # Ajouter des métadonnées pour les scénarios
        scenarios = []
        
        for _, row in failures.iterrows():
            scenario = {
                'scenario_id': len(scenarios) + 1,
                'product_type': row['Type'],
                'air_temp': row['Air temperature [K]'],
                'process_temp': row['Process temperature [K]'],
                'rotational_speed': row['Rotational speed [rpm]'],
                'torque': row['Torque [Nm]'],
                'tool_wear': row['Tool wear [min]'],
                'failure_type': self._get_primary_failure_type(row),
                'severity': self._calculate_severity(row),
                'description': self._generate_scenario_description(row)
            }
            scenarios.append(scenario)
        
        scenarios_df = pd.DataFrame(scenarios)
        
        # Sauvegarder les scénarios
        output_file = self.processed_dir / "failure_scenarios.csv"
        scenarios_df.to_csv(output_file, index=False)
        
        logger.info(f"{len(scenarios)} scénarios de panne extraits et sauvegardés dans {output_file}")
        
        return scenarios_df
    
    def _get_primary_failure_type(self, row) -> str:
        """Détermine le type de panne principal"""
        failure_types = ['TWF', 'HDF', 'PWF', 'OSF', 'RNF']
        for failure_type in failure_types:
            if row[failure_type] == 1:
                return failure_type
        return 'Unknown'
    
    def _calculate_severity(self, row) -> str:
        """Calcule la sévérité de la panne"""
        score = 0
        
        # Température élevée
        if row['Air temperature [K]'] > 305:
            score += 1
        if row['Process temperature [K]'] > 315:
            score += 1
            
        # Vitesse anormale
        if row['Rotational speed [rpm]'] < 1200 or row['Rotational speed [rpm]'] > 1800:
            score += 1
            
        # Couple élevé
        if row['Torque [Nm]'] > 50:
            score += 1
            
        # Usure importante
        if row['Tool wear [min]'] > 200:
            score += 2
        
        if score >= 4:
            return 'Critical'
        elif score >= 2:
            return 'High'
        else:
            return 'Medium'
    
    def _generate_scenario_description(self, row) -> str:
        """Génère une description textuelle du scénario"""
        failure_type = self._get_primary_failure_type(row)
        
        descriptions = {
            'TWF': f"Usure d'outil excessive ({row['Tool wear [min]']:.0f} min)",
            'HDF': f"Défaillance de dissipation thermique (T_air: {row['Air temperature [K]']:.1f}K)",
            'PWF': f"Défaillance de puissance (Couple: {row['Torque [Nm]']:.1f} Nm, Vitesse: {row['Rotational speed [rpm]']:.0f} rpm)",
            'OSF': f"Défaillance de contrainte excessive (Couple: {row['Torque [Nm]']:.1f} Nm)",
            'RNF': "Défaillance aléatoire"
        }
        
        return descriptions.get(failure_type, "Défaillance inconnue")


def main():
    """Fonction principale"""
    print("🚀 Téléchargement et analyse des Open Data industriels")
    print("=" * 60)
    
    # Initialiser le téléchargeur
    downloader = OpenDataDownloader()
    
    # Télécharger le dataset principal
    dataset_path = downloader.download_ai4i_dataset()
    
    # Analyser le dataset
    analysis = downloader.analyze_dataset(dataset_path)
    
    # Créer les scénarios de panne
    scenarios = downloader.create_failure_scenarios(dataset_path)
    
    print("\n✅ Données téléchargées et analysées avec succès !")
    print(f"📊 Dataset : {dataset_path}")
    print(f"📈 {analysis['shape'][0]} échantillons analysés")
    print(f"🔥 {len(scenarios)} scénarios de panne extraits")
    print("\nProchaine étape : Exécuter le notebook d'analyse des données")


if __name__ == "__main__":
    main()