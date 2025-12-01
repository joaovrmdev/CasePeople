import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Analytics de POs", layout="wide")

# --- FUNÇÕES DE CARREGAMENTO E TRATAMENTO DE DADOS ---
@st.cache_data
def load_data():
    # Adendo: Estou fazendo a inserção direta dos arquivos csvs, apenas porque para esse case 
    # nao precisamos de um data lake nem nada tão sofisticado, mas eu poderia ter anonimizado ainda mais esses dados adotando o snowflake, por exemplo
    try:
        df_avaliacao = pd.read_csv('case_assessmentAnalytics_vsAbr2024.xlsx - Base_Avaliacao.csv')
        df_necessidade = pd.read_csv('case_assessmentAnalytics_vsAbr2024.xlsx - Nivel_de_necessidade_po.csv')
    except FileNotFoundError:
        st.error("Arquivos CSV não encontrados. Por favor, verifique os nomes e o diretório.")
        return None, None

    # Limpeza dos nomes das colunas (removendo espaços extras)
    df_avaliacao.columns = df_avaliacao.columns.str.strip()
    df_necessidade.columns = df_necessidade.columns.str.strip()
    
    return df_avaliacao, df_necessidade

@st.cache_data
def process_data(df_avaliacao, df_necessidade):
    # 1. Filtrar apenas para POs
    df_po = df_avaliacao[df_avaliacao['Papel_comunidade'] == 'PO'].copy()
    
    # 2. Pegando as skills (estão entre colchetes [])
    skill_cols = [c for c in df_po.columns if '[' in c and ']' in c]
    
    # 3. Tratamento de Avaliações Múltiplas (Funcional vs Matricial) -> Como não queria selecionar pesos,
    # fiz uma abordagem simples com media simetrica, ou seja, os dois casos tiveram peso igual
    df_po_agg = df_po.groupby(
        ['Nome do colaborador avaliado', 'ESPECIALIDADE_avaliado']
    )[skill_cols].mean().reset_index()
    
    # 4. Preparar tabela de necessidades (Meta)
    df_necessidade_po = df_necessidade[df_necessidade['PAPEL'] == 'PO'].copy()
    
    # 5. Cruzamento (Merge) dos dados Reais vs Meta
    merged_df = pd.merge(
        df_po_agg,
        df_necessidade_po,
        left_on='ESPECIALIDADE_avaliado',
        right_on='ESPECIALIDADE',
        suffixes=('_actual', '_target')
    )
    
    # 6. Cálculo de Gaps (Real - Meta)
    gap_cols = []
    for col in skill_cols:
        actual_col = f"{col}_actual"
        target_col = f"{col}_target"
        gap_col = f"{col}_gap"
        # Gap negativo significa que precisa de treinamento
        merged_df[gap_col] = merged_df[actual_col] - merged_df[target_col]
        gap_cols.append(gap_col)
        
    return merged_df, skill_cols, gap_cols

# --- CARREGAR DADOS ---
df_aval, df_nec = load_data()

if df_aval is not None:
    df_final, skills, gaps = process_data(df_aval, df_nec)

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros")
    especialidades = ['Todas'] + list(df_final['ESPECIALIDADE_avaliado'].unique())
    filtro_especialidade = st.sidebar.selectbox("Selecione a Especialidade:", especialidades)

    if filtro_especialidade != 'Todas':
        df_view = df_final[df_final['ESPECIALIDADE_avaliado'] == filtro_especialidade]
    else:
        df_view = df_final

    # --- HEADER ---
    st.title("Diagnóstico de Skills: Product Owners")
    st.markdown("### Análise de Prontidão para a Transformação Digital")
    st.markdown("---")

    # --- KPI GERAL (PERGUNTA 1) ---
    # Definição de Apto: Não possui nenhum gap negativo em nenhuma skill
    df_view['is_fit'] = df_view[gaps].min(axis=1) >= 0
    pct_fit = df_view['is_fit'].mean() * 100
    total_pos = len(df_view)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de POs Analisados", total_pos)
    col2.metric("POs Aptos (Sem Gaps)", f"{pct_fit:.1f}%", delta_color="normal")
    col3.metric("POs com Necessidade de Treinamento", f"{100-pct_fit:.1f}%", delta_color="inverse")

    st.caption("*Critério de Aptidão: O colaborador atende ou supera o nível exigido em TODAS as competências.*")

    st.markdown("---")

    # --- ANÁLISE DE GAPS ---
    st.subheader("Onde estão os maiores problemas?")
    
    gap_counts = (df_view[gaps] < 0).sum().reset_index()
    gap_counts.columns = ['Skill_Gap', 'Count']
    gap_counts['Skill'] = gap_counts['Skill_Gap'].str.replace('_gap', '')
    gap_counts['Percent'] = (gap_counts['Count'] / total_pos) * 100
    gap_counts = gap_counts.sort_values('Percent', ascending=True)

    # Gráfico de Barras Horizontal
    fig_bar = px.bar(
        gap_counts, 
        x='Percent', 
        y='Skill', 
        orientation='h',
        title="Percentual de POs abaixo do nível esperado por Competência",
        text=gap_counts['Percent'].apply(lambda x: f'{x:.1f}%'),
        color='Percent',
        color_continuous_scale='Reds'
    )
    fig_bar.update_layout(xaxis_title="% de Colaboradores com Gap", yaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- ANÁLISE DETALHADA (RADAR CHART) ---
    st.subheader("Perfil Atual vs. Esperado (Média)")
    
    col_radar1, col_radar2 = st.columns([2, 1])
    
    with col_radar1:
        avg_actual = df_view[[s + '_actual' for s in skills]].mean()
        avg_target = df_view[[s + '_target' for s in skills]].mean()
        
        categories = skills
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_actual.values,
            theta=categories,
            fill='toself',
            name='Nível Atual (Média)',
            line_color='blue'
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_target.values,
            theta=categories,
            fill='toself',
            name='Nível Esperado (Meta)',
            line_color='gray',
            opacity=0.4
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            showlegend=True,
            title="Comparativo: Competências Reais vs Exigidas"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_radar2:
        st.info("**Insight Rápido:**")
        avg_gaps = df_view[gaps].mean()
        worst_skill_gap = avg_gaps.idxmin()
        worst_skill_name = worst_skill_gap.replace('_gap', '')
        worst_gap_val = avg_gaps.min()
        
        st.markdown(f"A competência mais crítica é **{worst_skill_name}**.")
        st.markdown(f"Em média, os POs estão **{abs(worst_gap_val):.2f} pontos** abaixo do esperado nesta skill.")

    st.markdown("---")

    # PRIORIZAÇÃO (ONDE ATUAR PRIMEIRO)

    st.subheader("Matriz de Priorização: Onde atuar primeiro?")
    st.markdown("""
    Esta visão cruza **Alcance** (quantas pessoas precisam) x **Severidade** (tamanho do gap).
    Os pontos no canto superior direito são as prioridades imediatas.
    """)

    # Preparar dados para o Scatter Plot
    summary_data = []
    for i, skill in enumerate(skills):
        gap_col = gaps[i]
        # Consideramos gap apenas quem está NEGATIVO
        below_target = df_view[df_view[gap_col] < 0]
        count = len(below_target)
        # Severidade: Gap médio apenas de quem tem gap (para não diluir com quem está bem)
        avg_gap_val = below_target[gap_col].mean() if count > 0 else 0
        
        summary_data.append({
            'Skill': skill,
            'Afetados (%)': (count / total_pos) * 100,
            'Severidade Média': abs(avg_gap_val) # Adoção para ter o gráfico positivo
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    col_matrix_1, col_matrix_2 = st.columns([3, 1])

    with col_matrix_1:
        fig_scatter = px.scatter(
            df_summary,
            x='Afetados (%)',
            y='Severidade Média',
            text='Skill',
            size='Afetados (%)',
            color='Severidade Média',
            color_continuous_scale='Reds',
            title="Priorização de Treinamentos (Canto Superior Direito = Crítico)"
        )
        # Linhas de quadrante para facilitar leitura
        fig_scatter.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
        fig_scatter.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig_scatter.update_traces(textposition='top center')
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_matrix_2:
        # Pega a skill com maior combinação de severidade e alcance
        priority_skill = df_summary.sort_values(by=['Afetados (%)', 'Severidade Média'], ascending=False).iloc[0]
        st.warning(f"**Prioridade #1:**\n\n {priority_skill['Skill']}")
        st.markdown(f"Impacta **{priority_skill['Afetados (%)']:.0f}%** do time.")
        st.markdown("Recomendação: Treinamento obrigatório de curto prazo.")

    st.markdown("---")

    # TOP TALENTS (MENTORES)
    
    st.subheader("Top Talents: Potenciais Mentores")
    st.markdown("Estes colaboradores atingiram todos os critérios de excelência para a função. Eles podem atuar como multiplicadores de conhecimento.")

    # Filtra quem tem alto desempenho (fit)
    top_talents = df_view[df_view['is_fit'] == True][['Nome do colaborador avaliado', 'ESPECIALIDADE_avaliado']]

    if not top_talents.empty:
        col_talents_1, col_talents_2 = st.columns([1, 2])
        with col_talents_1:
            st.metric("Total de Mentores", len(top_talents))
        with col_talents_2:
            st.dataframe(top_talents, hide_index=True, use_container_width=True)
    else:
        st.warning("Nenhum colaborador nesta seleção atende 100% dos requisitos atualmente.")

    st.markdown("---")

    with st.expander("Ver base de dados completa para análise"):
        st.dataframe(df_view.style.format("{:.1f}", subset=[c for c in df_view.columns if 'actual' in c or 'gap' in c]))