# app/main.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import random
from datetime import date
from streamlit_calendar import calendar
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DE PATH ---
# Garante que o python encontre a pasta utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import db, styles, logic

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Projetos", page_icon="🚀", layout="wide")

# Aplica estilos se existirem
try:
    styles.apply_magalog_style()
except:
    pass

# Inicialização DB
if not os.path.exists("project_management.db"):
    db.init_db()
elif 'db_initialized' not in st.session_state:
    db.init_db()
    st.session_state['db_initialized'] = True

# --- CARREGAMENTO DE DADOS ---
# Carrega projetos e garante colunas necessárias para evitar erros
df_all_projects = db.run_query("SELECT * FROM projects")
if df_all_projects.empty or 'date_changes' not in df_all_projects.columns:
    # Se estiver vazio ou faltar coluna, força recarregar estrutura básica no pandas para não quebrar visual
    cols = ['id', 'name', 'code', 'sponsor', 'manager', 'start_date', 'end_date', 'status', 'priority', 'scope', 'results_text', 'date_changes', 'archived']
    if not df_all_projects.empty:
        # Se tem dados mas falta coluna, cria a coluna no DF
        if 'date_changes' not in df_all_projects.columns: df_all_projects['date_changes'] = 0
    else:
        df_all_projects = pd.DataFrame(columns=cols)

df_active = df_all_projects[df_all_projects['archived'] == 0].copy()
df_archived = df_all_projects[df_all_projects['archived'] == 1].copy()

df_tasks = db.run_query("SELECT * FROM tasks")
df_risks = db.run_query("SELECT * FROM risks")
df_notes = db.run_query("SELECT * FROM project_notes")
df_team = db.run_query("SELECT * FROM team_members")

# --- CARREGA ÁREAS DO BANCO (DINÂMICO) ---
df_sponsors_list = db.run_query("SELECT name FROM sponsors ORDER BY name ASC")
if not df_sponsors_list.empty:
    LISTA_AREAS = df_sponsors_list['name'].tolist()
else:
    LISTA_AREAS = ["Geral"]

# --- LÓGICA DE ALERTAS GLOBAIS ---
projects_at_risk = df_active[df_active['status'] == 'Em Risco']

active_gaps_alert = pd.DataFrame()
if not df_notes.empty and not df_active.empty:
    all_gaps = df_notes[df_notes['category'].str.contains("Gap", na=False)]
    active_gaps_alert = all_gaps[all_gaps['project_id'].isin(df_active['id'])]

def project_has_gap(proj_id):
    if active_gaps_alert.empty: return False
    return proj_id in active_gaps_alert['project_id'].values

def show_project_risk_alert(project_id):
    status = df_active.loc[df_active['id'] == project_id, 'status'].values[0]
    if status == 'Em Risco':
        st.error("🔥 **ALERTA DE STATUS:** Este projeto está marcado como **'Em Risco'**. O prazo ou escopo podem estar comprometidos.", icon="🔥")
    if project_has_gap(project_id):
        gap_desc = active_gaps_alert.loc[active_gaps_alert['project_id'] == project_id, 'description'].values[0]
        st.error(f"⛔ **PROJETO TRAVADO (GAP):** Existe um impeditivo pendente: *{gap_desc}*", icon="🛑")

# Mapa de Cores
COLOR_MAP = {
    "Concluído": "#22C55E", "Feito": "#22C55E", "🟢 Saudável": "#22C55E",
    "Em andamento": "#F59E0B", "Fazendo": "#3B82F6", "🟡 Atenção": "#F59E0B",
    "Em Risco": "#EF4444", "Bloqueado": "#EF4444", "🔴 Crítico": "#EF4444",
    "Backlog": "#9CA3AF", "A fazer": "#9CA3AF", "Cancelado": "#4B5563"
}

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    menu = option_menu(
        menu_title="Gestão de Projetos", 
        options=[
            "Dashboard Executivo", 
            "📝 Central de Cadastros", 
            "Projetos Ativos", 
            "Tarefas", 
            "Cronograma (Gantt)", 
            "Riscos", 
            "Docs & Gaps", 
            "Agenda / Calendário", 
            "Histórico / Arquivados", 
            "⚙️ Cadastros & Config"
        ],
        icons=[
            "speedometer2", 
            "pencil-square",
            "folder-fill", 
            "list-check", 
            "bar-chart-line", 
            "exclamation-triangle", 
            "folder2-open", 
            "calendar-event", 
            "archive", 
            "gear-wide-connected"
        ],
        menu_icon="rocket-takeoff",
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#0B2D5C"},
            "icon": {"color": "white", "font-size": "20px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "0px", "color": "white"},
            "nav-link-selected": {"background-color": "#00B7C2"},
            "menu-title": {"color": "#00B7C2", "font-weight": "bold", "font-size": "24px"}
        }
    )
    st.markdown("---")
    st.markdown("""<div style="text-align: center; color: rgba(255,255,255,0.7); font-size: 13px; margin-top: 20px;"><p><strong>Desenvolvido por<br>Gabriel Fernandes</strong></p></div>""", unsafe_allow_html=True)

# =========================================================
# 1. DASHBOARD EXECUTIVO
# =========================================================
if menu == "Dashboard Executivo":
    if not active_gaps_alert.empty:
        with st.container(border=True):
            st.markdown("### ⛔ Painel de Impeditivos (GAPs)")
            st.markdown("<div style='background-color: #FEF2F2; padding: 10px; border-radius: 5px; color: #991B1B; margin-bottom: 10px;'><strong>Atenção:</strong> Os projetos abaixo têm pendências que impedem o progresso e estão contabilizados como <strong>CRÍTICOS</strong>.</div>", unsafe_allow_html=True)
            for _, row in active_gaps_alert.iterrows():
                p_name = df_active.loc[df_active['id'] == row['project_id'], 'name'].values[0]
                p_manager = df_active.loc[df_active['id'] == row['project_id'], 'manager'].values[0]
                st.error(f"**PROJETO:** {p_name} ({p_manager}) | 🛑 **TRAVA:** {row['description']}", icon="🚫")
        st.divider()

    if not projects_at_risk.empty:
        st.warning(f"🔥 **Atenção:** Existem {len(projects_at_risk)} projetos com status manual **'Em Risco'**.")

    st.title("📊 Dashboard Executivo")
    
    df_view = df_active.copy()
    if not df_view.empty and 'sponsor' in df_view.columns:
        df_view['sponsor'] = df_view['sponsor'].fillna("Geral").replace("", "Geral")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        existing_sponsors = list(df_view['sponsor'].unique())
        combined_options = sorted(list(set(LISTA_AREAS + existing_sponsors)))
        options = ["Todos"] + combined_options
        f_sponsor = st.selectbox("Filtrar por Área", options)
    
    if f_sponsor != "Todos":
        df_view = df_view[df_view['sponsor'] == f_sponsor]

    total = len(df_view)
    if not df_view.empty:
        df_view['health'] = df_view.apply(lambda x: logic.calculate_project_health(x, df_tasks[df_tasks['project_id']==x['id']], df_risks), axis=1)
        def override_health_if_gap(row):
            if project_has_gap(row['id']):
                return "🔴 Crítico"
            return row['health']
        df_view['health'] = df_view.apply(override_health_if_gap, axis=1)
        crit = len(df_view[df_view['health'].str.contains("Crítico")])
        ok = len(df_view[df_view['health'].str.contains("Saudável")])
    else: crit = 0; ok = 0

    late_count = 0
    if not df_active.empty and not df_tasks.empty:
        active_ids = df_active['id'].tolist()
        active_tasks = df_tasks[df_tasks['project_id'].isin(active_ids)].copy()
        if not active_tasks.empty:
            active_tasks['is_late'] = active_tasks.apply(logic.calculate_delay, axis=1)
            late_count = len(active_tasks[active_tasks['is_late']])

    c1, c2, c3, c4 = st.columns(4)
    with c1: styles.card_component("Projetos Ativos", total, "Em execução", "neutral")
    with c2: styles.card_component("Projetos Críticos", crit, "Atenção Imediata (Inc. Gaps)", "danger" if crit > 0 else "success")
    with c3: styles.card_component("Tarefas Atrasadas", late_count, "Impactando Prazos", "danger" if late_count > 0 else "success")
    with c4: styles.card_component("Saudáveis", ok, "Dentro do previsto", "success")
    
    g1, g2 = st.columns([1, 2])
    with g1:
        st.markdown('<div class="magalog-card">', unsafe_allow_html=True)
        st.subheader("Status")
        if not df_view.empty:
            fig = px.pie(df_view, names='status', hole=0.6, color='status', color_discrete_map=COLOR_MAP)
            fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2), margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.markdown('<div class="magalog-card">', unsafe_allow_html=True)
        st.subheader("Eficiência: Físico vs Tempo")
        if not df_view.empty:
            proj_metrics = []
            today = pd.to_datetime("today")
            for _, proj in df_view.iterrows():
                p_tasks = df_tasks[df_tasks['project_id'] == proj['id']]
                real_progress = logic.calculate_progress(p_tasks)
                if pd.notnull(proj['start_date']) and pd.notnull(proj['end_date']):
                    start, end = pd.to_datetime(proj['start_date']), pd.to_datetime(proj['end_date'])
                    total_days = (end - start).days
                    elapsed = (today - start).days
                    time_pct = max(0, min(100, (elapsed / total_days) * 100)) if total_days > 0 else 0
                else: time_pct = 0
                proj_metrics.append({"Nome": proj['name'], "Avanço Real (%)": real_progress, "Tempo Decorrido (%)": time_pct, "Saúde": proj['health']})
            
            df_m = pd.DataFrame(proj_metrics).sort_values('Avanço Real (%)')
            if not df_m.empty:
                fig_combo = go.Figure()
                fig_combo.add_trace(go.Bar(y=df_m['Nome'], x=df_m['Avanço Real (%)'], name='Entrega Real', orientation='h', marker_color=[COLOR_MAP.get(h, "#ccc") for h in df_m['Saúde']], text=df_m['Avanço Real (%)'].apply(lambda x: f"{x:.0f}%"), textposition='auto'))
                fig_combo.add_trace(go.Scatter(y=df_m['Nome'], x=df_m['Tempo Decorrido (%)'], name='Tempo Gasto', mode='markers', marker=dict(symbol='line-ns-open', size=30, color='#2E2E2E', line=dict(width=4))))
                fig_combo.update_layout(height=400, xaxis=dict(range=[0, 105]), legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_combo, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 2. CENTRAL DE CADASTROS (UNIFICADA)
# =========================================================
elif menu == "📝 Central de Cadastros":
    st.title("📝 Central de Cadastros")
    st.markdown("Crie tudo o que precisa em um só lugar.")
    
    t_proj, t_task, t_risk, t_memb, t_gap = st.tabs(["🚀 Novo Projeto", "✅ Nova Tarefa", "🎯 Novo Risco", "👥 Novo Membro", "📂 Novo Gap/Doc"])
    
    # --- PROJETO ---
    with t_proj:
        with st.form("nw_p_cent", clear_on_submit=True):
            nm = st.text_input("Nome do Projeto")
            mg = st.text_input("Gerente do Projeto")
            sp = st.selectbox("Área / Sponsor", LISTA_AREAS)
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Início")
            d2 = c2.date_input("Fim")
            if st.form_submit_button("Criar Projeto"):
                if nm:
                    db.execute_command("INSERT INTO projects (name, manager, sponsor, start_date, end_date, status, date_changes, archived) VALUES (?,?,?,?,?,?,0,0)", (nm, mg, sp, d1, d2, "Backlog"))
                    st.success(f"✅ Projeto '{nm}' criado com sucesso!")
                else: st.warning("Nome obrigatório.")

    # --- TAREFA ---
    with t_task:
        if df_active.empty: st.warning("Crie um projeto antes.")
        else:
            with st.form("nw_t_cent", clear_on_submit=True):
                p_sel = st.selectbox("Projeto", df_active['name'])
                tt = st.text_input("Título da Tarefa")
                ow = st.text_input("Responsável (Dono)")
                dd = st.date_input("Prazo de Entrega")
                if st.form_submit_button("Criar Tarefa"):
                    pid = df_active[df_active['name'] == p_sel]['id'].values[0]
                    if tt:
                        db.execute_command("INSERT INTO tasks (project_id, title, owner, start_date, end_date, status, progress) VALUES (?,?,?,?,?,?,?)", (int(pid), tt, ow, date.today(), dd, "A fazer", 0))
                        st.success("✅ Tarefa Criada!")
                    else: st.warning("Título obrigatório.")

    # --- RISCO ---
    with t_risk:
        if df_active.empty: st.warning("Crie um projeto antes.")
        else:
            with st.form("nw_r_cent", clear_on_submit=True):
                p_sel = st.selectbox("Projeto ", df_active['name'], key="risc_proj")
                d = st.text_input("Descrição do Risco")
                c1, c2 = st.columns(2)
                p = c1.select_slider("Probabilidade", ["Baixa","Média","Alta"])
                i = c2.select_slider("Impacto", ["Baixo","Médio","Alto"])
                pl = st.text_area("Plano de Mitigação")
                if st.form_submit_button("Criar Risco"):
                    pid = df_active[df_active['name'] == p_sel]['id'].values[0]
                    db.execute_command("INSERT INTO risks (project_id, description, probability, impact, mitigation_plan) VALUES (?,?,?,?,?)", (int(pid), d, p, i, pl))
                    st.success("✅ Risco Salvo!")

    # --- MEMBRO ---
    with t_memb:
        with st.form("nw_m_cent", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo")
            cargo = c1.text_input("Cargo")
            area = c2.selectbox("Área", LISTA_AREAS, key="memb_area")
            email = c2.text_input("Email")
            if st.form_submit_button("Cadastrar Membro"):
                if nome:
                    db.execute_command("INSERT INTO team_members (name, role, area, email, phone) VALUES (?,?,?,?,?)", (nome, cargo, area, email, ""))
                    st.success(f"✅ {nome} cadastrado!")
                else: st.warning("
