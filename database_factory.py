import streamlit as st
import os

def get_database():
    """
    Retorna a instância correta do banco de dados:
    - PostgreSQL em produção (Streamlit Cloud)
    - SQLite em desenvolvimento local
    """
    
    # Verificar se está em produção (tem secrets do PostgreSQL)
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets and 'url' in st.secrets['database']:
            print("🐘 Usando PostgreSQL (Produção)")
            from database_postgres import DatabasePostgres
            return DatabasePostgres()
    except Exception as e:
        print(f"Aviso: Secrets não encontrados - {e}")
    
    # Fallback para SQLite (desenvolvimento local)
    print("💾 Usando SQLite (Desenvolvimento)")
    from database import Database
    return Database()


def is_using_postgres():
    """Verifica se está usando PostgreSQL"""
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            return True
    except Exception:
        pass
    return False