"""
Database models, SQLite initialization, and sample seed data for the Mall RCM System.
"""
import sqlite3
import hashlib
import json
from datetime import datetime, date, timedelta
from pathlib import Path

DB_PATH = Path("mall_rcm.db")

def hash_password(password: str) -> str:
    """Return SHA-256 hashed password with a fixed salt."""
    salt = "mall_rcm_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def get_connection():
    """Get SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Create all required tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Manager', 'Engineer', 'Technician', 'Tenant')),
        department TEXT DEFAULT 'Facility Operations',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        zone_type TEXT NOT NULL,
        floor_level TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        location_id INTEGER,
        status TEXT NOT NULL CHECK(status IN ('Operational', 'Degraded', 'Under Maintenance', 'Out of Service')),
        manufacturer TEXT,
        model TEXT,
        serial_number TEXT,
        install_date DATE,
        criticality TEXT NOT NULL CHECK(criticality IN ('Critical (Tier 1)', 'High (Tier 2)', 'Medium (Tier 3)', 'Low (Tier 4)')),
        safety_impact INTEGER DEFAULT 3,
        operational_impact INTEGER DEFAULT 3,
        tenant_impact INTEGER DEFAULT 3,
        cost_impact INTEGER DEFAULT 3,
        rcm_strategy TEXT DEFAULT 'Preventive (Time-based)',
        expected_lifespan_years INTEGER DEFAULT 15,
        FOREIGN KEY (location_id) REFERENCES locations(id)
    );

    CREATE TABLE IF NOT EXISTS fmea_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        failure_mode TEXT NOT NULL,
        failure_cause TEXT NOT NULL,
        failure_effect TEXT NOT NULL,
        severity INTEGER NOT NULL,
        occurrence INTEGER NOT NULL,
        detection INTEGER NOT NULL,
        rpn INTEGER NOT NULL,
        recommended_action TEXT,
        maintenance_strategy TEXT,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wo_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        asset_id INTEGER NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('Critical / Emergency', 'High', 'Medium', 'Low')),
        status TEXT NOT NULL CHECK(status IN ('New / Reported', 'Under Review', 'Assigned', 'In Progress', 'Pending Parts', 'Completed', 'Cancelled')),
        assigned_to INTEGER,
        reported_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        completed_at TIMESTAMP,
        labor_hours REAL DEFAULT 0.0,
        parts_cost REAL DEFAULT 0.0,
        labor_cost REAL DEFAULT 0.0,
        downtime_minutes INTEGER DEFAULT 0,
        resolution_summary TEXT,
        FOREIGN KEY (asset_id) REFERENCES assets(id),
        FOREIGN KEY (assigned_to) REFERENCES users(id),
        FOREIGN KEY (reported_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS preventive_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        asset_id INTEGER NOT NULL,
        frequency TEXT NOT NULL CHECK(frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual')),
        checklist_json TEXT NOT NULL,
        last_executed DATE,
        next_due DATE NOT NULL,
        assigned_role TEXT DEFAULT 'Technician',
        estimated_hours REAL DEFAULT 1.5,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Paused')),
        FOREIGN KEY (asset_id) REFERENCES assets(id)
    );
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    """Populate realistic sample data if the database is newly created."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed Default Users (Admin, Engineer, Technician, Tenant)
    users_data = [
        ('admin', hash_password('admin123'), 'Sarah Jenkins', 'sarah.j@grandmall.com', 'Manager', 'Mall Executive Management'),
        ('engineer1', hash_password('eng123'), 'Marcus Vance', 'marcus.v@grandmall.com', 'Engineer', 'Central Engineering & MEP'),
        ('tech1', hash_password('tech123'), 'David Chen', 'david.c@grandmall.com', 'Technician', 'HVAC & Refrigeration'),
        ('tech2', hash_password('tech123'), 'Amina Al-Mansoor', 'amina.m@grandmall.com', 'Technician', 'Vertical Transportation & Electrical'),
        ('tenant_zara', hash_password('tenant123'), 'Carlos Gomez (Zara Store)', 'manager@zara-mall.com', 'Tenant', 'Retail Tenant')
    ]
    cursor.executemany("""
        INSERT INTO users (username, password_hash, full_name, email, role, department)
        VALUES (?, ?, ?, ?, ?, ?)
    """, users_data)

    # Seed Mall Locations
    locations_data = [
        ('North Wing - Ground Floor', 'Retail Promenade', 'Ground Floor', 'Main luxury retail corridor'),
        ('Central Atrium', 'Public Space', 'Levels G-3', 'High-traffic open central court with skylight'),
        ('East Wing - Food Court', 'Dining & F&B', 'Level 2', 'Fast casual & restaurant zone with high exhaust load'),
        ('West Wing - Cineplex', 'Entertainment', 'Level 3', 'Cinema complexes and arcade zone'),
        ('Basement 1 - Parking & Loading Dock', 'Logistics / Utility', 'Basement 1', 'Main delivery bays and customer valet'),
        ('Rooftop Plant Room - MEP Station A', 'Plant Room', 'Rooftop', 'Heavy HVAC chillers and cooling towers'),
        ('South Plant Room - Substation', 'Plant Room', 'Basement 2', 'Main step-down transformers and standby generators')
    ]
    cursor.executemany("""
        INSERT INTO locations (name, zone_type, floor_level, description)
        VALUES (?, ?, ?, ?)
    """, locations_data)

    # Seed Mall Critical Assets
    assets_data = [
        ('HVAC-CHL-01', 'York Centrifugal Chiller 800TR #1', 'HVAC', 6, 'Operational', 'Johnson Controls', 'YK Centrifugal', 'SN-YK-99120', '2021-05-10', 'Critical (Tier 1)', 4, 5, 5, 5, 'Predictive (CBM)', 20),
        ('HVAC-CHL-02', 'York Centrifugal Chiller 800TR #2', 'HVAC', 6, 'Degraded', 'Johnson Controls', 'YK Centrifugal', 'SN-YK-99121', '2021-05-10', 'Critical (Tier 1)', 4, 5, 5, 5, 'Condition-based Monitoring', 20),
        ('ESC-AT-01', 'Central Atrium Escalator G-1 Up', 'Vertical Transport', 2, 'Operational', 'Schindler', 'Schindler 9300', 'SN-SCH-3310', '2022-01-15', 'Critical (Tier 1)', 5, 4, 5, 4, 'Preventive (Time-based)', 15),
        ('ESC-AT-02', 'Central Atrium Escalator G-1 Down', 'Vertical Transport', 2, 'Under Maintenance', 'Schindler', 'Schindler 9300', 'SN-SCH-3311', '2022-01-15', 'Critical (Tier 1)', 5, 4, 5, 4, 'Preventive (Time-based)', 15),
        ('ELEV-NW-01', 'North Wing Scenic Glass Elevator', 'Vertical Transport', 1, 'Operational', 'Otis', 'Otis SkyRise', 'SN-OTIS-8821', '2021-11-20', 'High (Tier 2)', 4, 3, 4, 3, 'Preventive (Time-based)', 20),
        ('GEN-EM-01', 'Cummins Standby Diesel Generator 1500kVA', 'Electrical & Power', 7, 'Operational', 'Cummins', 'QSK50-G4', 'SN-CUMM-4019', '2020-08-01', 'Critical (Tier 1)', 5, 5, 4, 5, 'Failure Finding & Periodic Run', 25),
        ('AHU-FC-01', 'Food Court Air Handling Unit #1', 'HVAC', 3, 'Operational', 'Carrier', '39M Air Handler', 'SN-CAR-5520', '2022-03-12', 'High (Tier 2)', 3, 4, 4, 3, 'Preventive (Time-based)', 15),
        ('PUMP-FP-01', 'Main Fire Suppression Jockey & Sprinkler Pump', 'Fire & Safety', 7, 'Operational', 'Armstrong', 'Series 4300', 'SN-ARM-1102', '2020-04-18', 'Critical (Tier 1)', 5, 5, 5, 4, 'Periodic Inspection & Testing', 20),
        ('PUMP-SEW-01', 'Basement Sewage Submersible Pump #1', 'Plumbing & Drainage', 5, 'Operational', 'Grundfos', 'SE1.80', 'SN-GRUN-9011', '2021-09-05', 'Medium (Tier 3)', 3, 3, 2, 2, 'Condition-based Monitoring', 12)
    ]
    cursor.executemany("""
        INSERT INTO assets (asset_tag, name, category, location_id, status, manufacturer, model, serial_number, install_date, criticality, safety_impact, operational_impact, tenant_impact, cost_impact, rcm_strategy, expected_lifespan_years)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, assets_data)

    # Seed FMEA Records (Reliability Centered Maintenance Analysis)
    # RPN = Severity * Occurrence * Detection
    fmea_data = [
        (1, 'Compressor Bearing High Vibration / Seizure', 'Lubrication breakdown / fatigue wear', 'Total loss of 50% central cooling, tenant store overheating', 9, 3, 3, 81, 'Implement bi-weekly ultrasonic vibration analysis & oil spectrometry', 'Predictive (CBM)'),
        (2, 'Condenser Tube Fouling / Scale Buildup', 'Cooling tower water mineral precipitation', 'Elevated head pressure, reduced chiller efficiency, energy surge', 7, 5, 3, 105, 'Monthly water chemistry sampling and bi-annual automated tube brushing', 'Condition-based Monitoring'),
        (3, 'Handrail Drive Slippage & Friction Heat', 'Drive wheel tire wear, improper tensioning', 'Handrail stops while steps move, risk of patron fall & injury', 9, 3, 2, 54, 'Monthly tension measurement & tactile alignment calibration', 'Preventive (Time-based)'),
        (4, 'Comb Plate Safety Switch Tripped', 'Debris lodged in comb tooth or step misalignment', 'Emergency escalator abrupt halt, crowd congestion in atrium', 8, 4, 2, 64, 'Daily pre-opening visual check and comb tooth clearance gauging', 'Preventive (Time-based)'),
        (6, 'Starting Battery Failure during Grid Outage', 'Battery electrolyte depletion or cell sulfation', 'Emergency standby generator fails to crank during blackout; loss of safety systems', 10, 2, 2, 40, 'Weekly automated battery conductance check and monthly simulated load test', 'Failure Finding'),
        (7, 'Belt Drive Snap on Food Court AHU', 'Mechanical fatigue, pulley misalignment', 'Airflow stoppage, smoke/odor buildup across dining area', 6, 4, 2, 48, 'Quarterly tension check and scheduled annual belt replacement before fatigue limit', 'Preventive (Time-based)')
    ]
    cursor.executemany("""
        INSERT INTO fmea_records (asset_id, failure_mode, failure_cause, failure_effect, severity, occurrence, detection, rpn, recommended_action, maintenance_strategy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fmea_data)

    # Seed Sample Work Orders
    today = date.today()
    work_orders_data = [
        ('WO-2026-001', 'High Bearing Vibration Alert on Chiller #2', 'Telemetry sensor indicated 4.2 mm/s vibration exceeding ISO threshold.', 2, 'High', 'In Progress', 3, 2, (today - timedelta(days=2)).isoformat(), (today + timedelta(days=1)).isoformat(), None, 4.5, 350.0, 450.0, 0, 'Inspecting drive coupling alignment and lubricant reservoir.'),
        ('WO-2026-002', 'Step Comb Tooth Replacement - Escalator Down', 'Patron dropped coin caused minor comb tooth deformation on step entry.', 4, 'Critical / Emergency', 'Under Review', 4, 1, (today - timedelta(days=1)).isoformat(), today.isoformat(), None, 2.0, 180.0, 200.0, 120, 'Safety barricades deployed. Replacement comb segment retrieved from stock.'),
        ('WO-2026-003', 'Monthly Filter Pack Replacement on Food Court AHU', 'Routine preventive replacement of MERV 13 pre-filters and carbon filters.', 7, 'Medium', 'Completed', 3, 2, (today - timedelta(days=5)).isoformat(), (today - timedelta(days=3)).isoformat(), (today - timedelta(days=3)).isoformat(), 3.0, 240.0, 300.0, 0, 'Replaced 8 filter elements. Differential pressure gauge reset to 0.15 in. wg.'),
        ('WO-2026-004', 'Scenic Elevator Door Sensor Calibration', 'Optical curtain detector intermittently false-triggering on Floor 1.', 5, 'Low', 'Assigned', 4, 5, (today - timedelta(days=3)).isoformat(), (today + timedelta(days=2)).isoformat(), None, 1.0, 0.0, 100.0, 0, 'Cleaned optical lens array. Alignment test scheduled tonight after closing.'),
        ('WO-2026-005', 'Emergency Generator Monthly Full Load Transfer Test', 'Scheduled NFPA 110 compliance simulation run under automatic transfer switch.', 6, 'High', 'Completed', 4, 2, (today - timedelta(days=10)).isoformat(), (today - timedelta(days=10)).isoformat(), (today - timedelta(days=10)).isoformat(), 2.5, 95.0, 250.0, 0, 'ATS triggered without voltage dip. Frequency held at 50.1 Hz stable.')
    ]
    cursor.executemany("""
        INSERT INTO work_orders (wo_number, title, description, asset_id, priority, status, assigned_to, reported_by, created_at, due_date, completed_at, labor_hours, parts_cost, labor_cost, downtime_minutes, resolution_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, work_orders_data)

    # Seed Preventive Maintenance Schedules
    chiller_checklist = json.dumps([
        {"task": "Record suction & discharge refrigerant pressures", "done": False},
        {"task": "Verify oil reservoir level and differential pressure", "done": False},
        {"task": "Inspect evaporator water inlet/outlet temperatures", "done": False},
        {"task": "Check motor electrical terminals for thermal hotspots", "done": False},
        {"task": "Verify safety relief valve seals and burst discs", "done": False}
    ])
    escalator_checklist = json.dumps([
        {"task": "Inspect handrail speed synchronism with step band", "done": False},
        {"task": "Check emergency stop buttons at both landings", "done": False},
        {"task": "Examine comb plate clearance and tooth integrity", "done": False},
        {"task": "Inspect skirting deflector brushes for gap compliance", "done": False},
        {"task": "Lubricate drive chain automatic oiler reservoir", "done": False}
    ])
    generator_checklist = json.dumps([
        {"task": "Test battery electrolyte specific gravity & terminal voltage", "done": False},
        {"task": "Inspect fuel day-tank level and water separator bowl", "done": False},
        {"task": "Check engine coolant level and freeze point protection", "done": False},
        {"task": "Verify block heater operation (warm to touch)", "done": False},
        {"task": "Exercise automatic transfer switch (ATS) in manual bypass", "done": False}
    ])

    pm_schedules_data = [
        ('PM-CHL-M01', 'Monthly Chiller Plant Reliability Inspection', 1, 'Monthly', chiller_checklist, (today - timedelta(days=20)).isoformat(), (today + timedelta(days=10)).isoformat(), 'Engineer', 2.0, 'Active'),
        ('PM-ESC-W01', 'Weekly Escalator Safety & Comb Plate Audit', 3, 'Weekly', escalator_checklist, (today - timedelta(days=4)).isoformat(), (today + timedelta(days=3)).isoformat(), 'Technician', 1.0, 'Active'),
        ('PM-GEN-M01', 'Monthly Standby Power & NFPA Compliance Run', 6, 'Monthly', generator_checklist, (today - timedelta(days=10)).isoformat(), (today + timedelta(days=20)).isoformat(), 'Engineer', 2.5, 'Active')
    ]
    cursor.executemany("""
        INSERT INTO preventive_schedules (code, title, asset_id, frequency, checklist_json, last_executed, next_due, assigned_role, estimated_hours, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pm_schedules_data)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
    seed_sample_data()
    print("Mall RCM Database initialized and seeded successfully.")
