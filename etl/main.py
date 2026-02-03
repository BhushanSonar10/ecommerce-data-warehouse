"""
Main ETL pipeline script with enhanced error handling and caching
Orchestrates the complete data warehouse build process
"""
import pandas as pd
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import CSV_FILES, SQL_DIR, DATE_RANGE, ETL_CONFIG
from database import DatabaseManager
from transformations import DataTransformer
from data_quality import DataQualityChecker
from cache_manager import cache_manager
from error_handler import (
    error_handler, handle_etl_errors, retry_on_failure, 
    validate_data_frame, create_error_report, ETLError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.transformer = DataTransformer()
        self.run_id = f"etl_run_{int(time.time())}"
        self.start_time = time.time()
        self.metrics = {
            'run_id': self.run_id,
            'start_time': datetime.now().isoformat(),
            'status': 'running'
        }
    
    @handle_etl_errors
    @retry_on_failure(max_retries=2, delay=10)
    def connect_to_database(self):
        """Establish database connection with retry logic"""
        logger.info("Connecting to database...")
        if not self.db.connect():
            raise ETLError("Failed to connect to database", "DB_CONNECTION_ERROR")
        return True
    
    @handle_etl_errors
    def create_database_schema(self):
        """Create database schema"""
        logger.info("Creating database schema...")
        schema_file = f"{SQL_DIR}/01_create_schema.sql"
        
        if not self.db.execute_sql_file(schema_file):
            raise ETLError("Failed to create database schema", "SCHEMA_CREATION_ERROR")
        
        return True
    
    @handle_etl_errors
    def load_and_validate_source_data(self):
        """Load and validate all source CSV files"""
        logger.info("Loading and validating source data...")
        source_data = {}
        
        for data_type, file_path in CSV_FILES.items():
            try:
                # Check cache first
                cache_key = f"source_data:{data_type}"
                cached_df = cache_manager.get_cached_dataframe(cache_key)
                
                if cached_df is not None:
                    logger.info(f"Using cached data for {data_type}")
                    df = cached_df
                else:
                    logger.info(f"Loading {data_type} from {file_path}")
                    df = pd.read_csv(file_path)
                    
                    # Cache the loaded data
                    cache_manager.cache_dataframe(cache_key, df, ttl=1800)  # 30 minutes
                
                # Validate data
                if data_type == 'customers':
                    validate_data_frame(df, data_type, ['customer_id', 'email'], min_rows=1)
                elif data_type == 'products':
                    validate_data_frame(df, data_type, ['product_id', 'price'], min_rows=1)
                elif data_type == 'orders':
                    validate_data_frame(df, data_type, ['order_id', 'customer_id', 'product_id'], min_rows=1)
                elif data_type == 'payments':
                    validate_data_frame(df, data_type, ['payment_id', 'order_id'], min_rows=1)
                
                source_data[data_type] = df
                logger.info(f"Successfully loaded and validated {len(df)} {data_type} records")
                
            except Exception as e:
                raise ETLError(f"Failed to load {data_type} data: {str(e)}", "DATA_LOADING_ERROR")
        
        self.metrics['source_data_counts'] = {k: len(v) for k, v in source_data.items()}
        return source_data
    
    @handle_etl_errors
    def transform_data(self, source_data):
        """Transform all source data"""
        logger.info("Transforming source data...")
        transformed_data = {}
        
        try:
            # Transform each dataset
            transformed_data['customers'] = self.transformer.clean_customers_data(source_data['customers'])
            transformed_data['products'] = self.transformer.clean_products_data(source_data['products'])
            transformed_data['orders'] = self.transformer.clean_orders_data(source_data['orders'])
            transformed_data['payments'] = self.transformer.clean_payments_data(source_data['payments'])
            
            # Generate date dimension
            transformed_data['dates'] = self.transformer.generate_date_dimension(
                DATE_RANGE['start_date'], 
                DATE_RANGE['end_date']
            )
            
            # Cache transformed data
            for data_type, df in transformed_data.items():
                cache_key = f"transformed_data:{data_type}:{self.run_id}"
                cache_manager.cache_dataframe(cache_key, df, ttl=3600)  # 1 hour
            
            self.metrics['transformed_data_counts'] = {k: len(v) for k, v in transformed_data.items()}
            return transformed_data
            
        except Exception as e:
            raise ETLError(f"Data transformation failed: {str(e)}", "DATA_TRANSFORMATION_ERROR")
    
    @handle_etl_errors
    @retry_on_failure(max_retries=2, delay=5)
    def load_dimension_tables(self, transformed_data):
        """Load dimension tables"""
        logger.info("Loading dimension tables...")
        
        try:
            # Load customers dimension
            if not self.db.insert_dataframe(transformed_data['customers'], 'dim_customers', if_exists='replace'):
                raise ETLError("Failed to load customers dimension", "DIMENSION_LOAD_ERROR")
            
            # Load products dimension
            if not self.db.insert_dataframe(transformed_data['products'], 'dim_products', if_exists='replace'):
                raise ETLError("Failed to load products dimension", "DIMENSION_LOAD_ERROR")
            
            # Load date dimension
            if not self.db.insert_dataframe(transformed_data['dates'], 'dim_dates', if_exists='replace'):
                raise ETLError("Failed to load date dimension", "DIMENSION_LOAD_ERROR")
            
            return True
            
        except Exception as e:
            raise ETLError(f"Dimension table loading failed: {str(e)}", "DIMENSION_LOAD_ERROR")
    
    @handle_etl_errors
    def retrieve_dimension_keys(self):
        """Retrieve dimension keys for fact table creation"""
        logger.info("Retrieving dimension keys...")
        
        try:
            customer_dim_df = self.db.fetch_query("SELECT customer_key, customer_id FROM dim_customers")
            product_dim_df = self.db.fetch_query("SELECT product_key, product_id FROM dim_products")
            date_dim_df = self.db.fetch_query("SELECT date_key, date_value FROM dim_dates")
            
            if any(df is None for df in [customer_dim_df, product_dim_df, date_dim_df]):
                raise ETLError("Failed to retrieve dimension keys", "DIMENSION_KEY_ERROR")
            
            # Cache dimension keys
            cache_manager.cache_dataframe(f"dim_keys:customers:{self.run_id}", customer_dim_df)
            cache_manager.cache_dataframe(f"dim_keys:products:{self.run_id}", product_dim_df)
            cache_manager.cache_dataframe(f"dim_keys:dates:{self.run_id}", date_dim_df)
            
            return customer_dim_df, product_dim_df, date_dim_df
            
        except Exception as e:
            raise ETLError(f"Failed to retrieve dimension keys: {str(e)}", "DIMENSION_KEY_ERROR")
    
    @handle_etl_errors
    def create_and_load_fact_table(self, transformed_data, customer_dim_df, product_dim_df, date_dim_df):
        """Create and load fact table"""
        logger.info("Creating and loading fact table...")
        
        try:
            fact_sales = self.transformer.create_fact_sales(
                transformed_data['orders'], 
                transformed_data['payments'], 
                transformed_data['products'],
                customer_dim_df, 
                product_dim_df, 
                date_dim_df
            )
            
            # Validate fact table
            validate_data_frame(fact_sales, 'fact_sales', 
                              ['order_id', 'customer_key', 'product_key'], min_rows=1)
            
            if not self.db.insert_dataframe(fact_sales, 'fact_sales', if_exists='replace'):
                raise ETLError("Failed to load fact sales table", "FACT_LOAD_ERROR")
            
            self.metrics['fact_records_created'] = len(fact_sales)
            return fact_sales
            
        except Exception as e:
            raise ETLError(f"Fact table creation failed: {str(e)}", "FACT_CREATION_ERROR")
    
    @handle_etl_errors
    def run_data_quality_checks(self):
        """Run comprehensive data quality checks"""
        logger.info("Running data quality checks...")
        
        try:
            quality_checker = DataQualityChecker(self.db)
            quality_results = quality_checker.run_all_checks()
            quality_checker.print_results()
            
            # Store quality results in cache
            quality_data = {
                'run_id': self.run_id,
                'timestamp': datetime.now().isoformat(),
                'results': quality_results
            }
            cache_manager.store_data_quality_results(quality_data)
            
            # Check for critical failures
            failed_checks = [r for r in quality_results if r['status'] == 'FAIL']
            if failed_checks:
                raise ETLError(f"Data quality checks failed: {len(failed_checks)} failures", 
                             "DATA_QUALITY_ERROR", {'failed_checks': failed_checks})
            
            self.metrics['data_quality_score'] = len([r for r in quality_results if r['status'] == 'PASS']) / len(quality_results) * 100
            return quality_results
            
        except Exception as e:
            raise ETLError(f"Data quality checks failed: {str(e)}", "DATA_QUALITY_ERROR")
    
    def finalize_pipeline(self, success=True):
        """Finalize pipeline execution and store metrics"""
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        self.metrics.update({
            'end_time': datetime.now().isoformat(),
            'execution_time_seconds': execution_time,
            'status': 'success' if success else 'failed'
        })
        
        # Store pipeline metrics
        cache_manager.store_pipeline_metrics(self.metrics)
        
        # Print summary
        print("\n" + "="*60)
        if success:
            print("ETL PIPELINE COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"✓ Execution Time: {execution_time:.2f} seconds")
            print(f"✓ Customers processed: {self.metrics.get('source_data_counts', {}).get('customers', 0)}")
            print(f"✓ Products processed: {self.metrics.get('source_data_counts', {}).get('products', 0)}")
            print(f"✓ Orders processed: {self.metrics.get('source_data_counts', {}).get('orders', 0)}")
            print(f"✓ Fact records created: {self.metrics.get('fact_records_created', 0)}")
            print(f"✓ Data quality score: {self.metrics.get('data_quality_score', 0):.1f}%")
        else:
            print("ETL PIPELINE FAILED")
            print("="*60)
            error_report = create_error_report()
            print(f"✗ Total errors: {error_report['error_summary']['total_errors']}")
            print(f"✗ Execution time: {execution_time:.2f} seconds")
        
        print("="*60)
        
        # Close connections
        self.db.close()
        cache_manager.close()

def main():
    """Main ETL pipeline execution"""
    pipeline = ETLPipeline()
    
    try:
        logger.info(f"Starting ETL pipeline run: {pipeline.run_id}")
        
        # Step 1: Connect to database
        pipeline.connect_to_database()
        
        # Step 2: Create database schema
        pipeline.create_database_schema()
        
        # Step 3: Load and validate source data
        source_data = pipeline.load_and_validate_source_data()
        
        # Step 4: Transform data
        transformed_data = pipeline.transform_data(source_data)
        
        # Step 5: Load dimension tables
        pipeline.load_dimension_tables(transformed_data)
        
        # Step 6: Retrieve dimension keys
        customer_dim_df, product_dim_df, date_dim_df = pipeline.retrieve_dimension_keys()
        
        # Step 7: Create and load fact table
        pipeline.create_and_load_fact_table(transformed_data, customer_dim_df, product_dim_df, date_dim_df)
        
        # Step 8: Run data quality checks
        pipeline.run_data_quality_checks()
        
        # Step 9: Finalize pipeline
        pipeline.finalize_pipeline(success=True)
        
        logger.info("ETL pipeline completed successfully!")
        return True
        
    except ETLError as e:
        logger.error(f"ETL pipeline failed with ETL error: {e.message}")
        pipeline.finalize_pipeline(success=False)
        return False
        
    except Exception as e:
        logger.error(f"ETL pipeline failed with unexpected error: {str(e)}")
        pipeline.finalize_pipeline(success=False)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)