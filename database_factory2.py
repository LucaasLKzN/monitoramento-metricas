import streamlit as st
import os

def get_database():
    """
    Retorna a instância correta do banco de dados:
    - PostgreSQL/Supabase em produção (Streamlit Cloud)
    - SQLite em desenvolvimento local
    """

    # Verificação se está em produção
    try:
        # Tentar acessar os secrets
        if hasattr(st, 'secrets'):
            # Aceita tanto 'database' quanto 'supabase' como chave
            if 'database' in st.secrets and 'url' in st.secrets['database']:
                print("Usando PostgreSQL (Produção)")
                from database_postgres import DatabasePostgres
                return DatabasePostgres()
            elif 'supabase' in st.secrets and 'url' in st.secrets['supabase']:
                print(" Usando PostgreSQL (Produção)")
                from database_postgres import DatabasePostgres
                return DatabasePostgres()
    except Exception as e:
        print(f"Aviso: Secrets não encontrados - {e}")

    # Fallback para SQLite (Dev local)
    print ("Usando SQLite (Dev)")
    from database import Database
    return Database()

def usando_postgres():
    """
    Verifica se está usando PostgreSQL
    """

    try:
        if hasattr(st, 'secrets'):
            return('database' in st.secrets and 'url' in st.secrets['database']) or \
                  ('supabase' in st.secrets and 'url' in st.secrets['supabase'])  
    except Exception:
        pass
    return False

def get_db_type():
    """Retorna o tipo de banco sendo usado"""
    return "PostgreSQL/Supabase" if usando_postgres() else "SQLite"