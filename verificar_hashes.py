import hashlib
import json

def hash_password(password: str) -> str:
    """Gera hash SHA-256 da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

print("=" * 70)
print("🔐 VERIFICAÇÃO DE HASHES DE SENHA")
print("=" * 70)

# Senhas padrão
senhas = {
    "13234075964": "Lucas123@@",
    "00742712966": "Ricardo123@@"
}

print("\n📋 HASHES GERADOS:\n")

hashes_sql = []
for username, senha in senhas.items():
    hash_gerado = hash_password(senha)
    print(f"👤 {username.upper()}")
    print(f"   Senha: {senha}")
    print(f"   Hash:  {hash_gerado}")
    print()
    
    hashes_sql.append(f"('{username}', '{hash_gerado}', '{username.title()} Sistema', '{username}@sistema.com')")

print("=" * 70)
print("📝 SQL PARA INSERIR NO SUPABASE:")
print("=" * 70)
print()
print("INSERT INTO users (username, password_hash, nome, email) VALUES")
print(",\n".join(hashes_sql))
print("ON CONFLICT (username) DO NOTHING;")
print()
print("=" * 70)

# Verificar se existe users.json local
try:
    with open('users.json', 'r') as f:
        users_json = json.load(f)
    
    print("\n🔍 COMPARAÇÃO COM users.json EXISTENTE:")
    print("=" * 70)
    
    for username in senhas.keys():
        if username in users_json:
            hash_json = users_json[username]['password']
            hash_esperado = hash_password(senhas[username])
            
            match = "✅ MATCH" if hash_json == hash_esperado else "❌ DIFERENTE"
            print(f"\n{username}:")
            print(f"  JSON:     {hash_json}")
            print(f"  Esperado: {hash_esperado}")
            print(f"  Status:   {match}")
    
    print("\n" + "=" * 70)

except FileNotFoundError:
    print("\n⚠️ Arquivo users.json não encontrado (normal se já foi removido)")
except Exception as e:
    print(f"\n⚠️ Erro ao ler users.json: {e}")

print("\n✅ Script concluído!")
print("💡 Se os hashes estão corretos, execute o SQL acima no Supabase.")