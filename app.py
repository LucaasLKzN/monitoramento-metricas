import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import Database
from auth import Auth

# Configuração da página
st.set_page_config(
    page_title="Sistema de Monitoramento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session_state se não existir
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_nome' not in st.session_state:
    st.session_state.user_nome = None
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

# Inicializar autenticação
auth = Auth()

# Verificar autenticação - SE NÃO ESTIVER LOGADO, MOSTRA LOGIN E PARA
if not auth.is_authenticated():
    auth.show_login_page()
    st.stop()

# SE CHEGOU AQUI, ESTÁ AUTENTICADO! Continua o app normal...

# Inicializar banco de dados (sem cache para sempre pegar dados atualizados)
def init_database():
    return Database()

db = init_database()

# Título principal
st.title("📊 Sistema de Monitoramento de Métricas")
st.markdown("---")

# Sidebar - Menu lateral
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Mostrar info do usuário
    auth.show_user_info_sidebar()
    
    st.markdown("---")
    
    menu = st.radio(
        "Navegação",
        ["📈 Dashboard", "📥 Importar Dados", "📋 Dados Completos", "🔧 Configurações", "🔑 Alterar Senha"]
    )
    
    st.markdown("---")
    
    # Filtros de data
    st.subheader("🗓️ Filtro de Período")
    
    # Obter intervalo de datas disponíveis
    resumo_geral = db.get_resumo_geral()
    
    if resumo_geral['total_registros'] > 0:
        dados = db.get_dados_completos()
        data_min = pd.to_datetime(dados['data'], format='%Y-%m-%d').min().date()
        data_max = pd.to_datetime(dados['data'], format='%Y-%m-%d').max().date()
        
        # Calcular data inicial (7 dias atrás por padrão, mas não antes da data mínima)
        data_inicial_sugerida = data_max - timedelta(days=7)
        if data_inicial_sugerida < data_min:
            data_inicial_sugerida = data_min
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input(
                "Data Início",
                value=data_inicial_sugerida,
                min_value=data_min,
                max_value=data_max,
                key="data_inicio_filter"
            )
        with col2:
            data_fim = st.date_input(
                "Data Fim",
                value=data_max,
                min_value=data_min,
                max_value=data_max,
                key="data_fim_filter"
            )
    else:
        st.info("Importe dados para usar os filtros")
        data_inicio = datetime.now().date()
        data_fim = datetime.now().date()

# =======================
# PÁGINA: DASHBOARD
# =======================
if menu == "📈 Dashboard":
    if resumo_geral['total_registros'] == 0:
        st.warning("⚠️ Nenhum dado encontrado. Importe dados pela aba 'Importar Dados'")
        st.stop()
    
    # Obter resumo do período selecionado
    resumo_periodo = db.get_resumo_geral(str(data_inicio), str(data_fim))
    
    st.header(f"📊 Dashboard - Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    # Cards com métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Registros",
            f"{resumo_periodo['total_registros']:,}".replace(',', '.')
        )
    
    with col2:
        st.metric(
            "Total Liberado",
            f"R$ {resumo_periodo['total_liberado']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    
    with col3:
        st.metric(
            "Média por Registro",
            f"R$ {resumo_periodo['media_liberado']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    
    with col4:
        st.metric(
            "Promotoras Ativas",
            resumo_periodo['total_promotoras']
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Evolução Temporal")
        df_periodo = db.get_totais_por_periodo(str(data_inicio), str(data_fim))
        
        if not df_periodo.empty:
            df_periodo['data'] = pd.to_datetime(df_periodo['data'])
            
            fig = px.line(
                df_periodo,
                x='data',
                y='total_liberado',
                title='Total Liberado por Dia',
                labels={'data': 'Data', 'total_liberado': 'Valor Liberado (R$)'}
            )
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para o período selecionado")
    
    with col2:
        st.subheader("👥 Top Promotoras")
        df_promotoras = db.get_totais_por_promotora(str(data_inicio), str(data_fim))
        
        if not df_promotoras.empty:
            # Pegar top 10
            df_top = df_promotoras.head(10)
            
            fig = px.bar(
                df_top,
                x='total_liberado',
                y='promotora',
                orientation='h',
                title='Top 10 Promotoras por Valor Total',
                labels={'total_liberado': 'Valor Total (R$)', 'promotora': 'Promotora'}
            )
            fig.update_traces(marker_color='#2ca02c')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para o período selecionado")
    
    st.markdown("---")
    
    # Tabelas detalhadas
    tab1, tab2 = st.tabs(["📊 Por Promotora", "📅 Por Período"])
    
    with tab1:
        st.subheader("Resumo por Promotora")
        df_promotoras = db.get_totais_por_promotora(str(data_inicio), str(data_fim))
        
        if not df_promotoras.empty:
            # Formatar valores
            df_display = df_promotoras.copy()
            df_display['total_liberado'] = df_display['total_liberado'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
            df_display['media_liberado'] = df_display['media_liberado'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
            df_display.columns = ['Promotora', 'Quantidade', 'Total Liberado', 'Média']
            
            st.dataframe(df_display, use_container_width=True, height=400)
            
            # Botão de download
            csv = df_promotoras.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar Relatório (CSV)",
                data=csv,
                file_name=f"relatorio_promotoras_{data_inicio}_{data_fim}.csv",
                mime="text/csv"
            )
        else:
            st.info("Sem dados para o período selecionado")
    
    with tab2:
        st.subheader("Resumo por Data")
        df_periodo = db.get_totais_por_periodo(str(data_inicio), str(data_fim))
        
        if not df_periodo.empty:
            # Formatar valores
            df_display = df_periodo.copy()
            df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
            df_display['total_liberado'] = df_display['total_liberado'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
            df_display.columns = ['Data', 'Quantidade', 'Total Liberado']
            
            st.dataframe(df_display, use_container_width=True, height=400)
            
            # Botão de download
            csv = df_periodo.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar Relatório (CSV)",
                data=csv,
                file_name=f"relatorio_periodo_{data_inicio}_{data_fim}.csv",
                mime="text/csv"
            )
        else:
            st.info("Sem dados para o período selecionado")

# =======================
# PÁGINA: IMPORTAR DADOS
# =======================
elif menu == "📥 Importar Dados":
    st.header("📥 Importar Dados do Google Sheets")
    
    st.info("""
    ### 📝 Como importar:
    1. Abra seu Google Sheets
    2. Clique em **Arquivo > Fazer download > Valores separados por vírgula (.csv)**
    3. Faça upload do arquivo abaixo
    4. Certifique-se que o CSV contém as colunas: **DATA, PROMOTORA, VALOR LIBERADO, ID**
    """)
    
    uploaded_file = st.file_uploader(
        "Escolha o arquivo CSV exportado do Google Sheets",
        type=['csv']
    )
    
    if uploaded_file is not None:
        # Preview dos dados
        try:
            df_preview = pd.read_csv(uploaded_file)
            
            st.subheader("👁️ Preview dos Dados")
            st.dataframe(df_preview.head(10), use_container_width=True)
            
            st.info(f"📊 Total de linhas no arquivo: {len(df_preview):,}".replace(',', '.'))
            
            # Resetar ponteiro do arquivo
            uploaded_file.seek(0)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✅ Confirmar Importação", type="primary"):
                    with st.spinner("Importando dados..."):
                        # Salvar temporariamente
                        temp_path = "temp_upload.csv"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        # Importar para o banco
                        resultado = db.import_from_csv(temp_path)
                        
                        if resultado['sucesso']:
                            st.success(f"""
                            ✅ **Importação concluída com sucesso!**
                            
                            - Registros importados: {resultado['registros_importados']:,}
                            - Total no banco: {resultado['total_no_banco']:,}
                            """.replace(',', '.'))
                            st.balloons()
                            # Limpar cache e forçar recarga
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Erro na importação: {resultado['erro']}")
            
            with col2:
                if st.button("🔄 Resetar Banco"):
                    if st.checkbox("⚠️ Confirmo que quero APAGAR todos os dados"):
                        db.limpar_banco()
                        st.success("✅ Banco limpo com sucesso!")
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
    
    # Mostrar estatísticas do banco atual
    st.markdown("---")
    st.subheader("📊 Estatísticas do Banco Atual")
    
    resumo = db.get_resumo_geral()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Registros", f"{resumo['total_registros']:,}".replace(',', '.'))
    
    with col2:
        st.metric(
            "Total Liberado",
            f"R$ {resumo['total_liberado']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    
    with col3:
        st.metric("Promotoras Cadastradas", resumo['total_promotoras'])

# =======================
# PÁGINA: DADOS COMPLETOS
# =======================
elif menu == "📋 Dados Completos":
    st.header("📋 Visualização de Dados Completos")
    
    if resumo_geral['total_registros'] == 0:
        st.warning("⚠️ Nenhum dado encontrado.")
        st.stop()
    
    df_completo = db.get_dados_completos(str(data_inicio), str(data_fim))
    
    st.info(f"📊 Mostrando {len(df_completo):,} registros do período selecionado".replace(',', '.'))
    
    # Formatar para exibição
    df_display = df_completo.copy()
    df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
    df_display['valor_liberado'] = df_display['valor_liberado'].apply(
        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    )
    df_display.columns = ['Data', 'Promotora', 'Valor Liberado', 'ID']
    
    st.dataframe(df_display, use_container_width=True, height=600)
    
    # Download
    csv = df_completo.to_csv(index=False)
    st.download_button(
        label="⬇️ Baixar Dados Completos (CSV)",
        data=csv,
        file_name=f"dados_completos_{data_inicio}_{data_fim}.csv",
        mime="text/csv"
    )

# =======================
# PÁGINA: CONFIGURAÇÕES
# =======================
elif menu == "🔧 Configurações":
    st.header("🔧 Configurações do Sistema")
    
    st.subheader("📊 Informações do Banco")
    resumo = db.get_resumo_geral()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Estatísticas Gerais:**
        - Total de Registros: {resumo['total_registros']:,}
        - Total Liberado: R$ {resumo['total_liberado']:,.2f}
        - Promotoras: {resumo['total_promotoras']}
        """.replace(',', '.').replace('.', ',', 2))
    
    with col2:
        st.info(f"""
        **Valores:**
        - Mínimo: R$ {resumo['min_liberado']:,.2f}
        - Máximo: R$ {resumo['max_liberado']:,.2f}
        - Média: R$ {resumo['media_liberado']:,.2f}
        """.replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---")
    
    st.subheader("⚠️ Zona de Perigo")
    st.warning("As ações abaixo são irreversíveis. Use com cuidado!")
    
    # Criar um estado para controlar a confirmação
    if 'confirmar_limpar' not in st.session_state:
        st.session_state.confirmar_limpar = False
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpar Todos os Dados", type="secondary"):
            st.session_state.confirmar_limpar = True
    
    if st.session_state.confirmar_limpar:
        st.error("⚠️ ATENÇÃO: Esta ação irá apagar TODOS os dados permanentemente!")
        
        col_confirm, col_cancel = st.columns(2)
        
        with col_confirm:
            if st.button("✅ SIM, APAGAR TUDO", type="primary"):
                if db.limpar_banco():
                    st.success("✅ Banco limpo com sucesso!")
                    st.session_state.confirmar_limpar = False
                    st.rerun()
                else:
                    st.error("❌ Erro ao limpar banco")
        
        with col_cancel:
            if st.button("❌ Cancelar"):
                st.session_state.confirmar_limpar = False
                st.rerun()

# =======================
# PÁGINA: ALTERAR SENHA
# =======================
elif menu == "🔑 Alterar Senha":
    st.header("🔑 Alterar Senha")
    
    st.info("Por segurança, altere sua senha padrão!")
    
    with st.form("change_password_form"):
        senha_atual = st.text_input("🔒 Senha Atual", type="password")
        senha_nova = st.text_input("🔑 Nova Senha", type="password")
        senha_confirma = st.text_input("✅ Confirmar Nova Senha", type="password")
        
        submit = st.form_submit_button("💾 Alterar Senha", type="primary")
        
        if submit:
            if not senha_atual or not senha_nova or not senha_confirma:
                st.error("❌ Preencha todos os campos!")
            elif senha_nova != senha_confirma:
                st.error("❌ As senhas não coincidem!")
            elif len(senha_nova) < 6:
                st.error("❌ A senha deve ter no mínimo 6 caracteres!")
            else:
                username = st.session_state.get('username')
                sucesso, mensagem = auth.change_password(username, senha_atual, senha_nova)
                
                if sucesso:
                    st.success(f"✅ {mensagem}")
                    st.balloons()
                else:
                    st.error(f"❌ {mensagem}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Sistema de Monitoramento de Métricas v1.0 | Desenvolvido para otimização de análise de dados</small>
</div>
""", unsafe_allow_html=True)