"""
Database connection and utility functions
"""
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection_string = (
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        self.engine = None
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(self.connection_string)
            self.connection = psycopg2.connect(**DB_CONFIG)
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def execute_sql_file(self, file_path):
        """Execute SQL commands from a file"""
        try:
            with open(file_path, 'r') as file:
                sql_commands = file.read()
            
            cursor = self.connection.cursor()
            cursor.execute(sql_commands)
            self.connection.commit()
            cursor.close()
            logger.info(f"Successfully executed SQL file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            self.connection.rollback()
            return False
    
    def execute_query(self, query, params=None):
        """Execute a single query"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            self.connection.rollback()
            return False
    
    def fetch_query(self, query, params=None):
        """Fetch results from a query"""
        try:
            return pd.read_sql_query(query, self.engine, params=params)
        except Exception as e:
            logger.error(f"Failed to fetch query results: {e}")
            return None
    
    def insert_dataframe(self, df, table_name, if_exists='append'):
        """Insert pandas DataFrame into database table"""
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            logger.info(f"Successfully inserted {len(df)} rows into {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {e}")
            return False
    
    def get_row_count(self, table_name):
        """Get row count for a table"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.fetch_query(query)
            return result['count'].iloc[0] if result is not None else 0
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return 0
    
    def close(self):
        """Close database connections"""
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")