# utils/logic.py
import pandas as pd
from datetime import datetime, date

def calculate_delay(row):
    """Retorna True se estiver atrasado (Hoje > Data Fim E não concluído)"""
    if row['status'] in ['Feito', 'Concluído', 'Cancelado']:
        return False
    
    end_date = pd.to_datetime(row['end_date']).date() if isinstance(row['end_date'], str) else row['end_date']
    return end_date < date.today()

def calculate_project_health(project, tasks_df, risks_df):
    """
    Verde: Sem atraso e sem riscos altos
    Amarelo: Atraso leve (< 7 dias) OU Riscos médios
    Vermelho: Atraso crítico (> 7 dias) OU Risco Alto
    """
    proj_id = project['id']
    
    # Verifica Atraso do Projeto
    is_late = calculate_delay(project)
    days_late = (date.today() - pd.to_datetime(project['end_date']).date()).days if is_late else 0
    
    # Riscos
    proj_risks = risks_df[risks_df['project_id'] == proj_id]
    has_high_risk = not proj_risks[proj_risks['probability'] == 'Alta'].empty
    
    if days_late > 7 or has_high_risk:
        return "🔴 Crítico"
    elif is_late or not proj_risks[proj_risks['probability'] == 'Média'].empty:
        return "🟡 Atenção"
    else:
        return "🟢 Saudável"

def calculate_progress(tasks_df):
    """Média ponderada pelo esforço"""
    if tasks_df.empty:
        return 0
    
    total_effort = tasks_df['effort'].sum()
    if total_effort == 0:
        return tasks_df['progress'].mean()
        
    weighted_progress = (tasks_df['progress'] * tasks_df['effort']).sum()
    return round(weighted_progress / total_effort, 1)