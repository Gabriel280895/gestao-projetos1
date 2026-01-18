# utils/styles.py
import streamlit as st

def apply_magalog_style():
    # Cores
    PRIMARY_COLOR = "#0B2D5C"
    SECONDARY_COLOR = "#00B7C2"
    BG_COLOR = "#F5F7FA"
    CARD_BG = "#FFFFFF"
    
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            background-color: {BG_COLOR};
            color: #2E2E2E;
        }}
        
        /* =============================================
           BARRA LATERAL (SIDEBAR)
           ============================================= */
        section[data-testid="stSidebar"] {{
            background-color: {PRIMARY_COLOR};
            border-right: 1px solid #E5E7EB;
        }}

        /* FORÇA BRUTA: Tudo na sidebar fica branco */
        section[data-testid="stSidebar"] * {{
            color: #FFFFFF !important;
        }}
        
        /* Correção específica para o Menu de Navegação (Radio) */
        section[data-testid="stSidebar"] .stRadio label p {{
            font-size: 16px !important;
            font-weight: 500 !important;
        }}

        /* Títulos na Sidebar em Ciano */
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {{
            color: {SECONDARY_COLOR} !important;
        }}

        /* =============================================
           ÁREA PRINCIPAL (MAIN)
           ============================================= */
        
        /* Garante que os textos da área principal NÃO sejam afetados pela sidebar */
        .main p, .main span, .main label, .main div {{
            color: #2E2E2E;
        }}

        /* Filtros e Inputs (Selectbox, DateInput, etc) */
        .stSelectbox label, .stDateInput label, .stTextInput label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600;
        }}
        
        /* Topbar decoration */
        .stAppHeader {{
            background-color: {CARD_BG};
            border-bottom: 1px solid #E5E7EB;
        }}

        /* Cards */
        .magalog-card {{
            background-color: {CARD_BG};
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
            border-left: 5px solid {SECONDARY_COLOR};
        }}
        
        /* KPIs */
        div[data-testid="metric-container"] {{
            background-color: {CARD_BG};
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #E5E7EB;
        }}
        
        /* Títulos Principais */
        .main h1, .main h2, .main h3 {{
            color: {PRIMARY_COLOR} !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# utils/styles.py (Apenas a parte final)

def card_component(title, value, subtitle="", context="neutral"):
    # CORES PADRÃO "SEMÁFORO" DIDÁTICO
    colors = {
        "neutral": "#3B82F6", # Azul (Informativo)
        "success": "#22C55E", # Verde (Bom)
        "warning": "#F59E0B", # Amarelo/Laranja (Atenção)
        "danger":  "#EF4444"  # Vermelho (Crítico)
    }
    color = colors.get(context, "#3B82F6")
    
    html = f"""
    <div style="
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
        border-top: 5px solid {color}; /* Borda mais grossa para destaque */
        text-align: center;
        margin-bottom: 10px;">
        <h4 style="margin:0; font-size: 14px; color: #6B7280; text-transform: uppercase; font-weight: 700;">{title}</h4>
        <h2 style="margin: 5px 0; font-size: 28px; color: {color}; font-weight: 800;">{value}</h2>
        <p style="margin:0; font-size: 13px; color: #4B5563;">{subtitle}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)