-- E-Commerce Data Warehouse Schema
-- Star Schema Design with Fact and Dimension Tables

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_dates CASCADE;

-- Dimension Table: Customers
-- Contains customer demographic and contact information
CREATE TABLE dim_customers (
    customer_key SERIAL PRIMARY KEY,
    customer_id INTEGER UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    country VARCHAR(50),
    registration_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Table: Products
-- Contains product catalog information
CREATE TABLE dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE NOT NULL,
    product_name VARCHAR(200),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    brand VARCHAR(50),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    weight_kg DECIMAL(8,3),
    dimensions VARCHAR(50),
    description TEXT,
    created_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Table: Dates
-- Date dimension for time-based analysis
CREATE TABLE dim_dates (
    date_key SERIAL PRIMARY KEY,
    date_value DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    day INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    week_of_year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact Table: Sales
-- Grain: One row per order line item
-- Contains transactional data with foreign keys to dimensions
CREATE TABLE fact_sales (
    sales_key SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    customer_key INTEGER REFERENCES dim_customers(customer_key),
    product_key INTEGER REFERENCES dim_products(product_key),
    order_date_key INTEGER REFERENCES dim_dates(date_key),
    ship_date_key INTEGER REFERENCES dim_dates(date_key),
    delivery_date_key INTEGER REFERENCES dim_dates(date_key),
    payment_date_key INTEGER REFERENCES dim_dates(date_key),
    
    -- Measures
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    shipping_cost DECIMAL(10,2),
    tax_amount DECIMAL(10,2),
    payment_amount DECIMAL(10,2),
    transaction_fee DECIMAL(10,2),
    
    -- Attributes
    order_status VARCHAR(20),
    payment_method VARCHAR(20),
    payment_status VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_order_date ON fact_sales(order_date_key);
CREATE INDEX idx_fact_sales_order_id ON fact_sales(order_id);

CREATE INDEX idx_dim_customers_id ON dim_customers(customer_id);
CREATE INDEX idx_dim_products_id ON dim_products(product_id);
CREATE INDEX idx_dim_dates_value ON dim_dates(date_value);

-- Add comments for documentation
COMMENT ON TABLE dim_customers IS 'Customer dimension containing demographic and contact information';
COMMENT ON TABLE dim_products IS 'Product dimension containing catalog and pricing information';
COMMENT ON TABLE dim_dates IS 'Date dimension for time-based analysis and reporting';
COMMENT ON TABLE fact_sales IS 'Sales fact table with grain of one row per order line item';

COMMENT ON COLUMN fact_sales.sales_key IS 'Surrogate key for the fact table';
COMMENT ON COLUMN fact_sales.order_id IS 'Business key linking to source order system';
COMMENT ON COLUMN fact_sales.quantity IS 'Number of units ordered';
COMMENT ON COLUMN fact_sales.unit_price IS 'Price per unit from product catalog';
COMMENT ON COLUMN fact_sales.total_price IS 'Total price for this line item (quantity * unit_price)';