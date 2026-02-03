-- Top Products Analysis
-- Shows best performing products by revenue, quantity, and order frequency

-- Top 10 Products by Revenue
SELECT 
    dp.product_name,
    dp.category,
    dp.brand,
    COUNT(DISTINCT fs.order_id) as order_count,
    SUM(fs.quantity) as total_quantity_sold,
    SUM(fs.total_price) as total_revenue,
    ROUND(AVG(fs.unit_price), 2) as avg_selling_price,
    ROUND(SUM(fs.total_price) / SUM(fs.quantity), 2) as revenue_per_unit
FROM fact_sales fs
JOIN dim_products dp ON fs.product_key = dp.product_key
WHERE fs.order_status = 'delivered'
GROUP BY dp.product_id, dp.product_name, dp.category, dp.brand
ORDER BY total_revenue DESC
LIMIT 10;

-- Top Products by Quantity Sold
SELECT 
    dp.product_name,
    dp.category,
    dp.brand,
    SUM(fs.quantity) as total_quantity_sold,
    COUNT(DISTINCT fs.order_id) as order_count,
    SUM(fs.total_price) as total_revenue,
    ROUND(AVG(fs.quantity), 2) as avg_quantity_per_order
FROM fact_sales fs
JOIN dim_products dp ON fs.product_key = dp.product_key
WHERE fs.order_status = 'delivered'
GROUP BY dp.product_id, dp.product_name, dp.category, dp.brand
ORDER BY total_quantity_sold DESC
LIMIT 10;

-- Product Performance by Category
SELECT 
    dp.category,
    COUNT(DISTINCT dp.product_id) as unique_products,
    COUNT(DISTINCT fs.order_id) as total_orders,
    SUM(fs.quantity) as total_quantity_sold,
    SUM(fs.total_price) as total_revenue,
    ROUND(AVG(fs.total_price), 2) as avg_line_item_value,
    ROUND(SUM(fs.total_price) / COUNT(DISTINCT fs.order_id), 2) as revenue_per_order
FROM fact_sales fs
JOIN dim_products dp ON fs.product_key = dp.product_key
WHERE fs.order_status = 'delivered'
GROUP BY dp.category
ORDER BY total_revenue DESC;

-- Product Profitability Analysis (Revenue vs Cost)
SELECT 
    dp.product_name,
    dp.category,
    dp.brand,
    SUM(fs.quantity) as total_quantity_sold,
    SUM(fs.total_price) as total_revenue,
    SUM(fs.quantity * dp.cost) as total_cost,
    SUM(fs.total_price) - SUM(fs.quantity * dp.cost) as gross_profit,
    ROUND(
        ((SUM(fs.total_price) - SUM(fs.quantity * dp.cost)) / SUM(fs.total_price)) * 100, 2
    ) as gross_margin_percent
FROM fact_sales fs
JOIN dim_products dp ON fs.product_key = dp.product_key
WHERE fs.order_status = 'delivered'
GROUP BY dp.product_id, dp.product_name, dp.category, dp.brand
HAVING SUM(fs.quantity) > 0
ORDER BY gross_profit DESC;