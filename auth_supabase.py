import streamlit as st
import hashlib
import psycopg2
from psycopg2.extensions import parse_dsn
from datetime import datetime
import time

class AuthSupabase:
    def __init__(self):
        """Inicializa o sistema de autenticação com Supabase"""
        self.db_url = self._get_db_url_from_secrets()
        if not self.db_url:
            st.error("❌ Configuração do banco não encontrada!")
            st.stop()
        self.init_session()
    
    def _get_db_url_from_secrets(self) -> str:
        """Obtém URL do banco dos secrets do Streamlit"""
        try:
            if hasattr(st, 'secrets'):
                if 'database' in st.secrets and 'url' in st.secrets['database']:
                    return st.secrets['database']['url']
                
                if 'supabase' in st.secrets and 'url' in st.secrets['supabase']:
                    return st.secrets['supabase']['url']
        except Exception as e:
            print(f"❌ Erro ao ler secrets: {e}")
        return None
    
    def get_connection(self):
        """Cria conexão com o banco"""
        try:
            conn_params = parse_dsn(self.db_url)
            conn_params.update({
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            })
            return psycopg2.connect(**conn_params)
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco: {e}")
            raise
    
    def init_session(self):
        """Inicializa as variáveis de sessão"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'user_nome' not in st.session_state:
            st.session_state.user_nome = None
        if 'user_email' not in st.session_state:
            st.session_state.user_email = None
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
    
    def hash_password(self, password: str) -> str:
        """Criptografa a senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Verifica se as credenciais estão corretas no Supabase"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            hashed_password = self.hash_password(password)
            
            cursor.execute("""
                SELECT username, password_hash, nome, email, ativo 
                FROM users 
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                db_username, db_hash, db_nome, db_email, db_ativo = result
                
                # Verificar se usuário está ativo
                if not db_ativo:
                    print(f"⚠️ Usuário {username} está inativo")
                    return False
                
                # Verificar senha
                if db_hash == hashed_password:
                    # Atualizar último acesso
                    self._update_last_access(username)
                    return True
            
            return False
        
        except Exception as e:
            print(f"❌ Erro ao verificar credenciais: {e}")
            return False
    
    def _update_last_access(self, username: str):
        """Atualiza o timestamp do último acesso"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET ultimo_acesso = CURRENT_TIMESTAMP
                WHERE username = %s
            """, (username,))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Erro ao atualizar último acesso: {e}")
    
    def get_user_info(self, username: str) -> dict:
        """Retorna informações do usuário do Supabase"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username, nome, email, criado_em, senha_alterada_em, ultimo_acesso
                FROM users
                WHERE username = %s AND ativo = TRUE
            """, (username,))
            
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return {
                    "username": result[0],
                    "nome": result[1],
                    "email": result[2] or "N/A",
                    "criado_em": result[3].strftime("%Y-%m-%d %H:%M:%S") if result[3] else "N/A",
                    "senha_alterada_em": result[4].strftime("%Y-%m-%d %H:%M:%S") if result[4] else None,
                    "ultimo_acesso": result[5].strftime("%Y-%m-%d %H:%M:%S") if result[5] else None
                }
            
            return None
        
        except Exception as e:
            print(f"❌ Erro ao obter info do usuário: {e}")
            return None
    
    def login(self, username: str, password: str) -> bool:
        """Realiza o login do usuário"""
        if self.verify_credentials(username, password):
            # Criar session_id único
            session_id = hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()
            
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.session_id = session_id
            
            user_info = self.get_user_info(username)
            if user_info:
                st.session_state.user_nome = user_info['nome']
                st.session_state.user_email = user_info['email']
            else:
                st.session_state.user_nome = username
                st.session_state.user_email = "N/A"
            
            st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return True
        return False
    
    def logout(self):
        """Realiza o logout do usuário"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_nome = None
        st.session_state.user_email = None
        st.session_state.login_time = None
        st.session_state.session_id = None
    
    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado"""
        return st.session_state.get('authenticated', False)
    
    def require_auth(self):
        """Função que requer autenticação"""
        if not self.is_authenticated():
            self.show_login_page()
            st.stop()
    
    def show_login_page(self):
        """Exibe a página de login"""
        st.markdown("""
            <style>
            .login-container {
                max-width: 400px;
                margin: 100px auto;
                padding: 2rem;
                border-radius: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }
            .login-title {
                color: white;
                text-align: center;
                font-size: 2rem;
                margin-bottom: 2rem;
                font-weight: bold;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Container centralizado
        col1, col2, col3 = st.columns([1, 0.6, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<div class="login-title">🔐 Login</div>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Usuário", key="login_username")
                password = st.text_input("🔑 Senha", type="password", key="login_password")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    submit = st.form_submit_button("🚀 Entrar", use_container_width=True)
                
                with col_btn2:
                    show_info = st.form_submit_button("ℹ️ Info", use_container_width=True)
                
                if submit:
                    if username and password:
                        with st.spinner("Verificando credenciais..."):
                            if self.login(username, password):
                                st.success("✅ Login realizado com sucesso!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Usuário ou senha incorretos!")
                    else:
                        st.warning("⚠️ Preencha todos os campos!")
                
                if show_info:
                    st.info("""
                    **👥 Usuários Padrão:**
                    
                    **Admin:**
                    - Usuário: `admin`
                    - Senha: `admin123`
                    
                    **Usuário:**
                    - Usuário: `usuario`
                    - Senha: `user123`
                    
                    💡 *Altere as senhas após o primeiro acesso!*
                    """)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def show_user_info_sidebar(self):
        """Mostra informações do usuário na sidebar"""
        if self.is_authenticated():
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"👤 **Usuário:** {st.session_state.get('user_nome', 'N/A')}")
                st.markdown(f"🕐 **Login:** {st.session_state.get('login_time', 'N/A')}")
                
                if st.button("🚪 Sair", use_container_width=True):
                    self.logout()
                    st.rerun()
    
    def change_password(self, username: str, old_password: str, new_password: str) -> tuple:
        """Altera a senha do usuário no Supabase"""
        try:
            # Validações
            if len(new_password) < 6:
                return False, "A senha deve ter no mínimo 6 caracteres!"
            
            # Verificar senha antiga
            if not self.verify_credentials(username, old_password):
                return False, "Senha atual incorreta!"
            
            # Atualizar senha no banco
            conn = self.get_connection()
            cursor = conn.cursor()
            
            new_hash = self.hash_password(new_password)
            
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, 
                    senha_alterada_em = CURRENT_TIMESTAMP
                WHERE username = %s
            """, (new_hash, username))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True, "Senha alterada com sucesso!"
        
        except Exception as e:
            return False, f"Erro ao alterar senha: {str(e)}"
    
    def list_users(self) -> list:
        """Lista todos os usuários (admin apenas)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username, nome, email, ativo, criado_em, ultimo_acesso
                FROM users
                ORDER BY criado_em DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    "username": row[0],
                    "nome": row[1],
                    "email": row[2] or "N/A",
                    "ativo": row[3],
                    "criado_em": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else "N/A",
                    "ultimo_acesso": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else "Nunca"
                })
            
            cursor.close()
            conn.close()
            
            return users
        
        except Exception as e:
            print(f"❌ Erro ao listar usuários: {e}")
            return []