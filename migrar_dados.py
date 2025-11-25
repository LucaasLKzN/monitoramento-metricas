from database import Database  # SQLite
from database_postgres import DatabasePostgres
import pandas as pd

# Conectar nos dois bancos
sqlite_db = Database()
postgres_db = DatabasePostgres("postgresql://postgres:QhSiZGoJuqPKaeC8@db.jcdmwhuffwjvnsooqfwf.supabase.co:5432/postgres")

# Exportar do SQLite
print("📤 Exportando dados do SQLite...")
dados = sqlite_db.get_dados_completos()
print(f"Total de registros: {len(dados)}")

# Salvar temporariamente
dados.to_csv('temp_migracao.csv', index=False)

# Importar para PostgreSQL
print("📥 Importando para PostgreSQL...")
resultado = postgres_db.import_from_csv('temp_migracao.csv')

if resultado['sucesso']:
    print(f"✅ Migração concluída!")
    print(f"Registros migrados: {resultado['registros_importados']}")
else:
    print(f"❌ Erro: {resultado['erro']}")