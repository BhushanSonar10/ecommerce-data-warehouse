-- Payment Method and Transaction Analysis
-- Analysis of payment preferences, transaction fees, and payment success rates

-- Payment Method Performance
SELECT 
    fs.payment_method,
    COUNT(DISTINCT fs.order_id) as total_orders,
    SUM(fs.payment_amount) as total_payment_amount,
    SUM(fs.transaction_fee) as total_transaction_fees,
    ROUND(AVG(fs.payment_amount), 2) as avg_payment_amount,
    ROUND(AVG(fs.transaction_fee), 2) as avg_transaction_fee,
    ROUND((SUM(fs.transaction_fee) / SUM(fs.payment_amount)) * 100, 3) as fee_percentage,
    COUNT(CASE WHEN fs.payment_status = 'completed' THEN 1 END) as successful_payments,
    ROUND(
        (COUNT(CASE WHEN fs.payment_status = 'completed' THEN 1 END) * 100.0 / COUNT(*)), 2
    ) as success_rate_percent
FROM fact_sales fs
GROUP BY fs.payment_method
ORDER BY total_payment_amount DESC;

-- Monthly Payment Trends
SELECT 
    dd.year,
    dd.month,
    dd.month_name,
    fs.payment_method,
    COUNT(DISTINCT fs.order_id) as order_count,
    SUM(fs.payment_amount) as total_amount,
    ROUND(AVG(fs.payment_amount), 2) as avg_payment_amount
FROM fact_sales fs
JOIN dim_dates dd ON fs.payment_date_key = dd.date_key
WHERE fs.payment_status = 'completed'
GROUP BY dd.year, dd.month, dd.month_name, fs.payment_method
ORDER BY dd.year, dd.month, fs.payment_method;

-- Transaction Fee Analysis by Payment Method
SELECT 
    fs.payment_method,
    COUNT(*) as transaction_count,
    SUM(fs.payment_amount) as total_payment_amount,
    SUM(fs.transaction_fee) as total_fees,
    ROUND(AVG(fs.transaction_fee), 2) as avg_fee_per_transaction,
    ROUND(MIN(fs.transaction_fee), 2) as min_fee,
    ROUND(MAX(fs.transaction_fee), 2) as max_fee,
    ROUND((SUM(fs.transaction_fee) / SUM(fs.payment_amount)) * 100, 3) as effective_fee_rate_percent
FROM fact_sales fs
WHERE fs.payment_status = 'completed'
GROUP BY fs.payment_method
ORDER BY effective_fee_rate_percent DESC;

-- Payment Amount Distribution
SELECT 
    CASE 
        WHEN fs.payment_amount < 100 THEN 'Under $100'
        WHEN fs.payment_amount < 300 THEN '$100 - $299'
        WHEN fs.payment_amount < 500 THEN '$300 - $499'
        WHEN fs.payment_amount < 1000 THEN '$500 - $999'
        ELSE '$1000+'
    END as payment_range,
    COUNT(*) as transaction_count,
    ROUND(AVG(fs.payment_amount), 2) as avg_payment_amount,
    SUM(fs.payment_amount) as total_amount,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_sales WHERE payment_status = 'completed')), 2) as percentage_of_transactions
FROM fact_sales fs
WHERE fs.payment_status = 'completed'
GROUP BY 
    CASE 
        WHEN fs.payment_amount < 100 THEN 'Under $100'
        WHEN fs.payment_amount < 300 THEN '$100 - $299'
        WHEN fs.payment_amount < 500 THEN '$300 - $499'
        WHEN fs.payment_amount < 1000 THEN '$500 - $999'
        ELSE '$1000+'
    END
ORDER BY 
    MIN(CASE 
        WHEN fs.payment_amount < 100 THEN 1
        WHEN fs.payment_amount < 300 THEN 2
        WHEN fs.payment_amount < 500 THEN 3
        WHEN fs.payment_amount < 1000 THEN 4
        ELSE 5
    END);

-- Daily Payment Processing Analysis
SELECT 
    dd.date_value,
    dd.day_name,
    COUNT(DISTINCT fs.order_id) as orders_processed,
    SUM(fs.payment_amount) as total_processed_amount,
    COUNT(CASE WHEN fs.payment_status = 'completed' THEN 1 END) as successful_payments,
    COUNT(CASE WHEN fs.payment_status != 'completed' THEN 1 END) as failed_payments,
    ROUND(
        (COUNT(CASE WHEN fs.payment_status = 'completed' THEN 1 END) * 100.0 / COUNT(*)), 2
    ) as success_rate_percent
FROM fact_sales fs
JOIN dim_dates dd ON fs.payment_date_key = dd.date_key
GROUP BY dd.date_value, dd.day_name
ORDER BY dd.date_value;