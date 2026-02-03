-- Test Queries for E-Commerce Data Warehouse
-- Run these queries to verify the data warehouse is working correctly

-- 1. Basic row counts to verify data loading
SELECT 'dim_customers' as table_name, COUNT(*) as row_count FROM dim_customers
UNION ALL
SELECT 'dim_products' as table_name, COUNT(*) as row_count FROM dim_products
UNION ALL
SELECT 'dim_dates' as table_name, COUNT(*) as row_count FROM dim_dates
UNION ALL
SELECT 'fact_sales' as table_name, COUNT(*) as row_count FROM fact_sales;

-- 2. Sample data from each table
SELECT 'Customer Sample:' as info;
SELECT customer_id, first_name, last_name, city, state 
FROM dim_customers 
LIMIT 3;

SELECT 'Product Sample:' as info;
SELECT product_id, product_name, category, brand, price 
FROM dim_products 
LIMIT 3;

SELECT 'Sales Sample:' as info;
SELECT order_id, quantity, unit_price, total_price, order_status 
FROM fact_sales 
LIMIT 3;

-- 3. Test joins between fact and dimensions
SELECT 'Join Test - Customer Orders:' as info;
SELECT 
    dc.first_name,
    dc.last_name,
    dp.product_name,
    fs.quantity,
    fs.total_price
FROM fact_sales fs
JOIN dim_customers dc ON fs.customer_key = dc.customer_key
JOIN dim_products dp ON fs.product_key = dp.product_key
LIMIT 5;

-- 4. Simple analytics query
SELECT 'Monthly Revenue Summary:' as info;
SELECT 
    dd.month_name,
    COUNT(DISTINCT fs.order_id) as orders,
    SUM(fs.total_price) as revenue
FROM fact_sales fs
JOIN dim_dates dd ON fs.order_date_key = dd.date_key
GROUP BY dd.month, dd.month_name
ORDER BY dd.month;

-- 5. Data quality check
SELECT 'Data Quality Check:' as info;
SELECT 
    'Null customer keys' as check_name,
    COUNT(*) as issue_count
FROM fact_sales 
WHERE customer_key IS NULL
UNION ALL
SELECT 
    'Null product keys' as check_name,
    COUNT(*) as issue_count
FROM fact_sales 
WHERE product_key IS NULL
UNION ALL
SELECT 
    'Negative quantities' as check_name,
    COUNT(*) as issue_count
FROM fact_sales 
WHERE quantity < 0
UNION ALL
SELECT 
    'Zero or negative prices' as check_name,
    COUNT(*) as issue_count
FROM fact_sales 
WHERE unit_price <= 0;