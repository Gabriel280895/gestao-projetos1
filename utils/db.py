# utils/db.py
import sqlite3
import pandas as pd
from datetime import date, timedelta
import os

DB_PATH = "project_management.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Projetos (ADICIONADO CAMPO date_changes)
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        code TEXT,
        sponsor TEXT,
        manager TEXT,
        start_date DATE,
        end_date DATE,
        status TEXT,
        priority TEXT,
        scope TEXT,
        results_text TEXT, 
        date_changes INTEGER DEFAULT 0,
        archived INTEGER DEFAULT 0
    )''')
    
    # 2. Tarefas
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        title TEXT,
        owner TEXT,
        start_date DATE,
        end_date DATE,
        status TEXT,
        priority TEXT,
        effort INTEGER,
        progress INTEGER,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )''')
    
    # 3. Riscos
    c.execute('''CREATE TABLE IF NOT EXISTS risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        description TEXT,
        probability TEXT,
        impact TEXT,
        mitigation_plan TEXT,
        owner TEXT,
        status TEXT DEFAULT 'Ativo',
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )''')

    # 4. Gaps/Notas
    c.execute('''CREATE TABLE IF NOT EXISTS project_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        category TEXT,
        description TEXT,
        link_url TEXT,
        created_at DATE,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )''')

    # 5. Áreas / Sponsors
    c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
        name TEXT PRIMARY KEY
    )''')

    # 6. Equipe / Contatos
    c.execute('''CREATE TABLE IF NOT EXISTS team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        role TEXT,
        area TEXT,
        email TEXT,
        phone TEXT
    )''')
    
    conn.commit()
    conn.close()
    
    seed_data()

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Seed Projetos
    c.execute("SELECT count(*) FROM projects")
    if c.fetchone()[0] == 0:
        today = date.today()
        # Adicionado 0 para date_changes
        c.execute("INSERT INTO projects (name, manager, start_date, end_date, status, date_changes, archived) VALUES (?,?,?,?,?,0,0)", ("Exemplo de Projeto", "Gerente", today, today+timedelta(30), "Em andamento"))
    
    # Seed Areas
    default_areas = ["Geral", "TI", "RH", "Financeiro", "Marketing", "Operações", "Comercial", "Logística"]
    for area in default_areas:
        c.execute("INSERT OR IGNORE INTO sponsors (name) VALUES (?)", (area,))
        
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_PATH)
    if fetch:
        try: df = pd.read_sql(query, conn, params=params)
        except: df = pd.DataFrame()
        conn.close()
        return df
    else:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()
        return None

def execute_command(query, params=()):
    return run_query(query, params, fetch=False)
