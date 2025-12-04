# 📊 Sistema de Monitoramento de Métricas

Sistema completo de monitoramento e análise de métricas com dashboard interativo.

## 🚀 Funcionalidades

- ✅ Dashboard interativo com gráficos dinâmicos
- ✅ Importação de dados via CSV
- ✅ Análises por período, promotora e produto
- ✅ Sistema de autenticação seguro
- ✅ Banco de dados PostgreSQL (Supabase)
- ✅ Deploy em Streamlit Cloud

## 🛠️ Tecnologias

- **Backend:** Python 3.12+
- **Framework:** Streamlit
- **Banco de Dados:** PostgreSQL (Supabase)
- **Visualização:** Plotly
- **Análise:** Pandas

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o Supabase

1. Crie uma conta em [Supabase](https://supabase.com)
2. Crie um novo projeto
3. Execute o script SQL de criação de tabelas (veja `docs/setup_database.sql`)
4. Copie a connection string do seu projeto

### 5. Configure os Secrets

Crie o arquivo `.streamlit/secrets.toml`:

```toml
[database]
url = "postgresql://postgres:SUA_SENHA@db.seu-projeto.supabase.co:5432/postgres"
```

**⚠️ IMPORTANTE:** Nunca commite o arquivo `secrets.toml`!

### 6. Execute o aplicativo

```bash
streamlit run app.py
```

## 🔐 Usuários Padrão

Após configurar o banco de dados, use:

- **Admin:**
  - Usuário: `admin`
  - Senha: `admin123`

- **Usuário:**
  - Usuário: `usuario`
  - Senha: `user123`

⚠️ **Altere as senhas após o primeiro acesso!**

## 📊 Estrutura do Projeto

```
projeto/
├── app.py                    # Aplicação principal
├── auth_supabase.py          # Sistema de autenticação
├── database_factory.py       # Factory pattern para banco
├── database_postgres.py      # Implementação PostgreSQL
├── database.py              # Implementação SQLite (dev)
├── requirements.txt         # Dependências
├── .gitignore              # Arquivos ignorados
└── .streamlit/
    └── secrets.toml        # Credenciais (NÃO COMMITAR)
```

## 🌐 Deploy no Streamlit Cloud

1. Faça push do código para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Configure os Secrets em **Settings → Secrets**
5. Cole o conteúdo do seu `secrets.toml`
6. Deploy!

## 🔒 Segurança

- ✅ Senhas armazenadas com hash SHA-256
- ✅ Secrets gerenciados via Streamlit Secrets
- ✅ Conexões seguras com SSL (Supabase)
- ✅ Validação de inputs
- ✅ Proteção contra SQL injection

## 📝 Licença

Este projeto está sob a licença MIT.

## 👨‍💻 Autor

Desenvolvido por AzDev

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## 📧 Suporte

Para dúvidas ou suporte, abra uma issue no GitHub.
