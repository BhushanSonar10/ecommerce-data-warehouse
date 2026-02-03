"""
Data quality checks and validation functions
"""
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityChecker:
    def __init__(self, db_manager):
        self.db = db_manager
        self.quality_results = []
    
    def check_row_counts(self, expected_counts):
        """Validate row counts match expectations"""
        logger.info("Checking row counts...")
        
        for table_name, expected_count in expected_counts.items():
            actual_count = self.db.get_row_count(table_name)
            status = "PASS" if actual_count == expected_count else "FAIL"
            
            result = {
                'check': 'Row Count',
                'table': table_name,
                'expected': expected_count,
                'actual': actual_count,
                'status': status
            }
            
            self.quality_results.append(result)
            logger.info(f"Row count check - {table_name}: {status} ({actual_count}/{expected_count})")
    
    def check_null_values(self, table_configs):
        """Check for null values in critical columns"""
        logger.info("Checking for null values...")
        
        for table_name, columns in table_configs.items():
            for column in columns:
                query = f"""
                SELECT COUNT(*) as null_count 
                FROM {table_name} 
                WHERE {column} IS NULL
                """
                
                result_df = self.db.fetch_query(query)
                null_count = result_df['null_count'].iloc[0] if result_df is not None else -1
                status = "PASS" if null_count == 0 else "FAIL"
                
                result = {
                    'check': 'Null Values',
                    'table': table_name,
                    'column': column,
                    'null_count': null_count,
                    'status': status
                }
                
                self.quality_results.append(result)
                logger.info(f"Null check - {table_name}.{column}: {status} ({null_count} nulls)")
    
    def check_foreign_key_integrity(self):
        """Check foreign key relationships"""
        logger.info("Checking foreign key integrity...")
        
        # Check customer foreign keys
        query = """
        SELECT COUNT(*) as orphan_count
        FROM fact_sales fs
        LEFT JOIN dim_customers dc ON fs.customer_key = dc.customer_key
        WHERE dc.customer_key IS NULL
        """
        
        result_df = self.db.fetch_query(query)
        orphan_count = result_df['orphan_count'].iloc[0] if result_df is not None else -1
        status = "PASS" if orphan_count == 0 else "FAIL"
        
        result = {
            'check': 'Foreign Key Integrity',
            'relationship': 'fact_sales -> dim_customers',
            'orphan_count': orphan_count,
            'status': status
        }
        
        self.quality_results.append(result)
        logger.info(f"FK integrity - customers: {status} ({orphan_count} orphans)")
        
        # Check product foreign keys
        query = """
        SELECT COUNT(*) as orphan_count
        FROM fact_sales fs
        LEFT JOIN dim_products dp ON fs.product_key = dp.product_key
        WHERE dp.product_key IS NULL
        """
        
        result_df = self.db.fetch_query(query)
        orphan_count = result_df['orphan_count'].iloc[0] if result_df is not None else -1
        status = "PASS" if orphan_count == 0 else "FAIL"
        
        result = {
            'check': 'Foreign Key Integrity',
            'relationship': 'fact_sales -> dim_products',
            'orphan_count': orphan_count,
            'status': status
        }
        
        self.quality_results.append(result)
        logger.info(f"FK integrity - products: {status} ({orphan_count} orphans)")
    
    def check_data_ranges(self):
        """Check data value ranges make sense"""
        logger.info("Checking data ranges...")
        
        # Check for negative quantities
        query = "SELECT COUNT(*) as negative_qty FROM fact_sales WHERE quantity < 0"
        result_df = self.db.fetch_query(query)
        negative_qty = result_df['negative_qty'].iloc[0] if result_df is not None else -1
        status = "PASS" if negative_qty == 0 else "FAIL"
        
        result = {
            'check': 'Data Range',
            'field': 'quantity',
            'issue': 'negative values',
            'count': negative_qty,
            'status': status
        }
        
        self.quality_results.append(result)
        logger.info(f"Range check - negative quantities: {status} ({negative_qty} found)")
        
        # Check for zero or negative prices
        query = "SELECT COUNT(*) as invalid_price FROM fact_sales WHERE unit_price <= 0"
        result_df = self.db.fetch_query(query)
        invalid_price = result_df['invalid_price'].iloc[0] if result_df is not None else -1
        status = "PASS" if invalid_price == 0 else "FAIL"
        
        result = {
            'check': 'Data Range',
            'field': 'unit_price',
            'issue': 'zero or negative values',
            'count': invalid_price,
            'status': status
        }
        
        self.quality_results.append(result)
        logger.info(f"Range check - invalid prices: {status} ({invalid_price} found)")
    
    def run_all_checks(self):
        """Run all data quality checks"""
        logger.info("Starting comprehensive data quality checks...")
        
        # Expected row counts (based on our sample data)
        expected_counts = {
            'dim_customers': 10,
            'dim_products': 10,
            'fact_sales': 15,
            'dim_dates': 731  # 2 years of dates
        }
        
        # Critical columns that should not be null
        null_check_configs = {
            'dim_customers': ['customer_id', 'email'],
            'dim_products': ['product_id', 'product_name', 'price'],
            'fact_sales': ['order_id', 'customer_key', 'product_key', 'quantity', 'unit_price']
        }
        
        # Run all checks
        self.check_row_counts(expected_counts)
        self.check_null_values(null_check_configs)
        self.check_foreign_key_integrity()
        self.check_data_ranges()
        
        # Summary
        total_checks = len(self.quality_results)
        passed_checks = len([r for r in self.quality_results if r['status'] == 'PASS'])
        
        logger.info(f"Data quality summary: {passed_checks}/{total_checks} checks passed")
        
        return self.quality_results
    
    def print_results(self):
        """Print formatted results"""
        print("\n" + "="*60)
        print("DATA QUALITY CHECK RESULTS")
        print("="*60)
        
        for result in self.quality_results:
            status_symbol = "✓" if result['status'] == 'PASS' else "✗"
            print(f"{status_symbol} {result['check']}: {result.get('table', '')} - {result['status']}")
        
        total_checks = len(self.quality_results)
        passed_checks = len([r for r in self.quality_results if r['status'] == 'PASS'])
        
        print(f"\nSummary: {passed_checks}/{total_checks} checks passed")
        print("="*60)