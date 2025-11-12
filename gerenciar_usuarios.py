import json
import hashlib
from datetime import datetime

class UserManager:
    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
    
    def hash_password(self, password: str) -> str:
        """Criptografa a senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self) -> dict:
        """Carrega os usuários"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_users(self, users: dict):
        """Salva os usuários"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=4)
    
    def list_users(self):
        """Lista todos os usuários"""
        users = self.load_users()
        
        if not users:
            print("❌ Nenhum usuário cadastrado!")
            return
        
        print("\n" + "="*60)
        print("📋 USUÁRIOS CADASTRADOS")
        print("="*60)
        
        for username, info in users.items():
            print(f"\n👤 Usuário: {username}")
            print(f"   Nome: {info.get('nome', 'N/A')}")
            print(f"   Criado em: {info.get('criado_em', 'N/A')}")
            if 'senha_alterada_em' in info:
                print(f"   Senha alterada em: {info['senha_alterada_em']}")
        
        print("\n" + "="*60)
    
    def add_user(self, username: str, password: str, nome: str):
        """Adiciona um novo usuário"""
        users = self.load_users()
        
        if username in users:
            print(f"❌ Usuário '{username}' já existe!")
            return False
        
        users[username] = {
            "password": self.hash_password(password),
            "nome": nome,
            "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_users(users)
        print(f"✅ Usuário '{username}' criado com sucesso!")
        return True
    
    def remove_user(self, username: str):
        """Remove um usuário"""
        users = self.load_users()
        
        if username not in users:
            print(f"❌ Usuário '{username}' não existe!")
            return False
        
        del users[username]
        self.save_users(users)
        print(f"✅ Usuário '{username}' removido com sucesso!")
        return True
    
    def change_password(self, username: str, new_password: str):
        """Altera a senha de um usuário"""
        users = self.load_users()
        
        if username not in users:
            print(f"❌ Usuário '{username}' não existe!")
            return False
        
        users[username]["password"] = self.hash_password(new_password)
        users[username]["senha_alterada_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.save_users(users)
        print(f"✅ Senha do usuário '{username}' alterada com sucesso!")
        return True
    
    def reset_to_default(self):
        """Reseta para os usuários padrão"""
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
        
        self.save_users(users)
        print("✅ Usuários resetados para o padrão!")

def main():
    manager = UserManager()
    
    while True:
        print("\n" + "="*60)
        print("🔧 GERENCIADOR DE USUÁRIOS")
        print("="*60)
        print("1. 📋 Listar usuários")
        print("2. ➕ Adicionar usuário")
        print("3. ❌ Remover usuário")
        print("4. 🔑 Alterar senha")
        print("5. 🔄 Resetar para padrão")
        print("6. 🚪 Sair")
        print("="*60)
        
        opcao = input("\n📌 Escolha uma opção: ").strip()
        
        if opcao == "1":
            manager.list_users()
        
        elif opcao == "2":
            print("\n➕ ADICIONAR NOVO USUÁRIO")
            username = input("Digite o nome de usuário: ").strip()
            nome = input("Digite o nome completo: ").strip()
            password = input("Digite a senha: ").strip()
            
            if username and nome and password:
                manager.add_user(username, password, nome)
            else:
                print("❌ Todos os campos são obrigatórios!")
        
        elif opcao == "3":
            print("\n❌ REMOVER USUÁRIO")
            manager.list_users()
            username = input("\nDigite o usuário a remover: ").strip()
            
            if username:
                confirma = input(f"⚠️ Tem certeza que deseja remover '{username}'? (s/n): ").strip().lower()
                if confirma == 's':
                    manager.remove_user(username)
        
        elif opcao == "4":
            print("\n🔑 ALTERAR SENHA")
            manager.list_users()
            username = input("\nDigite o usuário: ").strip()
            new_password = input("Digite a nova senha: ").strip()
            
            if username and new_password:
                manager.change_password(username, new_password)
            else:
                print("❌ Todos os campos são obrigatórios!")
        
        elif opcao == "5":
            print("\n🔄 RESETAR PARA PADRÃO")
            confirma = input("⚠️ Isso vai APAGAR todos os usuários e criar os padrão. Confirma? (s/n): ").strip().lower()
            if confirma == 's':
                manager.reset_to_default()
        
        elif opcao == "6":
            print("\n👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()