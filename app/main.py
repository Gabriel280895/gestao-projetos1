# =========================================================
# 2. PROJETOS ATIVOS
# =========================================================
elif menu == "Projetos Ativos":
    st.title("📁 Projetos em Andamento")
    t1, t2 = st.tabs(["Lista", "Novo Projeto"])
    
    with t1:
        if not df_active.empty:
            d = df_active.copy()
            d['gap_indicador'] = d['id'].apply(lambda x: "⛔ TRAVADO" if project_has_gap(x) else "OK")
            d['status_icon'] = d['status'].apply(lambda x: "🔥" if x == "Em Risco" else "🟢")
            
            # Mostra a tabela (Adicionei a coluna de Alterações para visualização se quiser)
            d_display = d[['status_icon', 'gap_indicador', 'name', 'manager', 'status', 'end_date']].rename(columns={
                'status_icon': 'Sinal', 'gap_indicador': 'Impeditivo?', 'name': 'Nome do Projeto',
                'manager': 'Gerente', 'status': 'Status Atual', 'end_date': 'Entrega'
            })
            st.dataframe(d_display, hide_index=True, use_container_width=True)
            st.caption("Legenda: 🔥 = Risco de Prazo | ⛔ = Travado por Impeditivo (GAP)")
            
            st.divider()
            st.markdown("### ✏️ Editar Projeto")
            
            # Seleciona o projeto
            sel = st.selectbox("Selecione o Projeto para editar:", df_active['name'])
            
            if sel:
                # Pega os dados atuais do projeto (linha do banco)
                curr = df_active[df_active['name'] == sel].iloc[0]
                
                # Verifica quantas alterações já teve (se for nulo, assume 0)
                changes_count = curr['date_changes'] if 'date_changes' in curr and pd.notnull(curr['date_changes']) else 0
                
                with st.form("ed_p"):
                    # Aviso visual de quantas vezes mudou
                    if changes_count > 0:
                        st.warning(f"📅 Atenção: A data de entrega deste projeto já foi alterada **{int(changes_count)}** vezes.", icon="⚠️")
                    else:
                        st.info("📅 Este projeto mantém a data original.")

                    c1, c2 = st.columns(2)
                    with c1:
                        # CAMPO DE EDIÇÃO DO GERENTE (Livre)
                        new_manager = st.text_input("Gerente / Responsável", value=curr['manager'])
                        
                        # Campo Status
                        new_status = st.selectbox("Status", ["Em andamento", "Em Risco", "Concluído"], index=["Em andamento", "Em Risco", "Concluído"].index(curr['status']))
                    
                    with c2:
                        # CAMPO DE EDIÇÃO DA DATA
                        # Converte a string do banco para data do python para o calendário funcionar
                        current_date_obj = pd.to_datetime(curr['end_date']).date()
                        new_end_date = st.date_input("Data de Entrega", value=current_date_obj)
                        
                        # Checkbox Arquivar
                        arq = st.checkbox("Arquivar Projeto (Mover para Histórico)", value=bool(curr['archived']))

                    if st.form_submit_button("💾 Salvar Alterações"):
                        # --- LÓGICA DO CONTADOR ---
                        final_changes = int(changes_count)
                        
                        # Compara a data que estava no input com a data original
                        if str(new_end_date) != str(current_date_obj):
                            final_changes += 1 # Soma 1 se mudou
                            st.toast(f"Data alterada! Contador subiu para {final_changes}.", icon="📈")
                        
                        # Atualiza no Banco de Dados
                        db.execute_command(
                            "UPDATE projects SET manager=?, end_date=?, status=?, archived=?, date_changes=? WHERE id=?", 
                            (new_manager, new_end_date, new_status, 1 if arq else 0, final_changes, int(curr['id']))
                        )
                        st.success("Projeto atualizado com sucesso!")
                        st.rerun()
                        
    with t2:
        with st.form("nw_p", clear_on_submit=True):
            nm = st.text_input("Nome do Projeto")
            mg = st.text_input("Gerente do Projeto")
            sp = st.selectbox("Área / Sponsor", LISTA_AREAS)
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Início")
            d2 = c2.date_input("Fim")
            if st.form_submit_button("Criar Projeto"):
                if nm:
                    # Inserindo com date_changes = 0
                    db.execute_command("INSERT INTO projects (name, manager, sponsor, start_date, end_date, status, date_changes, archived) VALUES (?,?,?,?,?,?,0,0)", (nm, mg, sp, d1, d2, "Backlog"))
                    st.success(f"✅ Projeto '{nm}' criado com sucesso!")
                else:
                    st.warning("⚠️ Nome do projeto obrigatório.")
