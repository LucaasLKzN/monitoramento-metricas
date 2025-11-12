import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_name: str = "dados.db"):
        """Inicializa conexão com o banco de dados"""
        self.db_name = db_name
        self.create_tables()
    
    def get_connection(self):
        """Cria uma nova conexão com o banco"""
        return sqlite3.connect(self.db_name)
    
    def create_tables(self):
        """Cria a tabela de métricas se não existir"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                promotora TEXT NOT NULL,
                valor_liberado REAL NOT NULL,
                id_externo TEXT,
                data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Criar índices para melhorar performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data ON metricas(data)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_promotora ON metricas(promotora)
        """)
        
        conn.commit()
        conn.close()
    
    def import_from_csv(self, csv_path: str) -> Dict[str, int]:
        """
        Importa dados de um arquivo CSV
        Retorna dicionário com estatísticas da importação
        """
        try:
            # Ler CSV
            df = pd.read_csv(csv_path)
            
            # Normalizar nomes das colunas
            df.columns = df.columns.str.strip().str.upper()
            
            # Validar colunas necessárias
            required_cols = ['DATA', 'PROMOTORA', 'VALOR LIBERADO']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Colunas faltando: {', '.join(missing_cols)}")
            
            # Converter data para formato padrão
            df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
            
            # Remover linhas com data inválida
            df = df.dropna(subset=['DATA'])
            
            # Converter valor para numérico (tratando formato brasileiro com R$)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].astype(str)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace('R$', '', regex=False)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace(' ', '', regex=False)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace('.', '', regex=False)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace(',', '.', regex=False)
            df['VALOR LIBERADO'] = pd.to_numeric(df['VALOR LIBERADO'], errors='coerce')
            
            # Remover linhas com valor inválido
            df = df.dropna(subset=['VALOR LIBERADO'])
            
            # Preparar dados para inserção
            df['DATA'] = df['DATA'].dt.strftime('%Y-%m-%d')
            
            # Verificar se existe coluna ID
            if 'ID' in df.columns:
                df['ID_EXTERNO'] = df['ID']
            else:
                df['ID_EXTERNO'] = None
            
            # Renomear colunas para minúsculas (padrão do banco)
            df_insert = df[['DATA', 'PROMOTORA', 'VALOR LIBERADO', 'ID_EXTERNO']].copy()
            df_insert.columns = ['data', 'promotora', 'valor_liberado', 'id_externo']
            
            # Inserir no banco
            conn = self.get_connection()
            
            # Contar registros antes
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM metricas")
            count_before = cursor.fetchone()[0]
            
            # Inserir dados
            df_insert.to_sql(
                'metricas',
                conn,
                if_exists='append',
                index=False
            )
            
            # Contar registros depois
            cursor.execute("SELECT COUNT(*) FROM metricas")
            count_after = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'sucesso': True,
                'registros_importados': count_after - count_before,
                'total_no_csv': len(df),
                'total_no_banco': count_after
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def get_totais_por_periodo(self, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Retorna totais agrupados por período"""
        conn = self.get_connection()
        
        query = """
            SELECT 
                DATE(data) as data,
                COUNT(*) as quantidade,
                SUM(valor_liberado) as total_liberado
            FROM metricas
            WHERE data BETWEEN ? AND ?
            GROUP BY DATE(data)
            ORDER BY data
        """
        
        df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
        conn.close()
        
        return df
    
    def get_totais_por_promotora(self, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Retorna totais agrupados por promotora"""
        conn = self.get_connection()
        
        query = """
            SELECT 
                promotora,
                COUNT(*) as quantidade,
                SUM(valor_liberado) as total_liberado,
                AVG(valor_liberado) as media_liberado
            FROM metricas
            WHERE data BETWEEN ? AND ?
            GROUP BY promotora
            ORDER BY total_liberado DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
        conn.close()
        
        return df
    
    def get_resumo_geral(self, data_inicio: Optional[str] = None, 
                        data_fim: Optional[str] = None) -> Dict:
        """Retorna resumo geral das métricas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if data_inicio and data_fim:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_registros,
                    SUM(valor_liberado) as total_liberado,
                    AVG(valor_liberado) as media_liberado,
                    MIN(valor_liberado) as min_liberado,
                    MAX(valor_liberado) as max_liberado,
                    COUNT(DISTINCT promotora) as total_promotoras
                FROM metricas
                WHERE data BETWEEN ? AND ?
            """, (data_inicio, data_fim))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_registros,
                    SUM(valor_liberado) as total_liberado,
                    AVG(valor_liberado) as media_liberado,
                    MIN(valor_liberado) as min_liberado,
                    MAX(valor_liberado) as max_liberado,
                    COUNT(DISTINCT promotora) as total_promotoras
                FROM metricas
            """)
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_registros': result[0],
            'total_liberado': result[1] or 0,
            'media_liberado': result[2] or 0,
            'min_liberado': result[3] or 0,
            'max_liberado': result[4] or 0,
            'total_promotoras': result[5]
        }
    
    def get_dados_completos(self, data_inicio: Optional[str] = None,
                           data_fim: Optional[str] = None) -> pd.DataFrame:
        """Retorna todos os dados filtrados por período"""
        conn = self.get_connection()
        
        if data_inicio and data_fim:
            query = """
                SELECT data, promotora, valor_liberado, id_externo
                FROM metricas
                WHERE data BETWEEN ? AND ?
                ORDER BY data DESC
            """
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
        else:
            query = """
                SELECT data, promotora, valor_liberado, id_externo
                FROM metricas
                ORDER BY data DESC
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def limpar_banco(self) -> bool:
        """Limpa todos os dados do banco (use com cuidado!)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metricas")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao limpar banco: {e}")
            return False