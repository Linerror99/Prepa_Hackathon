"""
Persistance SQLite pour les données IoT
Stockage des lectures, alertes et historique
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Chemin de la base de données - Docker/Local compatible
DATABASE_PATH = os.getenv('DATABASE_PATH', '/app/data/readings.db')

# Si le chemin n'est pas absolu, utiliser le dossier local
if not os.path.isabs(DATABASE_PATH):
    DB_PATH = Path(__file__).resolve().parent / "data" / "readings.db"
else:
    DB_PATH = Path(DATABASE_PATH)

# Créer le dossier si nécessaire
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db() -> None:
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Table des lectures capteurs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        machine_id TEXT NOT NULL,
        air_temperature REAL,
        process_temperature REAL,
        rotational_speed REAL,
        torque REAL,
        tool_wear REAL,
        product_type TEXT,
        status TEXT,
        failure_prob REAL,
        failure_type TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Table des alertes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        machine_id TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT,
        acknowledged BOOLEAN DEFAULT 0,
        acknowledged_by TEXT,
        acknowledged_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Table des machines
    cur.execute("""
    CREATE TABLE IF NOT EXISTS machines (
        machine_id TEXT PRIMARY KEY,
        label TEXT,
        location TEXT,
        install_date TEXT,
        last_seen TEXT,
        status TEXT DEFAULT 'unknown',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Index pour les performances
    cur.execute("CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_readings_machine ON readings(machine_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_machine ON alerts(machine_id);")
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Base de données SQLite initialisée: {DB_PATH}")

def save_reading(reading: Dict) -> None:
    """Sauvegarde une lecture de capteur"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO readings (
            timestamp, machine_id, air_temperature, process_temperature,
            rotational_speed, torque, tool_wear, product_type, status,
            failure_prob, failure_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reading.get("timestamp"),
            reading.get("machine_id"),
            reading.get("air_temperature"),
            reading.get("process_temperature"),
            reading.get("rotational_speed"),
            reading.get("torque"),
            reading.get("tool_wear"),
            reading.get("product_type"),
            reading.get("status"),
            reading.get("predicted_failure_probability"),
            reading.get("failure_type")
        ))
        
        # Mettre à jour le statut de la machine
        cur.execute("""
        INSERT OR REPLACE INTO machines (machine_id, last_seen, status)
        VALUES (?, ?, ?)
        """, (
            reading.get("machine_id"),
            reading.get("timestamp"),
            reading.get("status", "unknown")
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde lecture: {e}")

def save_alert(alert: Dict) -> None:
    """Sauvegarde une alerte"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO alerts (
            timestamp, machine_id, alert_type, severity, message
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            alert.get("timestamp"),
            alert.get("machine_id"),
            alert.get("alert_type"),
            alert.get("severity"),
            alert.get("message")
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🚨 Alerte sauvegardée: {alert.get('machine_id')} - {alert.get('alert_type')}")
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde alerte: {e}")

def get_recent_readings(machine_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Récupère les lectures récentes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        if machine_id:
            cur.execute("""
            SELECT * FROM readings 
            WHERE machine_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (machine_id, limit))
        else:
            cur.execute("""
            SELECT * FROM readings 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (limit,))
        
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        conn.close()
        
        # Convertir en liste de dictionnaires
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture données: {e}")
        return []

def get_active_alerts(machine_id: Optional[str] = None) -> List[Dict]:
    """Récupère les alertes non acquittées"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        if machine_id:
            cur.execute("""
            SELECT * FROM alerts 
            WHERE machine_id = ? AND acknowledged = 0
            ORDER BY timestamp DESC
            """, (machine_id,))
        else:
            cur.execute("""
            SELECT * FROM alerts 
            WHERE acknowledged = 0
            ORDER BY timestamp DESC
            """)
        
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture alertes: {e}")
        return []

def get_machines_status() -> List[Dict]:
    """Récupère le statut de toutes les machines"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
        SELECT m.*, 
               COUNT(r.id) as readings_count,
               COUNT(a.id) as alerts_count
        FROM machines m
        LEFT JOIN readings r ON m.machine_id = r.machine_id 
            AND r.timestamp > datetime('now', '-1 hour')
        LEFT JOIN alerts a ON m.machine_id = a.machine_id 
            AND a.acknowledged = 0
        GROUP BY m.machine_id
        ORDER BY m.last_seen DESC
        """)
        
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture machines: {e}")
        return []

def get_stats() -> Dict:
    """Récupère les statistiques générales"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Statistiques générales
        cur.execute("SELECT COUNT(*) FROM readings")
        total_readings = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
        active_alerts = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT machine_id) FROM machines")
        total_machines = cur.fetchone()[0]
        
        # Lectures récentes (dernière heure)
        cur.execute("""
        SELECT COUNT(*) FROM readings 
        WHERE timestamp > datetime('now', '-1 hour')
        """)
        recent_readings = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_readings": total_readings,
            "active_alerts": active_alerts,
            "total_machines": total_machines,
            "recent_readings": recent_readings,
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture stats: {e}")
        return {}

def acknowledge_alert(alert_id: int, acknowledged_by: str) -> bool:
    """Acquitte une alerte"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
        UPDATE alerts 
        SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
        WHERE id = ?
        """, (acknowledged_by, datetime.now().isoformat(), alert_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Alerte {alert_id} acquittée par {acknowledged_by}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur acquittement alerte: {e}")
        return False

def cleanup_old_data(days: int = 30) -> None:
    """Nettoie les anciennes données"""
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Supprimer les anciennes lectures
        cur.execute("DELETE FROM readings WHERE timestamp < ?", (cutoff_date,))
        readings_deleted = cur.rowcount
        
        # Supprimer les anciennes alertes acquittées
        cur.execute("""
        DELETE FROM alerts 
        WHERE acknowledged = 1 AND acknowledged_at < ?
        """, (cutoff_date,))
        alerts_deleted = cur.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Nettoyage: {readings_deleted} lectures, {alerts_deleted} alertes supprimées")
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage: {e}")

# Fonction utilitaire pour les tests
def get_db_info() -> Dict:
    """Informations sur la base de données"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Taille du fichier
        db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        
        # Nombre de tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        conn.close()
        
        return {
            "db_path": str(DB_PATH),
            "db_size_bytes": db_size,
            "db_size_mb": round(db_size / 1024 / 1024, 2),
            "tables": tables,
            "exists": DB_PATH.exists()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur info DB: {e}")
        return {}

if __name__ == "__main__":
    # Test de la base de données
    print("🗄️ Test de la base de données SQLite")
    
    init_db()
    
    # Test d'insertion
    test_reading = {
        "timestamp": datetime.now().isoformat(),
        "machine_id": "TEST_01",
        "air_temperature": 305.2,
        "process_temperature": 318.7,
        "rotational_speed": 1420,
        "torque": 55.3,
        "tool_wear": 180,
        "product_type": "M",
        "status": "warning",
        "predicted_failure_probability": 0.75,
        "failure_type": "TWF"
    }
    
    save_reading(test_reading)
    
    # Vérifier
    recent = get_recent_readings(limit=5)
    print(f"✅ {len(recent)} lectures récentes trouvées")
    
    stats = get_stats()
    print(f"📊 Stats: {stats}")
    
    info = get_db_info()
    print(f"ℹ️ Info DB: {info}")