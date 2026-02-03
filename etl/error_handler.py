"""
Comprehensive error handling and retry logic for ETL pipeline
"""
import logging
import time
import traceback
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime
import json
from config import ETL_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLError(Exception):
    """Base exception for ETL pipeline errors"""
    def __init__(self, message: str, error_code: str = None, context: Dict = None):
        self.message = message
        self.error_code = error_code or "ETL_GENERIC_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

class DataValidationError(ETLError):
    """Exception for data validation failures"""
    def __init__(self, message: str, validation_results: Dict = None):
        super().__init__(message, "DATA_VALIDATION_ERROR", {"validation_results": validation_results})

class DatabaseConnectionError(ETLError):
    """Exception for database connection issues"""
    def __init__(self, message: str, connection_details: Dict = None):
        super().__init__(message, "DB_CONNECTION_ERROR", {"connection_details": connection_details})

class DataTransformationError(ETLError):
    """Exception for data transformation failures"""
    def __init__(self, message: str, transformation_step: str = None, data_sample: Dict = None):
        super().__init__(message, "DATA_TRANSFORMATION_ERROR", {
            "transformation_step": transformation_step,
            "data_sample": data_sample
        })

class DataQualityError(ETLError):
    """Exception for data quality check failures"""
    def __init__(self, message: str, quality_metrics: Dict = None):
        super().__init__(message, "DATA_QUALITY_ERROR", {"quality_metrics": quality_metrics})

class ErrorHandler:
    def __init__(self):
        self.error_log = []
        self.max_retries = ETL_CONFIG.get('max_retries', 3)
        self.retry_delay = ETL_CONFIG.get('retry_delay', 5)
    
    def log_error(self, error: Exception, context: Dict = None):
        """Log error with context information"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        if isinstance(error, ETLError):
            error_entry['error_code'] = error.error_code
            error_entry['etl_context'] = error.context
        
        self.error_log.append(error_entry)
        logger.error(f"Error logged: {error_entry}")
    
    def get_error_summary(self) -> Dict:
        """Get summary of all errors encountered"""
        if not self.error_log:
            return {'total_errors': 0, 'error_types': {}}
        
        error_types = {}
        for error in self.error_log:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'error_types': error_types,
            'latest_error': self.error_log[-1] if self.error_log else None,
            'first_error': self.error_log[0] if self.error_log else None
        }
    
    def clear_errors(self):
        """Clear error log"""
        self.error_log.clear()
        logger.info("Error log cleared")

# Global error handler instance
error_handler = ErrorHandler()

def retry_on_failure(max_retries: int = None, delay: float = None, 
                    exceptions: tuple = (Exception,), backoff_factor: float = 1.0):
    """
    Decorator for retrying functions on failure with exponential backoff
    """
    max_retries = max_retries or ETL_CONFIG.get('max_retries', 3)
    delay = delay or ETL_CONFIG.get('retry_delay', 5)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"Function {func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}. "
                            f"Retrying in {wait_time} seconds. Error: {str(e)}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Final error: {str(e)}"
                        )
                        error_handler.log_error(e, {
                            'function': func.__name__,
                            'attempts': max_retries + 1,
                            'args': str(args)[:200],  # Limit args length
                            'kwargs': str(kwargs)[:200]
                        })
                        raise e
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator

def handle_etl_errors(func: Callable) -> Callable:
    """
    Decorator for comprehensive ETL error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        
        try:
            logger.info(f"Starting {func.__name__}")
            result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            
            return result
        
        except DataValidationError as e:
            logger.error(f"Data validation failed in {func.__name__}: {e.message}")
            error_handler.log_error(e, {'function': func.__name__, 'step': 'data_validation'})
            raise
        
        except DatabaseConnectionError as e:
            logger.error(f"Database connection failed in {func.__name__}: {e.message}")
            error_handler.log_error(e, {'function': func.__name__, 'step': 'database_connection'})
            raise
        
        except DataTransformationError as e:
            logger.error(f"Data transformation failed in {func.__name__}: {e.message}")
            error_handler.log_error(e, {'function': func.__name__, 'step': 'data_transformation'})
            raise
        
        except DataQualityError as e:
            logger.error(f"Data quality check failed in {func.__name__}: {e.message}")
            error_handler.log_error(e, {'function': func.__name__, 'step': 'data_quality'})
            raise
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error in {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
            error_handler.log_error(e, {
                'function': func.__name__,
                'execution_time': execution_time,
                'step': 'unknown'
            })
            raise ETLError(f"Unexpected error in {func.__name__}: {str(e)}", "UNEXPECTED_ERROR")
    
    return wrapper

def validate_data_frame(df, table_name: str, required_columns: List[str] = None, 
                       min_rows: int = 1, max_null_percentage: float = 5.0):
    """
    Validate DataFrame meets basic quality requirements
    """
    validation_results = {}
    
    # Check if DataFrame is empty
    if df is None or df.empty:
        raise DataValidationError(f"DataFrame for {table_name} is empty or None")
    
    # Check minimum row count
    if len(df) < min_rows:
        raise DataValidationError(
            f"DataFrame for {table_name} has {len(df)} rows, minimum required: {min_rows}"
        )
    
    # Check required columns
    if required_columns:
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise DataValidationError(
                f"DataFrame for {table_name} missing required columns: {missing_columns}"
            )
    
    # Check null percentage
    for column in df.columns:
        null_count = df[column].isnull().sum()
        null_percentage = (null_count / len(df)) * 100
        
        validation_results[f"{column}_null_percentage"] = null_percentage
        
        if null_percentage > max_null_percentage:
            raise DataValidationError(
                f"Column {column} in {table_name} has {null_percentage:.2f}% null values, "
                f"maximum allowed: {max_null_percentage}%",
                validation_results
            )
    
    # Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    duplicate_percentage = (duplicate_count / len(df)) * 100
    validation_results['duplicate_percentage'] = duplicate_percentage
    
    if duplicate_percentage > 1.0:  # Allow up to 1% duplicates
        logger.warning(
            f"DataFrame for {table_name} has {duplicate_percentage:.2f}% duplicate rows"
        )
    
    validation_results['total_rows'] = len(df)
    validation_results['total_columns'] = len(df.columns)
    
    logger.info(f"Data validation passed for {table_name}: {validation_results}")
    return validation_results

def create_error_report() -> Dict:
    """
    Create comprehensive error report for monitoring
    """
    error_summary = error_handler.get_error_summary()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'pipeline_status': 'FAILED' if error_summary['total_errors'] > 0 else 'SUCCESS',
        'error_summary': error_summary,
        'recommendations': []
    }
    
    # Add recommendations based on error types
    if 'DataValidationError' in error_summary.get('error_types', {}):
        report['recommendations'].append(
            "Review source data quality and implement additional validation rules"
        )
    
    if 'DatabaseConnectionError' in error_summary.get('error_types', {}):
        report['recommendations'].append(
            "Check database connectivity and connection pool settings"
        )
    
    if 'DataTransformationError' in error_summary.get('error_types', {}):
        report['recommendations'].append(
            "Review data transformation logic and handle edge cases"
        )
    
    if 'DataQualityError' in error_summary.get('error_types', {}):
        report['recommendations'].append(
            "Implement stricter data quality checks and monitoring"
        )
    
    return report