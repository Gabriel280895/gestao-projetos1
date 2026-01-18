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

# Configuração de Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import db, styles, logic

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Projetos", page_icon="🚀", layout="wide")
styles.apply_magalog_style()

# Inicialização DB (Verificação Robusta)
if not os.path.exists("project_management.db"):
    db.init_db()
    db.seed_data()
    st.session_state['db_initialized'] = True
elif 'db_initialized' not in st.session_state:
    db.init_db()
    st.session_state['db_initialized'] = True

# --- CARREGAMENTO DE DADOS BLINDADO ---
# Projetos
df_all_projects = db.run_query("SELECT * FROM projects")
if df_all_projects.empty or 'id' not in df_all_projects.columns:
    df_all_projects = pd.DataFrame(columns=['id', 'name', 'code', 'sponsor', 'manager', 'start_date', 'end_date', 'status', 'priority', 'scope', 'results_text', 'archived'])

df_active = df_all_projects[df_all_projects['archived'] == 0]
df_archived = df_all_projects[df_all_projects['archived'] == 1]

# Tarefas
df_tasks = db.run_query("SELECT * FROM tasks")
if df_tasks.empty or 'project_id' not in df_tasks.columns:
    df_tasks = pd.DataFrame(columns=['id', 'project_id', 'title', 'owner', 'start_date', 'end_date', 'status', 'priority', 'effort', 'progress'])

# Riscos
df_risks = db.run_query("SELECT * FROM risks")
if df_risks.empty:
    df_risks = pd.DataFrame(columns=['id', 'project_id', 'description', 'probability', 'impact', 'mitigation_plan', 'owner', 'status'])

# Notas
df_notes = db.run_query("SELECT * FROM project_notes")
if df_notes.empty:
    df_notes = pd.DataFrame(columns=['id', 'project_id', 'category', 'description', 'link_url', 'created_at'])

# Lógica de Alertas (Gaps)
active_gaps_alert = pd.DataFrame()
if not df_notes.empty and not df_active.empty:
    all_gaps = df_notes[df_notes['category'].str.contains("Gap", na=False)]
    active_gaps_alert = all_gaps[all_gaps['project_id'].isin(df_active['id'])]

def project_has_gap(proj_id):
    if active_gaps_alert.empty: return False
    return proj_id in active_gaps_alert['project_id'].values

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
        options=["Dashboard Executivo", "Projetos Ativos", "Histórico / Arquivados", "Tarefas", "Docs & Gaps", "Cronograma (Gantt)", "Riscos", "Agenda / Calendário", "Config & Export"],
        icons=["speedometer2", "folder-fill", "archive", "list-check", "folder2-open", "bar-chart-line", "exclamation-triangle", "calendar-event", "gear"],
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
    st.markdown(
        """
        <div style="text-align: center; color: rgba(255,255,255,0.7); font-size: 13px; margin-top: 20px;">
            <p><strong>Desenvolvido por<br>Gabriel Fernandes</strong></p>
            <p style="font-size: 11px; color: rgba(255,255,255,0.5);">v1.9 - Galeria Edition</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# =========================================================
# 1. DASHBOARD EXECUTIVO
# =========================================================
if menu == "Dashboard Executivo":
    if not active_gaps_alert.empty:
        st.error(f"🚨 **ATENÇÃO: {len(active_gaps_alert)} GAPS EM PROJETOS ATIVOS!**")
        for _, row in active_gaps_alert.iterrows():
            p_name = df_active.loc[df_active['id'] == row['project_id'], 'name'].values[0]
            st.markdown(f"**🛑 {p_name}**: {row['description']}")
        st.divider()

    st.title("📊 Dashboard Executivo")
    
    df_view = df_active.copy()
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        options = ["Todos"] + list(df_view['sponsor'].unique()) if not df_view.empty else ["Todos"]
        f_sponsor = st.selectbox("Filtrar por Área", options)
    if f_sponsor != "Todos": df_view = df_view[df_view['sponsor'] == f_sponsor]

    total = len(df_view)
    if not df_view.empty:
        df_view['health'] = df_view.apply(lambda x: logic.calculate_project_health(x, df_tasks[df_tasks['project_id']==x['id']], df_risks), axis=1)
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
    with c2: styles.card_component("Projetos Críticos", crit, "Atenção Imediata", "danger" if crit > 0 else "success")
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
# 2. PROJETOS ATIVOS
# =========================================================
elif menu == "Projetos Ativos":
    st.title("📁 Projetos em Andamento")
    t1, t2 = st.tabs(["Lista", "Novo Projeto"])
    with t1:
        if not df_active.empty:
            d = df_active.copy()
            d['gap'] = d['id'].apply(lambda x: "🛑 GAP" if project_has_gap(x) else "")
            st.dataframe(d[['name', 'manager', 'status', 'end_date', 'gap']], hide_index=True, use_container_width=True)
            st.divider()
            st.markdown("### ✏️ Editar")
            sel = st.selectbox("Projeto:", df_active['name'])
            if sel:
                curr = df_active[df_active['name'] == sel].iloc[0]
                with st.form("ed_p"):
                    ns = st.selectbox("Status", ["Em andamento", "Em Risco", "Concluído"], index=0)
                    arq = st.checkbox("Arquivar")
                    if st.form_submit_button("Salvar"):
                        db.execute_command("UPDATE projects SET status=?, archived=? WHERE id=?", (ns, 1 if arq else 0, int(curr['id'])))
                        st.rerun()
    with t2:
        with st.form("nw_p"):
            nm = st.text_input("Nome")
            mg = st.text_input("Gerente")
            d1 = st.date_input("Início")
            d2 = st.date_input("Fim")
            if st.form_submit_button("Criar"):
                db.execute_command("INSERT INTO projects (name, manager, start_date, end_date, status, archived) VALUES (?,?,?,?,?,0)", (nm, mg, d1, d2, "Backlog"))
                st.rerun()

# =========================================================
# 3. HISTÓRICO / ARQUIVADOS
# =========================================================
elif menu == "Histórico / Arquivados":
    st.title("🏛️ Galeria de Projetos Arquivados")
    st.markdown("Histórico de projetos concluídos ou cancelados. Utilize para registrar **Lições Aprendidas** e **Ganhos**.")
    
    if df_archived.empty:
        st.info("Nenhum projeto arquivado ainda.")
    else:
        cols = st.columns(3)
        for idx, row in df_archived.iterrows():
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #E5E7EB; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;">
                    <h3 style="color: #0B2D5C; margin: 0 0 5px 0;">{row['name']}</h3>
                    <span style="background-color: #E5E7EB; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; color: #374151;">{row['status']}</span>
                    <p style="font-size: 13px; color: #6B7280; margin-top: 10px;">
                        👤 <b>Gerente:</b> {row['manager']}<br>
                        🏁 <b>Fim:</b> {row['end_date']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🏆 Ver Ganhos & Resultados"):
                    with st.form(key=f"results_{row['id']}"):
                        current_text = row['results_text'] if row['results_text'] else ""
                        results = st.text_area("Quais foram os ganhos/entregáveis?", value=current_text, height=100, placeholder="Ex: Redução de 20% no custo operacional...")
                        
                        c_btn1, c_btn2 = st.columns([1,1])
                        if c_btn1.form_submit_button("💾 Salvar"):
                            db.execute_command("UPDATE projects SET results_text = ? WHERE id = ?", (results, row['id']))
                            st.success("Salvo!")
                            st.rerun()
                        
                        if c_btn2.form_submit_button("🔄 Restaurar"):
                            db.execute_command("UPDATE projects SET archived = 0 WHERE id = ?", (row['id'],))
                            st.success("Restaurado!")
                            st.rerun()

# =========================================================
# 4. TAREFAS (VISUAL COLORIDO RESTAURADO)
# =========================================================
elif menu == "Tarefas":
    st.title("✅ Tarefas (Visual Kanban)")
    
    opts = dict(zip(df_active['name'], df_active['id']))
    
    if not opts:
        st.warning("Sem projetos ativos.")
    else:
        sel_nm = st.selectbox("Selecione o Projeto:", list(opts.keys()))
        sel_id = opts[sel_nm]
        
        # Filtra tarefas
        tv = df_tasks[df_tasks['project_id'] == sel_id]
        
        t_tab1, t_tab2 = st.tabs(["📊 Kanban Board", "➕ Nova Tarefa"])
        
        with t_tab1:
            c1, c2, c3, c4 = st.columns(4)
            
            # --- COLUNA: A FAZER (NEUTRO) ---
            with c1:
                st.markdown("### 📝 A fazer")
                st.markdown("---")
                for _, t in tv[tv['status'] == "A fazer"].iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{t['title']}**")
                        st.caption(f"👤 {t['owner']}")
                        st.progress(int(t['progress']))
                        with st.expander("✏️ Editar"):
                            with st.form(f"f1_{t['id']}"):
                                ns = st.selectbox("Status", ["A fazer", "Fazendo", "Bloqueado", "Feito"], index=0)
                                np = st.slider("%", 0, 100, int(t['progress']))
                                if st.form_submit_button("Salvar"):
                                    db.execute_command("UPDATE tasks SET status=?, progress=? WHERE id=?", (ns, np, t['id']))
                                    st.rerun()

            # --- COLUNA: FAZENDO (AMARELO/EMOJIS) ---
            with c2:
                st.markdown("### 🔨 Fazendo")
                st.markdown("---")
                for _, t in tv[tv['status'] == "Fazendo"].iterrows():
                    # Usa st.warning para dar a cor de fundo amarela e ícone
                    st.warning(f"**{t['title']}**\n\n👤 {t['owner']}", icon="🏗️")
                    
                    with st.expander("⚙️ Ações"):
                         with st.form(f"f2_{t['id']}"):
                            ns = st.selectbox("Mover para:", ["A fazer", "Fazendo", "Bloqueado", "Feito"], index=1)
                            np = st.slider("Progresso (%)", 0, 100, int(t['progress']))
                            if st.form_submit_button("Atualizar"):
                                db.execute_command("UPDATE tasks SET status=?, progress=? WHERE id=?", (ns, np, t['id']))
                                st.rerun()

            # --- COLUNA: BLOQUEADO (VERMELHO/EMOJIS) ---
            with c3:
                st.markdown("### 🚫 Bloqueado")
                st.markdown("---")
                for _, t in tv[tv['status'] == "Bloqueado"].iterrows():
                    # Usa st.error para dar a cor de fundo vermelha e ícone
                    st.error(f"**{t['title']}**\n\n🛑 Travado", icon="🚨")
                    
                    with st.expander("🔓 Resolver"):
                         with st.form(f"f3_{t['id']}"):
                            ns = st.selectbox("Mover para:", ["A fazer", "Fazendo", "Bloqueado", "Feito"], index=2)
                            if st.form_submit_button("Desbloquear"):
                                db.execute_command("UPDATE tasks SET status=? WHERE id=?", (ns, t['id']))
                                st.rerun()

            # --- COLUNA: FEITO (VERDE/EMOJIS) ---
            with c4:
                st.markdown("### ✅ Feito")
                st.markdown("---")
                for _, t in tv[tv['status'] == "Feito"].iterrows():
                    # Usa st.success para dar a cor de fundo verde e ícone
                    st.success(f"**{t['title']}**\n\n🏁 100% Concluído", icon="🎉")
                    
                    with st.expander("Reabrir?"):
                         with st.form(f"f4_{t['id']}"):
                            if st.form_submit_button("Voltar para Fazendo"):
                                db.execute_command("UPDATE tasks SET status='Fazendo', progress=50 WHERE id=?", (t['id'],))
                                st.rerun()

        with t_tab2:
            with st.form("new_t_form"):
                tt = st.text_input("Título da Tarefa")
                ow = st.text_input("Responsável (Dono)")
                dd = st.date_input("Prazo de Entrega")
                if st.form_submit_button("Criar Tarefa"):
                    db.execute_command("INSERT INTO tasks (project_id, title, owner, start_date, end_date, status, progress) VALUES (?,?,?,?,?,?,?)", (sel_id, tt, ow, date.today(), dd, "A fazer", 0))
                    st.success("Tarefa Criada com Sucesso!")
                    st.rerun()

# =========================================================
# 5. GAPS
# =========================================================
elif menu == "Docs & Gaps":
    st.title("📂 Docs & Gaps")
    opts = dict(zip(df_active['name'], df_active['id']))
    if opts:
        sel_nm = st.selectbox("Projeto:", list(opts.keys()))
        sel_id = opts[sel_nm]
        nv = df_notes[df_notes['project_id'] == sel_id]
        
        with st.form("ngap"):
            d = st.text_area("Descrição")
            t = st.radio("Tipo", ["Gap", "Link"])
            if st.form_submit_button("Salvar"):
                db.execute_command("INSERT INTO project_notes (project_id, category, description, created_at) VALUES (?,?,?,?)", (sel_id, t, d, date.today()))
                st.rerun()
        st.divider()
        for _, n in nv.iterrows():
            st.write(f"**{n['category']}**: {n['description']}")
            if st.button("x", key=f"dn_{n['id']}"):
                db.execute_command("DELETE FROM project_notes WHERE id=?", (n['id'],))
                st.rerun()

# =========================================================
# 6. GANTT
# =========================================================
elif menu == "Cronograma (Gantt)":
    st.title("📅 Gantt")
    gantt = df_tasks[df_tasks['project_id'].isin(df_active['id'])].merge(df_active[['id','name']], left_on='project_id', right_on='id')
    if not gantt.empty:
        fig = px.timeline(gantt, x_start="start_date", x_end="end_date", y="name", color="status", color_discrete_map=COLOR_MAP)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# 7. RISCOS
# =========================================================
elif menu == "Riscos":
    st.title("🎯 Riscos")
    if 'r_view' not in st.session_state: st.session_state['r_view'] = 'matriz'
    
    opts = dict(zip(df_active['name'], df_active['id']))
    if opts:
        sel_nm = st.selectbox("Projeto:", list(opts.keys()))
        sel_id = opts[sel_nm]
        rv = df_risks[df_risks['project_id'] == sel_id].copy()
        
        if st.session_state['r_view'] == 'matriz':
            if st.button("➕ Novo Risco"): 
                st.session_state['r_view'] = 'novo'
                st.rerun()
            
            if not rv.empty:
                col_name = 'title' if 'title' in rv.columns else 'description'
                m = {'Baixa':1,'Baixo':1,'Média':2,'Médio':2,'Alta':3,'Alto':3}
                rv['px'] = rv['impact'].map(m).fillna(2) + [random.uniform(-0.1,0.1) for _ in range(len(rv))]
                rv['py'] = rv['probability'].map(m).fillna(2) + [random.uniform(-0.1,0.1) for _ in range(len(rv))]
                
                fig = go.Figure()
                fig.add_vline(x=2.5, line_dash="dash", line_color="#ccc")
                fig.add_hline(y=2.5, line_dash="dash", line_color="#ccc")
                fig.add_trace(go.Scatter(x=rv['px'], y=rv['py'], mode='markers', hovertext=rv[col_name], marker=dict(size=20, color='#EF4444')))
                fig.update_layout(title="Matriz", xaxis=dict(range=[0.5,3.5], tickvals=[1,2,3]), yaxis=dict(range=[0.5,3.5], tickvals=[1,2,3]), height=400, plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
                
                for _, r in rv.iterrows():
                    with st.expander(f"{r[col_name]}"):
                        st.write(r.get('mitigation_plan',''))
                        if st.button("Excluir", key=f"dr_{r['id']}"):
                            db.execute_command("DELETE FROM risks WHERE id=?", (r['id'],))
                            st.rerun()
            else: st.info("Sem riscos.")

        elif st.session_state['r_view'] == 'novo':
            if st.button("Voltar"):
                st.session_state['r_view'] = 'matriz'
                st.rerun()
            with st.form("nr", clear_on_submit=True):
                d = st.text_input("Descrição")
                p = st.select_slider("Prob", ["Baixa","Média","Alta"])
                i = st.select_slider("Impacto", ["Baixo","Médio","Alto"])
                pl = st.text_area("Plano")
                if st.form_submit_button("Salvar"):
                    db.execute_command("INSERT INTO risks (project_id, description, probability, impact, mitigation_plan) VALUES (?,?,?,?,?)", (sel_id, d, p, i, pl))
                    st.success("Salvo!")
                    st.session_state['r_view'] = 'matriz'
                    st.rerun()

# =========================================================
# 8. AGENDA
# =========================================================
elif menu == "Agenda / Calendário":
    st.title("📆 Agenda")
    evs = []
    for _,p in df_active.iterrows(): evs.append({"title":f"Fim: {p['name']}","start":str(p['end_date'])})
    calendar(events=evs)

# =========================================================
# 9. CONFIG
# =========================================================
elif menu == "Config & Export":
    st.title("Config")
    if st.button("Reset DB"):
        if os.path.exists("project_management.db"):
            os.remove("project_management.db")
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()