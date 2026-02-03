-- Monthly Revenue Analysis
-- Shows total revenue, order count, and average order value by month

SELECT 
    dd.year,
    dd.month,
    dd.month_name,
    COUNT(DISTINCT fs.order_id) as total_orders,
    SUM(fs.total_price) as gross_revenue,
    SUM(fs.shipping_cost) as shipping_revenue,
    SUM(fs.tax_amount) as tax_revenue,
    SUM(fs.total_price + fs.shipping_cost + fs.tax_amount) as total_revenue,
    ROUND(AVG(fs.total_price + fs.shipping_cost + fs.tax_amount), 2) as avg_order_value,
    COUNT(fs.sales_key) as total_line_items
FROM fact_sales fs
JOIN dim_dates dd ON fs.order_date_key = dd.date_key
WHERE fs.order_status = 'delivered'
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;

-- Monthly Revenue Growth Rate
WITH monthly_revenue AS (
    SELECT 
        dd.year,
        dd.month,
        dd.month_name,
        SUM(fs.total_price + fs.shipping_cost + fs.tax_amount) as total_revenue
    FROM fact_sales fs
    JOIN dim_dates dd ON fs.order_date_key = dd.date_key
    WHERE fs.order_status = 'delivered'
    GROUP BY dd.year, dd.month, dd.month_name
)
SELECT 
    year,
    month,
    month_name,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY year, month) as prev_month_revenue,
    ROUND(
        ((total_revenue - LAG(total_revenue) OVER (ORDER BY year, month)) / 
         LAG(total_revenue) OVER (ORDER BY year, month)) * 100, 2
    ) as growth_rate_percent
FROM monthly_revenue
ORDER BY year, month;