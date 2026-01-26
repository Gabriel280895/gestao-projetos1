# utils/db.py
import streamlit as st
import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine, text

# Função para pegar a conexão (AJUSTADA)
def get_connection_string():
    try:
        url = st.secrets["connections"]["supabase"]["url"]
        # Correção para o SQLAlchemy funcionar com Postgres
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://")
        return url
    except Exception as e:
        st.error(f"Erro ao ler Secrets: {e}")
        return None

def init_db():
    db_url = get_connection_string()
    if not db_url: return

    try:
        # Usa SQLAlchemy para criar tabelas (mais robusto)
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # 1. Projetos
            conn.execute(text('''CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT, code TEXT, sponsor TEXT, manager TEXT,
                start_date DATE, end_date DATE, status TEXT, priority TEXT,
                scope TEXT, results_text TEXT, date_changes INTEGER DEFAULT 0,
                archived INTEGER DEFAULT 0, notes TEXT
            )'''))
            
            # 2. Tarefas
            conn.execute(text('''CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                title TEXT, owner TEXT, start_date DATE, end_date DATE,
                status TEXT, priority TEXT, effort INTEGER, progress INTEGER
            )'''))
            
            # 3. Riscos
            conn.execute(text('''CREATE TABLE IF NOT EXISTS risks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                description TEXT, probability TEXT, impact TEXT,
                mitigation_plan TEXT, owner TEXT, status TEXT DEFAULT 'Ativo'
            )'''))

            # 4. Gaps/Notas
            conn.execute(text('''CREATE TABLE IF NOT EXISTS project_notes (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                category TEXT, description TEXT, link_url TEXT, created_at DATE
            )'''))

            # 5. Áreas
            conn.execute(text('''CREATE TABLE IF NOT EXISTS sponsors (name TEXT PRIMARY KEY)'''))

            # 6. Equipe
            conn.execute(text('''CREATE TABLE IF NOT EXISTS team_members (
                id SERIAL PRIMARY KEY,
                name TEXT, role TEXT, area TEXT, email TEXT, phone TEXT
            )'''))
            
            conn.commit()
            
        # Seed inicial
        check_seed()
        
    except Exception as e:
        st.error(f"❌ Erro ao conectar/criar tabelas: {e}")

def check_seed():
    df = run_query("SELECT count(*) as cnt FROM projects")
    if not df.empty and df.iloc[0]['cnt'] == 0:
        from datetime import date, timedelta
        today = date.today()
        execute_command(
            "INSERT INTO projects (name, manager, start_date, end_date, status, date_changes, archived, notes) VALUES (:name, :mgr, :start, :end, :st, 0, 0, '')", 
            {"name":"Exemplo Supabase", "mgr":"Gerente", "start":today, "end":today+timedelta(30), "st":"Em andamento"}
        )
        
        areas = ["Geral", "TI", "RH", "Financeiro", "Marketing", "Operações", "Comercial", "Logística"]
        for area in areas:
            execute_command("INSERT INTO sponsors (name) VALUES (:name) ON CONFLICT DO NOTHING", {"name":area})

def run_query(query, params=None, fetch=True):
    db_url = get_connection_string()
    if not db_url: return pd.DataFrame()
    
    # Adaptação da query do SQLite (?) para SQLAlchemy (:param)
    # Se o código antigo usa ?, tentamos converter, mas o ideal é usar dicionário
    if params and isinstance(params, tuple):
         # Truque sujo para compatibilidade: converte tuple para dict se a query usar :param
         # Mas para manter compatível com o código main.py que usa ?, vamos usar raw connection do pandas
         pass

    try:
        engine = create_engine(db_url)
        # Pandas read_sql com SQLAlchemy aceita %s ou :param dependendo do driver
        # Vamos forçar o uso cru do psycopg2 via pandas para manter compatibilidade com o ? do main.py
        
        # ATENÇÃO: O main.py usa '?' (estilo sqlite). Postgres usa %s.
        # Vamos substituir na força bruta para salvar o dia
        query = query.replace('?', '%s')
        
        if fetch:
            # Para SELECT
            with engine.connect() as conn:
                # O pandas read_sql precisa de uma conexão
                return pd.read_sql(text(query.replace('%s', ':p')), conn, params=params if params else {})
                # Nota: Ajustar parametros de tuple para dict é complexo aqui.
                # VAMOS SIMPLIFICAR: Usar psycopg2 direto que aceita tuple
        
        # Se falhar acima, fallback para psycopg2 puro (que aceita o %s que trocamos)
        conn = psycopg2.connect(st.secrets["connections"]["supabase"]["url"])
        cur = conn.cursor()
        if fetch:
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            return df
        else:
            cur.execute(query, params)
            conn.commit()
            conn.close()
            return None

    except Exception as e:
        # Tenta fallback direto com psycopg2 se o SQLAlchemy falhar na conversão de params
        try:
            conn = psycopg2.connect(st.secrets["connections"]["supabase"]["url"])
            query = query.replace('?', '%s')
            if fetch:
                df = pd.read_sql(query, conn, params=params)
                conn.close()
                return df
            else:
                cur = conn.cursor()
                cur.execute(query, params)
                conn.commit()
                conn.close()
                return None
        except Exception as e2:
            st.error(f"Erro SQL: {e2}")
            return pd.DataFrame() if fetch else None

def execute_command(query, params=()):
    return run_query(query, params, fetch=False)
