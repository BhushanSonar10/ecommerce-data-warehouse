-- Customer Analysis Queries
-- Customer lifetime value, segmentation, and behavior analysis

-- Customer Lifetime Value (CLV) Analysis
SELECT 
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.city,
    dc.state,
    COUNT(DISTINCT fs.order_id) as total_orders,
    SUM(fs.quantity) as total_items_purchased,
    SUM(fs.total_price + fs.shipping_cost + fs.tax_amount) as lifetime_value,
    ROUND(AVG(fs.total_price + fs.shipping_cost + fs.tax_amount), 2) as avg_order_value,
    MIN(dd.date_value) as first_order_date,
    MAX(dd.date_value) as last_order_date,
    MAX(dd.date_value) - MIN(dd.date_value) as customer_lifespan_days
FROM fact_sales fs
JOIN dim_customers dc ON fs.customer_key = dc.customer_key
JOIN dim_dates dd ON fs.order_date_key = dd.date_key
WHERE fs.order_status = 'delivered'
GROUP BY dc.customer_id, dc.first_name, dc.last_name, dc.city, dc.state
ORDER BY lifetime_value DESC;

-- Customer Segmentation by Purchase Behavior
WITH customer_metrics AS (
    SELECT 
        dc.customer_id,
        COUNT(DISTINCT fs.order_id) as order_count,
        SUM(fs.total_price + fs.shipping_cost + fs.tax_amount) as total_spent,
        ROUND(AVG(fs.total_price + fs.shipping_cost + fs.tax_amount), 2) as avg_order_value
    FROM fact_sales fs
    JOIN dim_customers dc ON fs.customer_key = dc.customer_key
    WHERE fs.order_status = 'delivered'
    GROUP BY dc.customer_id
)
SELECT 
    CASE 
        WHEN order_count >= 3 AND total_spent >= 1000 THEN 'High Value'
        WHEN order_count >= 2 AND total_spent >= 500 THEN 'Medium Value'
        WHEN order_count = 1 AND total_spent >= 200 THEN 'One-time High Spender'
        ELSE 'Low Value'
    END as customer_segment,
    COUNT(*) as customer_count,
    ROUND(AVG(total_spent), 2) as avg_lifetime_value,
    ROUND(AVG(order_count), 2) as avg_orders_per_customer,
    ROUND(AVG(avg_order_value), 2) as avg_order_value
FROM customer_metrics
GROUP BY 
    CASE 
        WHEN order_count >= 3 AND total_spent >= 1000 THEN 'High Value'
        WHEN order_count >= 2 AND total_spent >= 500 THEN 'Medium Value'
        WHEN order_count = 1 AND total_spent >= 200 THEN 'One-time High Spender'
        ELSE 'Low Value'
    END
ORDER BY avg_lifetime_value DESC;

-- Geographic Analysis - Revenue by Location
SELECT 
    dc.state,
    dc.city,
    COUNT(DISTINCT dc.customer_id) as unique_customers,
    COUNT(DISTINCT fs.order_id) as total_orders,
    SUM(fs.total_price + fs.shipping_cost + fs.tax_amount) as total_revenue,
    ROUND(AVG(fs.total_price + fs.shipping_cost + fs.tax_amount), 2) as avg_order_value,
    ROUND(SUM(fs.total_price + fs.shipping_cost + fs.tax_amount) / COUNT(DISTINCT dc.customer_id), 2) as revenue_per_customer
FROM fact_sales fs
JOIN dim_customers dc ON fs.customer_key = dc.customer_key
WHERE fs.order_status = 'delivered'
GROUP BY dc.state, dc.city
ORDER BY total_revenue DESC;

-- Customer Retention Analysis
WITH customer_order_months AS (
    SELECT 
        dc.customer_id,
        dd.year,
        dd.month,
        COUNT(DISTINCT fs.order_id) as orders_in_month
    FROM fact_sales fs
    JOIN dim_customers dc ON fs.customer_key = dc.customer_key
    JOIN dim_dates dd ON fs.order_date_key = dd.date_key
    WHERE fs.order_status = 'delivered'
    GROUP BY dc.customer_id, dd.year, dd.month
),
customer_activity AS (
    SELECT 
        customer_id,
        COUNT(*) as active_months,
        MIN(year * 12 + month) as first_month,
        MAX(year * 12 + month) as last_month
    FROM customer_order_months
    GROUP BY customer_id
)
SELECT 
    CASE 
        WHEN active_months = 1 THEN 'One-time Customer'
        WHEN last_month - first_month + 1 = active_months THEN 'Consistent Customer'
        ELSE 'Intermittent Customer'
    END as customer_type,
    COUNT(*) as customer_count,
    ROUND(AVG(active_months), 2) as avg_active_months,
    ROUND(AVG(last_month - first_month + 1), 2) as avg_customer_lifespan_months
FROM customer_activity
GROUP BY 
    CASE 
        WHEN active_months = 1 THEN 'One-time Customer'
        WHEN last_month - first_month + 1 = active_months THEN 'Consistent Customer'
        ELSE 'Intermittent Customer'
    END
ORDER BY customer_count DESC;