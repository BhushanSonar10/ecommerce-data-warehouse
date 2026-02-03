"""
Apache Airflow DAG for E-Commerce Data Warehouse ETL Pipeline
Orchestrates the complete data pipeline with error handling and monitoring
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
from airflow.models import Variable
import logging
import pandas as pd
import redis
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# DAG definition
dag = DAG(
    'ecommerce_etl_pipeline',
    default_args=default_args,
    description='Complete E-Commerce Data Warehouse ETL Pipeline',
    schedule_interval='@daily',
    max_active_runs=1,
    tags=['ecommerce', 'etl', 'data-warehouse']
)

def check_data_freshness(**context):
    """
    Check if source data files are fresh and ready for processing
    """
    try:
        import os
        from datetime import datetime, timedelta
        
        data_dir = '/opt/airflow/data'
        required_files = ['customers.csv', 'products.csv', 'orders.csv', 'payments.csv']
        
        # Check if all required files exist and are recent
        for file_name in required_files:
            file_path = os.path.join(data_dir, file_name)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file {file_name} not found")
            
            # Check file modification time (should be within last 24 hours for daily processing)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if datetime.now() - file_mtime > timedelta(hours=24):
                logger.warning(f"File {file_name} is older than 24 hours")
        
        logger.info("All source files are available and fresh")
        return True
        
    except Exception as e:
        logger.error(f"Data freshness check failed: {e}")
        raise

def validate_source_data(**context):
    """
    Validate source data quality before processing
    """
    try:
        data_dir = '/opt/airflow/data'
        validation_results = {}
        
        # Validate customers data
        customers_df = pd.read_csv(f'{data_dir}/customers.csv')
        validation_results['customers'] = {
            'row_count': len(customers_df),
            'null_emails': customers_df['email'].isnull().sum(),
            'duplicate_ids': customers_df['customer_id'].duplicated().sum()
        }
        
        # Validate products data
        products_df = pd.read_csv(f'{data_dir}/products.csv')
        validation_results['products'] = {
            'row_count': len(products_df),
            'null_prices': products_df['price'].isnull().sum(),
            'negative_prices': (products_df['price'] < 0).sum()
        }
        
        # Validate orders data
        orders_df = pd.read_csv(f'{data_dir}/orders.csv')
        validation_results['orders'] = {
            'row_count': len(orders_df),
            'null_quantities': orders_df['quantity'].isnull().sum(),
            'negative_quantities': (orders_df['quantity'] < 0).sum()
        }
        
        # Store validation results in Redis for monitoring
        r = redis.Redis(host='redis', port=6379, db=0)
        r.setex('etl_validation_results', 3600, json.dumps(validation_results))
        
        # Check for critical issues
        critical_issues = []
        if validation_results['customers']['duplicate_ids'] > 0:
            critical_issues.append("Duplicate customer IDs found")
        if validation_results['products']['negative_prices'] > 0:
            critical_issues.append("Negative product prices found")
        if validation_results['orders']['negative_quantities'] > 0:
            critical_issues.append("Negative order quantities found")
        
        if critical_issues:
            raise ValueError(f"Critical data quality issues: {critical_issues}")
        
        logger.info(f"Source data validation completed: {validation_results}")
        return validation_results
        
    except Exception as e:
        logger.error(f"Source data validation failed: {e}")
        raise

def run_etl_pipeline(**context):
    """
    Execute the main ETL pipeline
    """
    try:
        import subprocess
        import os
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            'DB_HOST': 'postgres',
            'DB_PORT': '5432',
            'DB_NAME': 'ecommerce_dw',
            'DB_USER': 'postgres',
            'DB_PASSWORD': 'postgres'
        })
        
        # Run the ETL pipeline
        result = subprocess.run(
            ['python', '/opt/airflow/etl/main.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode != 0:
            logger.error(f"ETL pipeline failed: {result.stderr}")
            raise RuntimeError(f"ETL pipeline execution failed: {result.stderr}")
        
        logger.info(f"ETL pipeline completed successfully: {result.stdout}")
        
        # Store success metrics in Redis
        r = redis.Redis(host='redis', port=6379, db=0)
        success_metrics = {
            'execution_time': context['task_instance'].duration,
            'completion_time': datetime.now().isoformat(),
            'status': 'success'
        }
        r.setex('etl_execution_metrics', 3600, json.dumps(success_metrics))
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        logger.error("ETL pipeline timed out after 30 minutes")
        raise
    except Exception as e:
        logger.error(f"ETL pipeline execution failed: {e}")
        
        # Store failure metrics in Redis
        r = redis.Redis(host='redis', port=6379, db=0)
        failure_metrics = {
            'failure_time': datetime.now().isoformat(),
            'error_message': str(e),
            'status': 'failed'
        }
        r.setex('etl_execution_metrics', 3600, json.dumps(failure_metrics))
        raise

def run_data_quality_checks(**context):
    """
    Run comprehensive data quality checks after ETL
    """
    try:
        import psycopg2
        import json
        
        # Connect to the data warehouse
        conn = psycopg2.connect(
            host='postgres',
            port=5432,
            database='ecommerce_dw',
            user='postgres',
            password='postgres'
        )
        
        cursor = conn.cursor()
        quality_results = {}
        
        # Check row counts
        tables = ['dim_customers', 'dim_products', 'dim_dates', 'fact_sales']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            quality_results[f'{table}_count'] = count
        
        # Check for null values in critical columns
        cursor.execute("SELECT COUNT(*) FROM fact_sales WHERE customer_key IS NULL")
        quality_results['null_customer_keys'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fact_sales WHERE product_key IS NULL")
        quality_results['null_product_keys'] = cursor.fetchone()[0]
        
        # Check for referential integrity
        cursor.execute("""
            SELECT COUNT(*) FROM fact_sales fs
            LEFT JOIN dim_customers dc ON fs.customer_key = dc.customer_key
            WHERE dc.customer_key IS NULL
        """)
        quality_results['orphaned_customer_refs'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM fact_sales fs
            LEFT JOIN dim_products dp ON fs.product_key = dp.product_key
            WHERE dp.product_key IS NULL
        """)
        quality_results['orphaned_product_refs'] = cursor.fetchone()[0]
        
        # Check business rules
        cursor.execute("SELECT COUNT(*) FROM fact_sales WHERE quantity <= 0")
        quality_results['invalid_quantities'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fact_sales WHERE unit_price <= 0")
        quality_results['invalid_prices'] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        # Store results in Redis
        r = redis.Redis(host='redis', port=6379, db=0)
        r.setex('data_quality_results', 3600, json.dumps(quality_results))
        
        # Check for critical quality issues
        critical_issues = []
        if quality_results['null_customer_keys'] > 0:
            critical_issues.append("Null customer keys found")
        if quality_results['null_product_keys'] > 0:
            critical_issues.append("Null product keys found")
        if quality_results['orphaned_customer_refs'] > 0:
            critical_issues.append("Orphaned customer references found")
        if quality_results['orphaned_product_refs'] > 0:
            critical_issues.append("Orphaned product references found")
        if quality_results['invalid_quantities'] > 0:
            critical_issues.append("Invalid quantities found")
        if quality_results['invalid_prices'] > 0:
            critical_issues.append("Invalid prices found")
        
        if critical_issues:
            raise ValueError(f"Critical data quality issues: {critical_issues}")
        
        logger.info(f"Data quality checks passed: {quality_results}")
        return quality_results
        
    except Exception as e:
        logger.error(f"Data quality checks failed: {e}")
        raise

def generate_data_lineage(**context):
    """
    Generate and store data lineage information
    """
    try:
        lineage_info = {
            'pipeline_run_id': context['run_id'],
            'execution_date': context['execution_date'].isoformat(),
            'source_files': [
                'customers.csv',
                'products.csv', 
                'orders.csv',
                'payments.csv',
                'suppliers.csv',
                'inventory_movements.csv'
            ],
            'target_tables': [
                'dim_customers',
                'dim_products',
                'dim_dates',
                'fact_sales'
            ],
            'transformations': [
                'data_cleaning',
                'type_conversions',
                'surrogate_key_generation',
                'date_dimension_creation',
                'fact_table_joins'
            ]
        }
        
        # Store lineage in Redis
        r = redis.Redis(host='redis', port=6379, db=0)
        r.setex(f'data_lineage_{context["run_id"]}', 86400, json.dumps(lineage_info))
        
        logger.info(f"Data lineage generated: {lineage_info}")
        return lineage_info
        
    except Exception as e:
        logger.error(f"Data lineage generation failed: {e}")
        raise

def send_success_notification(**context):
    """
    Send success notification and update monitoring dashboard
    """
    try:
        # Get execution metrics
        r = redis.Redis(host='redis', port=6379, db=0)
        
        validation_results = json.loads(r.get('etl_validation_results') or '{}')
        quality_results = json.loads(r.get('data_quality_results') or '{}')
        execution_metrics = json.loads(r.get('etl_execution_metrics') or '{}')
        
        success_summary = {
            'pipeline_status': 'SUCCESS',
            'execution_date': context['execution_date'].isoformat(),
            'run_id': context['run_id'],
            'total_customers_processed': validation_results.get('customers', {}).get('row_count', 0),
            'total_products_processed': validation_results.get('products', {}).get('row_count', 0),
            'total_orders_processed': validation_results.get('orders', {}).get('row_count', 0),
            'fact_records_created': quality_results.get('fact_sales_count', 0),
            'data_quality_score': 100 if not any([
                quality_results.get('null_customer_keys', 0),
                quality_results.get('null_product_keys', 0),
                quality_results.get('orphaned_customer_refs', 0),
                quality_results.get('orphaned_product_refs', 0),
                quality_results.get('invalid_quantities', 0),
                quality_results.get('invalid_prices', 0)
            ]) else 85
        }
        
        # Store success summary
        r.setex('pipeline_success_summary', 86400, json.dumps(success_summary))
        
        logger.info(f"Pipeline completed successfully: {success_summary}")
        return success_summary
        
    except Exception as e:
        logger.error(f"Success notification failed: {e}")
        # Don't fail the pipeline for notification issues
        return {'status': 'notification_failed', 'error': str(e)}

# Define task dependencies
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

# File sensors to check for source data availability
file_sensors = []
for file_name in ['customers.csv', 'products.csv', 'orders.csv', 'payments.csv']:
    sensor = FileSensor(
        task_id=f'check_{file_name.replace(".csv", "")}_file',
        filepath=f'/opt/airflow/data/{file_name}',
        fs_conn_id='fs_default',
        poke_interval=30,
        timeout=300,
        dag=dag
    )
    file_sensors.append(sensor)

data_freshness_check = PythonOperator(
    task_id='check_data_freshness',
    python_callable=check_data_freshness,
    dag=dag
)

source_validation = PythonOperator(
    task_id='validate_source_data',
    python_callable=validate_source_data,
    dag=dag
)

etl_execution = PythonOperator(
    task_id='run_etl_pipeline',
    python_callable=run_etl_pipeline,
    dag=dag
)

quality_checks = PythonOperator(
    task_id='run_data_quality_checks',
    python_callable=run_data_quality_checks,
    dag=dag
)

lineage_generation = PythonOperator(
    task_id='generate_data_lineage',
    python_callable=generate_data_lineage,
    dag=dag
)

success_notification = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_notification,
    dag=dag
)

end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag
)

# Set up task dependencies
start_task >> file_sensors >> data_freshness_check >> source_validation >> etl_execution >> quality_checks >> lineage_generation >> success_notification >> end_task