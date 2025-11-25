#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para PostgreSQL
"""

import sys
import pandas as pd
from database import Database
from database_postgres import DatabasePostgres

def migrar_dados(postgres_url: str):
    """Migra dados do SQLite local para PostgreSQL"""
    
    print("="*60)
    print("🔄 MIGRAÇÃO: SQLite → PostgreSQL")
    print("="*60)
    
    # Conectar SQLite
    print("\n1️⃣ Conectando ao SQLite...")
    try:
        sqlite_db = Database()
        print("✅ SQLite conectado!")
    except Exception as e:
        print(f"❌ Erro ao conectar SQLite: {e}")
        return False
    
    # Verificar dados no SQLite
    print("\n2️⃣ Verificando dados no SQLite...")
    try:
        resumo = sqlite_db.get_resumo_geral()
        total_registros = resumo['total_registros']
        
        if total_registros == 0:
            print("⚠️ Nenhum dado encontrado no SQLite!")
            return False
        
        print(f"✅ Encontrados {total_registros:,} registros".replace(',', '.'))
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")
        return False
    
    # Exportar dados
    print("\n3️⃣ Exportando dados do SQLite...")
    try:
        dados = sqlite_db.get_dados_completos()
        print(f"✅ {len(dados):,} registros exportados".replace(',', '.'))
        
        # Salvar temporariamente
        temp_file = 'temp_migracao.csv'
        dados.to_csv(temp_file, index=False)
        print(f"✅ Dados salvos em {temp_file}")
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
        return False
    
    # Conectar PostgreSQL
    print("\n4️⃣ Conectando ao PostgreSQL...")
    try:
        postgres_db = DatabasePostgres(postgres_url)
        print("✅ PostgreSQL conectado!")
    except Exception as e:
        print(f"❌ Erro ao conectar PostgreSQL: {e}")
        print("Verifique se a URL está correta:")
        print(f"  URL: {postgres_url[:50]}...")
        return False
    
    # Verificar se PostgreSQL está vazio
    print("\n5️⃣ Verificando PostgreSQL...")
    try:
        resumo_pg = postgres_db.get_resumo_geral()
        if resumo_pg['total_registros'] > 0:
            resposta = input(f"⚠️ PostgreSQL já tem {resumo_pg['total_registros']} registros. Continuar? (s/n): ")
            if resposta.lower() != 's':
                print("❌ Migração cancelada!")
                return False
    except Exception as e:
        print(f"⚠️ Aviso: {e}")
    
    # Importar para PostgreSQL
    print("\n6️⃣ Importando dados para PostgreSQL...")
    try:
        resultado = postgres_db.import_from_csv(temp_file)
        
        if resultado['sucesso']:
            print(f"✅ Migração concluída!")
            print(f"   - Registros importados: {resultado['registros_importados']:,}".replace(',', '.'))
            print(f"   - Total no PostgreSQL: {resultado['total_no_banco']:,}".replace(',', '.'))
        else:
            print(f"❌ Erro na importação: {resultado['erro']}")
            return False
    except Exception as e:
        print(f"❌ Erro ao importar: {e}")
        return False
    
    # Verificar migração
    print("\n7️⃣ Verificando migração...")
    try:
        resumo_final = postgres_db.get_resumo_geral()
        
        print("\n📊 Resumo Final:")
        print(f"   - Total de Registros: {resumo_final['total_registros']:,}".replace(',', '.'))
        print(f"   - Total Liberado: R$ {resumo_final['total_liberado']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        print(f"   - Promotoras: {resumo_final['total_promotoras']}")
        print(f"   - Produtos: {resumo_final['total_produtos']}")
        
        if resumo_final['total_registros'] == total_registros:
            print("\n✅ Migração verificada com sucesso!")
            print("   Todos os registros foram migrados corretamente!")
        else:
            print(f"\n⚠️ Atenção: Diferença de registros!")
            print(f"   SQLite: {total_registros}")
            print(f"   PostgreSQL: {resumo_final['total_registros']}")
    except Exception as e:
        print(f"❌ Erro ao verificar: {e}")
        return False
    
    print("\n" + "="*60)
    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*60)
    
    return True


def main():
    print("\n🐘 SCRIPT DE MIGRAÇÃO - SQLite → PostgreSQL\n")
    
    if len(sys.argv) < 2:
        print("❌ URL do PostgreSQL não fornecida!")
        print("\n📝 Uso:")
        print("  python migrar_sqlite_para_postgres.py 'postgresql://user:pass@host:port/db'")
        print("\n💡 Exemplo:")
        print("  python migrar_sqlite_para_postgres.py 'postgresql://postgres:senha123@localhost:5432/metricas'")
        sys.exit(1)
    
    postgres_url = sys.argv[1]
    
    # Confirmar
    print(f"📍 URL PostgreSQL: {postgres_url[:50]}...")
    resposta = input("\n⚠️ Deseja iniciar a migração? (s/n): ")
    
    if resposta.lower() != 's':
        print("❌ Migração cancelada!")
        sys.exit(0)
    
    # Executar migração
    sucesso = migrar_dados(postgres_url)
    
    if sucesso:
        print("\n✅ Próximos passos:")
        print("   1. Configure os Secrets no Streamlit Cloud")
        print("   2. Faça commit e push do código")
        print("   3. O app vai usar PostgreSQL automaticamente!")
        sys.exit(0)
    else:
        print("\n❌ Migração falhou!")
        sys.exit(1)


if __name__ == "__main__":
    main()