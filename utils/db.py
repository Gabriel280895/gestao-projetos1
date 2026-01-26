# utils/db.py
import streamlit as st
import pandas as pd
import psycopg2
import os

# Função para conectar ao banco
def get_connection():
    try:
        # Pega a URL dos segredos
        db_url = st.secrets["connections"]["supabase"]["url"]
        # Conecta diretamente usando psycopg2
        return psycopg2.connect(db_url)
    except Exception as e:
        st.error(f"Erro de Conexão com o Banco: {e}")
        return None

def init_db():
    """Cria as tabelas se não existirem"""
    conn = get_connection()
    if not conn: return
    
    try:
        c = conn.cursor()
        
        # 1. Projetos
        c.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT, code TEXT, sponsor TEXT, manager TEXT,
                start_date DATE, end_date DATE, status TEXT, priority TEXT,
                scope TEXT, results_text TEXT, date_changes INTEGER DEFAULT 0,
                archived INTEGER DEFAULT 0, notes TEXT
            );
        """)
        
        # 2. Tarefas
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                title TEXT, owner TEXT, start_date DATE, end_date DATE,
                status TEXT, priority TEXT, effort INTEGER, progress INTEGER
            );
        """)
        
        # 3. Riscos
        c.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                description TEXT, probability TEXT, impact TEXT,
                mitigation_plan TEXT, owner TEXT, status TEXT DEFAULT 'Ativo'
            );
        """)

        # 4. Gaps/Notas
        c.execute("""
            CREATE TABLE IF NOT EXISTS project_notes (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                category TEXT, description TEXT, link_url TEXT, created_at DATE
            );
        """)

        # 5. Áreas
        c.execute("""
            CREATE TABLE IF NOT EXISTS sponsors (name TEXT PRIMARY KEY);
        """)

        # 6. Equipe
        c.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id SERIAL PRIMARY KEY,
                name TEXT, role TEXT, area TEXT, email TEXT, phone TEXT
            );
        """)
        
        conn.commit()
        c.close()
        conn.close()
        
        check_seed()
        
    except Exception as e:
        st.error(f"Erro ao criar tabelas: {e}")

def check_seed():
    """Insere dados iniciais se o banco estiver vazio"""
    df = run_query("SELECT count(*) as cnt FROM projects")
    if not df.empty and df.iloc[0]['cnt'] == 0:
        from datetime import date, timedelta
        today = date.today()
        
        # Insere Projeto Exemplo
        execute_command(
            "INSERT INTO projects (name, manager, start_date, end_date, status, date_changes, archived, notes) VALUES (%s, %s, %s, %s, %s, 0, 0, '')", 
            ("Exemplo Supabase", "Gerente", today, today+timedelta(30), "Em andamento")
        )
        
        # Insere Áreas
        areas = ["Geral", "TI", "RH", "Financeiro", "Marketing", "Operações", "Comercial", "Logística"]
        for area in areas:
            execute_command("INSERT INTO sponsors (name) VALUES (%s) ON CONFLICT DO NOTHING", (area,))

def run_query(query, params=(), fetch=True):
    """Roda query SQL e trata conversão de ? para %s"""
    conn = get_connection()
    if not conn: return pd.DataFrame() if fetch else None
    
    # TRUQUE IMPORTANTE:
    # O app usa '?' (padrão SQLite) mas Postgres usa '%s'.
    # Substituímos automaticamente aqui para não precisar reescrever o main.py
    postgres_query = query.replace('?', '%s')
    
    try:
        if fetch:
            # Para SELECT (Ler dados)
            df = pd.read_sql(postgres_query, conn, params=params)
            conn.close()
            return df
        else:
            # Para INSERT/UPDATE/DELETE (Escrever dados)
            c = conn.cursor()
            c.execute(postgres_query, params)
            conn.commit()
            conn.close()
            return None
    except Exception as e:
        st.error(f"Erro na Query: {e}")
        if conn: conn.close()
        return pd.DataFrame() if fetch else None

def execute_command(query, params=()):
    return run_query(query, params, fetch=False)
