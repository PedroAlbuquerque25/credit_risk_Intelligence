-- ================================================
-- Credit Risk Intelligence — SQL Business Queries
-- Canadian Banking Project
-- ================================================

-- Query 1: Default rate by age group
SELECT 
    age_group,
    COUNT(*) as total_customers,
    SUM(SeriousDlqin2yrs) as total_defaults,
    ROUND(AVG(SeriousDlqin2yrs) * 100, 2) as default_rate_pct
FROM customers
GROUP BY age_group
ORDER BY default_rate_pct DESC;

-- Query 2: Average profile by customer segment
SELECT 
    cluster_name,
    COUNT(*) as total_customers,
    ROUND(AVG(MonthlyIncome), 2) as avg_income,
    ROUND(AVG(DebtRatio), 2) as avg_debt_ratio,
    ROUND(AVG(total_late_payments), 2) as avg_late_payments,
    ROUND(AVG(SeriousDlqin2yrs) * 100, 2) as default_rate_pct
FROM segments
GROUP BY cluster_name
ORDER BY avg_income DESC;

-- Query 3: Top 10 highest risk customers
SELECT actual, probability, result_type
FROM predictions
ORDER BY probability DESC
LIMIT 10;

-- Query 4: Model performance distribution
SELECT 
    result_type,
    COUNT(*) as volume,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM predictions), 2) as share_pct
FROM predictions
GROUP BY result_type
ORDER BY volume DESC;

-- Query 5: Default rate by credit utilization band
SELECT 
    CASE 
        WHEN RevolvingUtilizationOfUnsecuredLines < 0.3 THEN '1. Low (<30%)'
        WHEN RevolvingUtilizationOfUnsecuredLines < 0.7 THEN '2. Medium (30-70%)'
        WHEN RevolvingUtilizationOfUnsecuredLines <= 1.0 THEN '3. High (70-100%)'
        ELSE '4. Over Limit (>100%)'
    END as utilization_band,
    COUNT(*) as total_customers,
    ROUND(AVG(SeriousDlqin2yrs) * 100, 2) as default_rate_pct
FROM customers
GROUP BY utilization_band
ORDER BY utilization_band ASC;