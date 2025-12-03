import streamlit as st
import os

def get_database():
    """
    Retorna a instância correta do banco de dados:
    - PostgreSQL/Supabase em produção (Streamlit Cloud)
    - SQLite em desenvolvimento local
    """

    print("\n" + "="*60)
    print("🔍 INICIANDO DATABASE FACTORY")
    print("="*60)

    # Verificação se está em produção
    try:
        print("📋 Verificando se st.secrets existe...")
        
        # Verificar se secrets existe
        if not hasattr(st, 'secrets'):
            print("❌ st.secrets NÃO existe")
            print("💾 Usando SQLite (Desenvolvimento Local)")
            print("="*60 + "\n")
            from database import Database
            return Database()
        
        print("✅ st.secrets existe")
        
        # Listar todas as chaves disponíveis nos secrets
        try:
            keys = list(st.secrets.keys())
            print(f"📋 Chaves disponíveis no secrets: {keys}")
        except Exception as e:
            print(f"⚠️ Erro ao listar chaves: {e}")
        
        # Variável para armazenar a URL encontrada
        db_url = None
        
        # Tentar encontrar URL em 'database'
        if 'database' in st.secrets:
            print("✅ Chave 'database' encontrada nos secrets")
            
            try:
                db_keys = list(st.secrets['database'].keys())
                print(f"   📋 Subchaves em 'database': {db_keys}")
            except Exception as e:
                print(f"   ⚠️ Erro ao listar subchaves: {e}")
            
            if 'url' in st.secrets['database']:
                db_url = st.secrets['database']['url']
                # Mostrar apenas os primeiros 30 caracteres por segurança
                print(f"   ✅ URL encontrada em database.url: {db_url[:30]}...")
                print("🐘 Usando PostgreSQL/Supabase (Produção - database)")
                print("="*60 + "\n")
                from database_postgres import DatabasePostgres
                return DatabasePostgres()
            else:
                print("   ❌ 'url' NÃO encontrada dentro de 'database'")
        else:
            print("❌ Chave 'database' NÃO encontrada nos secrets")
        
        # Tentar encontrar URL em 'supabase'
        if 'supabase' in st.secrets:
            print("✅ Chave 'supabase' encontrada nos secrets")
            
            try:
                supa_keys = list(st.secrets['supabase'].keys())
                print(f"   📋 Subchaves em 'supabase': {supa_keys}")
            except Exception as e:
                print(f"   ⚠️ Erro ao listar subchaves: {e}")
            
            if 'url' in st.secrets['supabase']:
                db_url = st.secrets['supabase']['url']
                print(f"   ✅ URL encontrada em supabase.url: {db_url[:30]}...")
                print("🐘 Usando PostgreSQL/Supabase (Produção - supabase)")
                print("="*60 + "\n")
                from database_postgres import DatabasePostgres
                return DatabasePostgres()
            else:
                print("   ❌ 'url' NÃO encontrada dentro de 'supabase'")
        else:
            print("❌ Chave 'supabase' NÃO encontrada nos secrets")
        
        # Se chegou aqui, tem secrets mas não encontrou URL
        print("⚠️ Secrets existem mas URL do banco NÃO foi encontrada")
        print("   Estrutura esperada:")
        print("   [database]")
        print("   url = \"postgresql://...\"")
        print("   OU")
        print("   [supabase]")
        print("   url = \"postgresql://...\"")
        
    except Exception as e:
        print(f"⚠️ Exceção ao verificar secrets: {e}")
        import traceback
        print("📋 Traceback completo:")
        traceback.print_exc()

    # Fallback para SQLite (Dev local)
    print("💾 Usando SQLite (Desenvolvimento Local)")
    print("="*60 + "\n")
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

def debug_secrets_info():
    """
    Função auxiliar para debugar secrets
    Retorna informações formatadas sobre os secrets
    """
    info = []
    
    if not hasattr(st, 'secrets'):
        info.append("❌ st.secrets não existe")
        return "\n".join(info)
    
    info.append("✅ st.secrets existe")
    
    try:
        keys = list(st.secrets.keys())
        info.append(f"📋 Chaves principais: {keys}")
        
        if 'database' in st.secrets:
            try:
                db_keys = list(st.secrets['database'].keys())
                info.append(f"✅ database encontrado")
                info.append(f"   Subchaves: {db_keys}")
                
                if 'url' in st.secrets['database']:
                    url = st.secrets['database']['url']
                    info.append(f"   ✅ URL: {url[:30]}...")
                else:
                    info.append(f"   ❌ 'url' não encontrada")
            except Exception as e:
                info.append(f"   ❌ Erro: {e}")
        else:
            info.append("❌ 'database' não encontrado")
        
        if 'supabase' in st.secrets:
            try:
                supa_keys = list(st.secrets['supabase'].keys())
                info.append(f"✅ supabase encontrado")
                info.append(f"   Subchaves: {supa_keys}")
                
                if 'url' in st.secrets['supabase']:
                    url = st.secrets['supabase']['url']
                    info.append(f"   ✅ URL: {url[:30]}...")
                else:
                    info.append(f"   ❌ 'url' não encontrada")
            except Exception as e:
                info.append(f"   ❌ Erro: {e}")
        else:
            info.append("❌ 'supabase' não encontrado")
            
    except Exception as e:
        info.append(f"❌ Erro geral: {e}")
    
    return "\n".join(info)