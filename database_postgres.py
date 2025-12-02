import psycopg2
from psycopg2 import pool
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import streamlit as st

class DatabasePostgres:
    def __init__(self, db_url: str = None):
        """
        Inicializa conexão com PostgreSQL
        db_url formato: postgresql://user:password@host:port/database
        """
        print("\n Iniciando DatabasePostgres")

        if db_url:
            print(" URL fornecida diretamente: {db_url[:30]}...")
            self.db_url = db_url
        else:
            print(" Tentando obter URL dos secrets...")
            self.db_url = self._get_db_url_from_secrets()
        if not self.db_url:
            raise Exception("URL do banco não encontrada! Verifique os secrets")
        
        print(f" URL configurada: {self.db_url[:30]}...")

        self.connection_pool = None
        self._init_connection_pool()
        self.create_tables()

        print(" DatabasePostgres iniciado com sucesso!\n")
    
    def _get_db_url_from_secrets(self) -> str:
        """Obtém URL do banco dos secrets do Streamlit"""
        try:
            if hasattr(st, 'secrets'):
                # Tentar na chave 'database' primeiro
                if 'database' in st.secrets and 'url' in st.secrets['database']:
                    print(" URL encontrata em secrets.database.url")
                    return st.secrets['database']['url']
                
                # Tentar na chave 'supabase'
                if 'supabase' in st.secrets and 'url' in st.secrets['supabase']:
                    print("URL encontrada em secrets.supabase.url")
                    return st.secrets['supabase']['url']
        except Exception as e:
            print(f" Erro ao ler secrets: {e}")
        return None
    
    def _init_connection_pool(self):
        """Inicializa pool de conexões"""
        if self.db_url:
            try:
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10,  # mínimo e máximo de conexões
                    self.db_url
                )
            except Exception as e:
                print(f"Erro ao criar pool de conexões: {e}")
                raise
    
    def get_connection(self):
        """Obtém uma conexão do pool"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        raise Exception("Pool de conexões não inicializado")
    
    def return_connection(self, conn):
        """Devolve conexão ao pool"""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def create_tables(self):
        """Cria a tabela de métricas se não existir"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas (
                    id SERIAL PRIMARY KEY,
                    data DATE NOT NULL,
                    promotora TEXT NOT NULL,
                    produto TEXT,
                    valor_liberado DECIMAL(15,2) NOT NULL,
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
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_produto ON metricas(produto)
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Erro ao criar tabelas: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def import_from_csv(self, csv_path: str) -> Dict[str, any]:
        """Importa dados de um arquivo CSV"""
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
            
            # Converter data
            df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['DATA'])
            
            # Converter valor
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].astype(str)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace('R$', '', regex=False)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace(' ', '', regex=False)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace('.', '', regex=False)
            df['VALOR LIBERADO'] = df['VALOR LIBERADO'].str.replace(',', '.', regex=False)
            df['VALOR LIBERADO'] = pd.to_numeric(df['VALOR LIBERADO'], errors='coerce')
            df = df.dropna(subset=['VALOR LIBERADO'])
            
            # Preparar dados
            df['DATA'] = df['DATA'].dt.strftime('%Y-%m-%d')
            
            if 'ID' in df.columns:
                df['ID_EXTERNO'] = df['ID']
            else:
                df['ID_EXTERNO'] = None
            
            if 'PRODUTO' in df.columns:
                df['PRODUTO_TEMP'] = df['PRODUTO']
            else:
                df['PRODUTO_TEMP'] = None
            
            # Inserir no banco
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                # Contar registros antes
                cursor.execute("SELECT COUNT(*) FROM metricas")
                count_before = cursor.fetchone()[0]
                
                # Inserir dados
                registros_inseridos = 0
                for _, row in df[['DATA', 'PROMOTORA', 'PRODUTO_TEMP', 'VALOR LIBERADO', 'ID_EXTERNO']].iterrows():
                    cursor.execute("""
                        INSERT INTO metricas (data, promotora, produto, valor_liberado, id_externo)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (row['DATA'], row['PROMOTORA'], row['PRODUTO_TEMP'], 
                          row['VALOR LIBERADO'], row['ID_EXTERNO']))
                    registros_inseridos += 1
                
                conn.commit()
                
                # Contar registros depois
                cursor.execute("SELECT COUNT(*) FROM metricas")
                count_after = cursor.fetchone()[0]
                
                return {
                    'sucesso': True,
                    'registros_importados': registros_inseridos,
                    'total_no_csv': len(df),
                    'total_no_banco': count_after
                }
            
            except Exception as e:
                conn.rollback()
                return {
                    'sucesso': False,
                    'erro': str(e)
                }
            finally:
                cursor.close()
                self.return_connection(conn)
        
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def get_totais_por_periodo(self, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Retorna totais agrupados por período"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    data::date as data,
                    COUNT(*) as quantidade,
                    SUM(valor_liberado) as total_liberado
                FROM metricas
                WHERE data BETWEEN %s AND %s
                GROUP BY data
                ORDER BY data
            """
            
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            return df
        finally:
            self.return_connection(conn)
    
    def get_totais_por_promotora(self, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Retorna totais agrupados por promotora"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    promotora,
                    COUNT(*) as quantidade,
                    SUM(valor_liberado) as total_liberado,
                    AVG(valor_liberado) as media_liberado
                FROM metricas
                WHERE data BETWEEN %s AND %s
                GROUP BY promotora
                ORDER BY total_liberado DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            return df
        finally:
            self.return_connection(conn)
    
    def get_totais_por_produto(self, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Retorna totais agrupados por produto"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    COALESCE(produto, 'Não informado') as produto,
                    COUNT(*) as quantidade,
                    SUM(valor_liberado) as total_liberado,
                    AVG(valor_liberado) as media_liberado
                FROM metricas
                WHERE data BETWEEN %s AND %s
                GROUP BY produto
                ORDER BY total_liberado DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            return df
        finally:
            self.return_connection(conn)
    
    def get_resumo_geral(self, data_inicio: Optional[str] = None, 
                        data_fim: Optional[str] = None) -> Dict:
        """Retorna resumo geral das métricas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if data_inicio and data_fim:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_registros,
                        SUM(valor_liberado) as total_liberado,
                        AVG(valor_liberado) as media_liberado,
                        MIN(valor_liberado) as min_liberado,
                        MAX(valor_liberado) as max_liberado,
                        COUNT(DISTINCT promotora) as total_promotoras,
                        COUNT(DISTINCT produto) as total_produtos
                    FROM metricas
                    WHERE data BETWEEN %s AND %s
                """, (data_inicio, data_fim))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_registros,
                        SUM(valor_liberado) as total_liberado,
                        AVG(valor_liberado) as media_liberado,
                        MIN(valor_liberado) as min_liberado,
                        MAX(valor_liberado) as max_liberado,
                        COUNT(DISTINCT promotora) as total_promotoras,
                        COUNT(DISTINCT produto) as total_produtos
                    FROM metricas
                """)
            
            result = cursor.fetchone()
            
            return {
                'total_registros': result[0] or 0,
                'total_liberado': float(result[1]) if result[1] else 0.0,
                'media_liberado': float(result[2]) if result[2] else 0.0,
                'min_liberado': float(result[3]) if result[3] else 0.0,
                'max_liberado': float(result[4]) if result[4] else 0.0,
                'total_promotoras': result[5] or 0,
                'total_produtos': result[6] or 0
            }
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_dados_completos(self, data_inicio: Optional[str] = None,
                           data_fim: Optional[str] = None) -> pd.DataFrame:
        """Retorna todos os dados filtrados por período"""
        conn = self.get_connection()
        
        try:
            if data_inicio and data_fim:
                query = """
                    SELECT data, promotora, produto, valor_liberado, id_externo
                    FROM metricas
                    WHERE data BETWEEN %s AND %s
                    ORDER BY data DESC
                """
                df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            else:
                query = """
                    SELECT data, promotora, produto, valor_liberado, id_externo
                    FROM metricas
                    ORDER BY data DESC
                """
                df = pd.read_sql_query(query, conn)
            
            return df
        finally:
            self.return_connection(conn)
    
    def limpar_banco(self) -> bool:
        """Limpa todos os dados do banco (use com cuidado!)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM metricas")
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Erro ao limpar banco: {e}")
            return False
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def close_all_connections(self):
        """Fecha todas as conexões do pool"""
        if self.connection_pool:
            self.connection_pool.closeall()