# utils/db.py
import streamlit as st
import pandas as pd
import psycopg2
import os

# Função para pegar a conexão
def get_connection():
    try:
        # Pega a URL dos Secrets do Streamlit Cloud
        db_url = st.secrets["connections"]["supabase"]["url"]
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn:
        st.error("❌ Erro ao conectar no Supabase. Verifique os Secrets.")
        return
        
    c = conn.cursor()
    
    # CRIAÇÃO DAS TABELAS (Sintaxe PostgreSQL)
    
    # 1. Projetos
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
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
        archived INTEGER DEFAULT 0,
        notes TEXT
    )''')
    
    # 2. Tarefas
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id),
        title TEXT,
        owner TEXT,
        start_date DATE,
        end_date DATE,
        status TEXT,
        priority TEXT,
        effort INTEGER,
        progress INTEGER
    )''')
    
    # 3. Riscos
    c.execute('''CREATE TABLE IF NOT EXISTS risks (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id),
        description TEXT,
        probability TEXT,
        impact TEXT,
        mitigation_plan TEXT,
        owner TEXT,
        status TEXT DEFAULT 'Ativo'
    )''')

    # 4. Gaps/Notas
    c.execute('''CREATE TABLE IF NOT EXISTS project_notes (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id),
        category TEXT,
        description TEXT,
        link_url TEXT,
        created_at DATE
    )''')

    # 5. Áreas / Sponsors
    c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
        name TEXT PRIMARY KEY
    )''')

    # 6. Equipe / Contatos
    c.execute('''CREATE TABLE IF NOT EXISTS team_members (
        id SERIAL PRIMARY KEY,
        name TEXT,
        role TEXT,
        area TEXT,
        email TEXT,
        phone TEXT
    )''')
    
    conn.commit()
    conn.close()
    
    # Verifica se precisa inserir dados iniciais
    check_seed()

def check_seed():
    # Verifica se a tabela projects está vazia
    df = run_query("SELECT count(*) as cnt FROM projects")
    if not df.empty and df.iloc[0]['cnt'] == 0:
        from datetime import date, timedelta
        today = date.today()
        # Insere projeto de exemplo
        execute_command(
            "INSERT INTO projects (name, manager, start_date, end_date, status, date_changes, archived, notes) VALUES (%s,%s,%s,%s,%s,0,0,'')", 
            ("Exemplo Supabase", "Gerente", today, today+timedelta(30), "Em andamento")
        )
        
        # Insere áreas padrão
        areas = ["Geral", "TI", "RH", "Financeiro", "Marketing", "Operações", "Comercial", "Logística"]
        for area in areas:
            execute_command("INSERT INTO sponsors (name) VALUES (%s) ON CONFLICT DO NOTHING", (area,))

def run_query(query, params=(), fetch=True):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    
    # ADAPTAÇÃO: O código do app usa '?' (SQLite), mas Postgres usa '%s'
    # Essa linha faz a tradução automática para você não precisar mexer no main.py
    query_postgres = query.replace('?', '%s')
    
    try:
        if fetch:
            df = pd.read_sql(query_postgres, conn, params=params)
            conn.close()
            return df
        else:
            c = conn.cursor()
            c.execute(query_postgres, params)
            conn.commit()
            conn.close()
            return None
    except Exception as e:
        # st.error(f"Erro SQL: {e}") # Descomente para debug
        if conn: conn.close()
        return pd.DataFrame() if fetch else None

def execute_command(query, params=()):
    return run_query(query, params, fetch=False)
