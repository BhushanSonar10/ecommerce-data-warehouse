"""
Configuration settings for ETL pipeline with Redis caching
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection settings
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ecommerce_dw'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Redis connection settings
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': int(os.getenv('REDIS_DB', '0')),
    'decode_responses': True
}

# File paths
DATA_DIR = '/app/data'
SQL_DIR = '/app/sql'

# CSV file paths
CSV_FILES = {
    'customers': f'{DATA_DIR}/customers.csv',
    'products': f'{DATA_DIR}/products.csv',
    'orders': f'{DATA_DIR}/orders.csv',
    'payments': f'{DATA_DIR}/payments.csv',
    'suppliers': f'{DATA_DIR}/suppliers.csv',
    'inventory_movements': f'{DATA_DIR}/inventory_movements.csv'
}

# Date range for date dimension
DATE_RANGE = {
    'start_date': '2023-01-01',
    'end_date': '2024-12-31'
}

# ETL Configuration
ETL_CONFIG = {
    'batch_size': 1000,
    'max_retries': 3,
    'retry_delay': 5,  # seconds
    'timeout': 1800,   # 30 minutes
    'enable_caching': True,
    'cache_ttl': 3600  # 1 hour
}

# Data Quality Thresholds
QUALITY_THRESHOLDS = {
    'max_null_percentage': 5.0,
    'max_duplicate_percentage': 1.0,
    'min_row_count': 1,
    'max_processing_time': 1800  # 30 minutes
}