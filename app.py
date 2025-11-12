import streamlit as st
import hashlib
import json
from datetime import datetime, timedelta
import time

class Auth:
    def __init__(self, users_file: str = "users.json"):
        """Inicializa o sistema de autenticação"""
        self.users_file = users_file
        self.init_users()
        self.init_session()
    
    def init_session(self):
        """Inicializa as variáveis de sessão"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'user_nome' not in st.session_state:
            st.session_state.user_nome = None
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
    
    def hash_password(self, password: str) -> str:
        """Criptografa a senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_users(self):
        """Inicializa usuários padrão se não existirem"""
        # Tentar carregar do Streamlit Secrets primeiro (para produção)
        try:
            if hasattr(st, 'secrets') and 'users' in st.secrets:
                # Usar usuários do Streamlit Secrets
                return
        except Exception:
            pass
        
        # Se não tiver secrets, usar arquivo local
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
        except FileNotFoundError:
            # Criar usuários padrão
            users = {
                "admin": {
                    "password": self.hash_password("admin123"),
                    "nome": "Administrador",
                    "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "usuario": {
                    "password": self.hash_password("user123"),
                    "nome": "Usuário Padrão",
                    "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=4)
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Verifica se as credenciais estão corretas"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            if username in users:
                hashed_password = self.hash_password(password)
                return users[username]["password"] == hashed_password
            return False
        except Exception as e:
            print(f"Erro ao verificar credenciais: {e}")
            return False
    
    def get_user_info(self, username: str) -> dict:
        """Retorna informações do usuário"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            if username in users:
                return {
                    "username": username,
                    "nome": users[username].get("nome", username),
                    "criado_em": users[username].get("criado_em", "N/A")
                }
            return None
        except Exception as e:
            print(f"Erro ao obter info do usuário: {e}")
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
            st.session_state.user_nome = user_info['nome'] if user_info else username
            st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return True
        return False
    
    def logout(self):
        """Realiza o logout do usuário"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_nome = None
        st.session_state.login_time = None
        st.session_state.session_id = None
    
    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado"""
        return st.session_state.get('authenticated', False)
    
    def require_auth(self):
        """Decorator/função que requer autenticação"""
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
        col1, col2, col3 = st.columns([1, 2, 1])
        
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
                        if self.login(username, password):
                            st.success("✅ Login realizado com sucesso!")
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
                st.markdown(f"🕒 **Login:** {st.session_state.get('login_time', 'N/A')}")
                
                if st.button("🚪 Sair", use_container_width=True):
                    self.logout()
                    st.rerun()
    
    def change_password(self, username: str, old_password: str, new_password: str) -> tuple:
        """Altera a senha do usuário"""
        try:
            # Verificar senha antiga
            if not self.verify_credentials(username, old_password):
                return False, "Senha atual incorreta!"
            
            # Carregar usuários
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            # Atualizar senha
            users[username]["password"] = self.hash_password(new_password)
            users[username]["senha_alterada_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Salvar
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=4)
            
            return True, "Senha alterada com sucesso!"
        
        except Exception as e:
            return False, f"Erro ao alterar senha: {str(e)}"