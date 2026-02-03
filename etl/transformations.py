"""
Data transformation functions for ETL pipeline
"""
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataTransformer:
    def __init__(self):
        pass
    
    def clean_customers_data(self, df):
        """Clean and transform customers data"""
        logger.info("Transforming customers data...")
        
        # Create a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Convert registration_date to datetime
        cleaned_df['registration_date'] = pd.to_datetime(cleaned_df['registration_date'])
        
        # Clean phone numbers (remove any non-numeric characters except dashes)
        cleaned_df['phone'] = cleaned_df['phone'].str.replace(r'[^\d-]', '', regex=True)
        
        # Standardize email to lowercase
        cleaned_df['email'] = cleaned_df['email'].str.lower().str.strip()
        
        # Clean and standardize names
        cleaned_df['first_name'] = cleaned_df['first_name'].str.strip().str.title()
        cleaned_df['last_name'] = cleaned_df['last_name'].str.strip().str.title()
        
        # Standardize state codes to uppercase
        cleaned_df['state'] = cleaned_df['state'].str.upper().str.strip()
        
        # Clean zip codes
        cleaned_df['zip_code'] = cleaned_df['zip_code'].str.strip()
        
        logger.info(f"Cleaned {len(cleaned_df)} customer records")
        return cleaned_df
    
    def clean_products_data(self, df):
        """Clean and transform products data"""
        logger.info("Transforming products data...")
        
        cleaned_df = df.copy()
        
        # Convert dates
        cleaned_df['created_date'] = pd.to_datetime(cleaned_df['created_date'])
        
        # Ensure price and cost are numeric
        cleaned_df['price'] = pd.to_numeric(cleaned_df['price'], errors='coerce')
        cleaned_df['cost'] = pd.to_numeric(cleaned_df['cost'], errors='coerce')
        cleaned_df['weight_kg'] = pd.to_numeric(cleaned_df['weight_kg'], errors='coerce')
        
        # Clean text fields
        cleaned_df['product_name'] = cleaned_df['product_name'].str.strip()
        cleaned_df['category'] = cleaned_df['category'].str.strip().str.title()
        cleaned_df['subcategory'] = cleaned_df['subcategory'].str.strip().str.title()
        cleaned_df['brand'] = cleaned_df['brand'].str.strip()
        
        # Clean description
        cleaned_df['description'] = cleaned_df['description'].str.strip()
        
        logger.info(f"Cleaned {len(cleaned_df)} product records")
        return cleaned_df
    
    def clean_orders_data(self, df):
        """Clean and transform orders data"""
        logger.info("Transforming orders data...")
        
        cleaned_df = df.copy()
        
        # Convert date columns
        date_columns = ['order_date', 'ship_date', 'delivery_date']
        for col in date_columns:
            cleaned_df[col] = pd.to_datetime(cleaned_df[col])
        
        # Ensure numeric columns are proper type
        numeric_columns = ['quantity', 'shipping_cost', 'tax_amount']
        for col in numeric_columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # Clean status field
        cleaned_df['order_status'] = cleaned_df['order_status'].str.lower().str.strip()
        
        # Validate quantity is positive
        cleaned_df = cleaned_df[cleaned_df['quantity'] > 0]
        
        logger.info(f"Cleaned {len(cleaned_df)} order records")
        return cleaned_df
    
    def clean_payments_data(self, df):
        """Clean and transform payments data"""
        logger.info("Transforming payments data...")
        
        cleaned_df = df.copy()
        
        # Convert payment_date
        cleaned_df['payment_date'] = pd.to_datetime(cleaned_df['payment_date'])
        
        # Ensure numeric columns are proper type
        numeric_columns = ['amount', 'transaction_fee']
        for col in numeric_columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # Clean payment method and status
        cleaned_df['payment_method'] = cleaned_df['payment_method'].str.lower().str.strip()
        cleaned_df['payment_status'] = cleaned_df['payment_status'].str.lower().str.strip()
        
        # Validate amounts are positive
        cleaned_df = cleaned_df[cleaned_df['amount'] > 0]
        
        logger.info(f"Cleaned {len(cleaned_df)} payment records")
        return cleaned_df
    
    def generate_date_dimension(self, start_date, end_date):
        """Generate date dimension table"""
        logger.info("Generating date dimension...")
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Create DataFrame
        date_df = pd.DataFrame({
            'date_value': date_range,
            'year': date_range.year,
            'quarter': date_range.quarter,
            'month': date_range.month,
            'month_name': date_range.strftime('%B'),
            'day': date_range.day,
            'day_of_week': date_range.dayofweek + 1,  # 1=Monday, 7=Sunday
            'day_name': date_range.strftime('%A'),
            'week_of_year': date_range.isocalendar().week,
            'is_weekend': date_range.dayofweek >= 5,  # Saturday=5, Sunday=6
            'is_holiday': False  # Default to False, can be updated later
        })
        
        logger.info(f"Generated {len(date_df)} date records")
        return date_df
    
    def create_fact_sales(self, orders_df, payments_df, products_df, 
                         customer_dim_df, product_dim_df, date_dim_df):
        """Create fact sales table by joining all source data"""
        logger.info("Creating fact sales table...")
        
        # Start with orders as the base
        fact_df = orders_df.copy()
        
        # Join with payments
        fact_df = fact_df.merge(
            payments_df[['order_id', 'payment_method', 'payment_status', 
                        'payment_date', 'amount', 'transaction_fee']],
            on='order_id',
            how='left'
        )
        
        # Join with products to get unit price
        fact_df = fact_df.merge(
            products_df[['product_id', 'price']],
            on='product_id',
            how='left'
        )
        
        # Join with customer dimension to get customer_key
        fact_df = fact_df.merge(
            customer_dim_df[['customer_id', 'customer_key']],
            on='customer_id',
            how='left'
        )
        
        # Join with product dimension to get product_key
        fact_df = fact_df.merge(
            product_dim_df[['product_id', 'product_key']],
            on='product_id',
            how='left'
        )
        
        # Join with date dimension for various date keys
        # Order date
        fact_df = fact_df.merge(
            date_dim_df[['date_value', 'date_key']].rename(columns={'date_key': 'order_date_key'}),
            left_on='order_date',
            right_on='date_value',
            how='left'
        ).drop('date_value', axis=1)
        
        # Ship date
        fact_df = fact_df.merge(
            date_dim_df[['date_value', 'date_key']].rename(columns={'date_key': 'ship_date_key'}),
            left_on='ship_date',
            right_on='date_value',
            how='left'
        ).drop('date_value', axis=1)
        
        # Delivery date
        fact_df = fact_df.merge(
            date_dim_df[['date_value', 'date_key']].rename(columns={'date_key': 'delivery_date_key'}),
            left_on='delivery_date',
            right_on='date_value',
            how='left'
        ).drop('date_value', axis=1)
        
        # Payment date
        fact_df = fact_df.merge(
            date_dim_df[['date_value', 'date_key']].rename(columns={'date_key': 'payment_date_key'}),
            left_on='payment_date',
            right_on='date_value',
            how='left'
        ).drop('date_value', axis=1)
        
        # Calculate measures
        fact_df['unit_price'] = fact_df['price']
        fact_df['total_price'] = fact_df['quantity'] * fact_df['unit_price']
        fact_df['payment_amount'] = fact_df['amount']
        
        # Select final columns for fact table
        final_columns = [
            'order_id', 'customer_key', 'product_key',
            'order_date_key', 'ship_date_key', 'delivery_date_key', 'payment_date_key',
            'quantity', 'unit_price', 'total_price', 'shipping_cost', 'tax_amount',
            'payment_amount', 'transaction_fee',
            'order_status', 'payment_method', 'payment_status'
        ]
        
        fact_df = fact_df[final_columns]
        
        logger.info(f"Created fact table with {len(fact_df)} records")
        return fact_df