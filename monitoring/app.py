"""
Real-time monitoring dashboard for E-Commerce Data Warehouse
Flask-based web application for monitoring ETL pipeline health and performance
"""

from flask import Flask, render_template, jsonify, request
import psycopg2
import redis
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ecommerce_dw'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': int(os.getenv('REDIS_DB', '0')),
    'decode_responses': True
}

class MonitoringService:
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self._connect_services()
    
    def _connect_services(self):
        """Connect to PostgreSQL and Redis"""
        try:
            # PostgreSQL connection
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to PostgreSQL")
            
            # Redis connection
            self.redis_client = redis.Redis(**REDIS_CONFIG)
            self.redis_client.ping()
            logger.info("Connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to services: {e}")
    
    def get_database_health(self) -> Dict:
        """Check database health and connection status"""
        try:
            cursor = self.db_conn.cursor()
            
            # Test connection
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
            """)
            db_size = cursor.fetchone()[0]
            
            # Get table row counts
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """)
            
            table_stats = []
            for row in cursor.fetchall():
                table_stats.append({
                    'schema': row[0],
                    'table': row[1],
                    'inserts': row[2],
                    'updates': row[3],
                    'deletes': row[4],
                    'live_tuples': row[5]
                })
            
            cursor.close()
            
            return {
                'status': 'healthy',
                'database_size': db_size,
                'table_statistics': table_stats,
                'connection_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_time': datetime.now().isoformat()
            }
    
    def get_redis_health(self) -> Dict:
        """Check Redis health and get cache statistics"""
        try:
            # Test connection
            self.redis_client.ping()
            
            # Get Redis info
            info = self.redis_client.info()
            
            # Get cache statistics
            stats = {
                'status': 'healthy',
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            if hits + misses > 0:
                stats['hit_rate'] = round((hits / (hits + misses)) * 100, 2)
            else:
                stats['hit_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_etl_metrics(self) -> Dict:
        """Get ETL pipeline execution metrics"""
        try:
            # Get latest pipeline metrics from Redis
            pipeline_keys = self.redis_client.keys('pipeline_metrics:*')
            
            if not pipeline_keys:
                return {'status': 'no_data', 'message': 'No pipeline metrics found'}
            
            # Get the most recent metrics
            latest_key = sorted(pipeline_keys)[-1]
            metrics_data = self.redis_client.get(latest_key)
            
            if metrics_data:
                metrics = json.loads(metrics_data)
                return {
                    'status': 'available',
                    'latest_run': metrics,
                    'total_runs': len(pipeline_keys)
                }
            else:
                return {'status': 'no_data', 'message': 'No metrics data available'}
                
        except Exception as e:
            logger.error(f"Failed to get ETL metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_data_quality_metrics(self) -> Dict:
        """Get data quality check results"""
        try:
            # Get latest data quality results from Redis
            quality_keys = self.redis_client.keys('data_quality:*')
            
            if not quality_keys:
                return {'status': 'no_data', 'message': 'No data quality metrics found'}
            
            # Get the most recent results
            latest_key = sorted(quality_keys)[-1]
            quality_data = self.redis_client.get(latest_key)
            
            if quality_data:
                quality_results = json.loads(quality_data)
                return {
                    'status': 'available',
                    'latest_results': quality_results,
                    'total_checks': len(quality_keys)
                }
            else:
                return {'status': 'no_data', 'message': 'No quality data available'}
                
        except Exception as e:
            logger.error(f"Failed to get data quality metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_business_metrics(self) -> Dict:
        """Get key business metrics from the data warehouse"""
        try:
            cursor = self.db_conn.cursor()
            
            # Total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(total_price + shipping_cost + tax_amount), 0) as total_revenue
                FROM fact_sales
                WHERE order_status = 'delivered'
            """)
            total_revenue = cursor.fetchone()[0]
            
            # Total orders
            cursor.execute("""
                SELECT COUNT(DISTINCT order_id) as total_orders
                FROM fact_sales
                WHERE order_status = 'delivered'
            """)
            total_orders = cursor.fetchone()[0]
            
            # Total customers
            cursor.execute("SELECT COUNT(*) as total_customers FROM dim_customers")
            total_customers = cursor.fetchone()[0]
            
            # Average order value
            cursor.execute("""
                SELECT COALESCE(AVG(total_price + shipping_cost + tax_amount), 0) as avg_order_value
                FROM fact_sales
                WHERE order_status = 'delivered'
            """)
            avg_order_value = cursor.fetchone()[0]
            
            # Monthly revenue trend (last 6 months)
            cursor.execute("""
                SELECT 
                    dd.year,
                    dd.month,
                    dd.month_name,
                    COALESCE(SUM(fs.total_price + fs.shipping_cost + fs.tax_amount), 0) as monthly_revenue
                FROM dim_dates dd
                LEFT JOIN fact_sales fs ON dd.date_key = fs.order_date_key AND fs.order_status = 'delivered'
                WHERE dd.date_value >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY dd.year, dd.month, dd.month_name
                ORDER BY dd.year, dd.month
            """)
            
            monthly_trends = []
            for row in cursor.fetchall():
                monthly_trends.append({
                    'year': row[0],
                    'month': row[1],
                    'month_name': row[2],
                    'revenue': float(row[3])
                })
            
            cursor.close()
            
            return {
                'status': 'available',
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'total_customers': total_customers,
                'avg_order_value': float(avg_order_value),
                'monthly_trends': monthly_trends,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get business metrics: {e}")
            return {'status': 'error', 'error': str(e)}

# Initialize monitoring service
monitoring_service = MonitoringService()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/health')
def health_check():
    """Overall system health check"""
    db_health = monitoring_service.get_database_health()
    redis_health = monitoring_service.get_redis_health()
    
    overall_status = 'healthy' if (
        db_health['status'] == 'healthy' and 
        redis_health['status'] == 'healthy'
    ) else 'unhealthy'
    
    return jsonify({
        'overall_status': overall_status,
        'database': db_health,
        'redis': redis_health,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/etl-metrics')
def etl_metrics():
    """Get ETL pipeline metrics"""
    return jsonify(monitoring_service.get_etl_metrics())

@app.route('/api/data-quality')
def data_quality():
    """Get data quality metrics"""
    return jsonify(monitoring_service.get_data_quality_metrics())

@app.route('/api/business-metrics')
def business_metrics():
    """Get business KPIs and metrics"""
    return jsonify(monitoring_service.get_business_metrics())

@app.route('/api/system-stats')
def system_stats():
    """Get comprehensive system statistics"""
    return jsonify({
        'database': monitoring_service.get_database_health(),
        'redis': monitoring_service.get_redis_health(),
        'etl': monitoring_service.get_etl_metrics(),
        'data_quality': monitoring_service.get_data_quality_metrics(),
        'business': monitoring_service.get_business_metrics(),
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'Please check the logs for more details',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found',
        'timestamp': datetime.now().isoformat()
    }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)