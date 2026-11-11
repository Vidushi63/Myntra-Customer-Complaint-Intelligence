CREATE DATABASE myntra_complaint_db;
USE myntra_complaint_db;
CREATE TABLE reviews (
    reviewId VARCHAR(100) PRIMARY KEY,
    content TEXT,
    score INT,
    review_date DATETIME,
    sentiment VARCHAR(20),
    category VARCHAR(100),
    priority VARCHAR(20),
    is_complaint BOOLEAN
);
SHOW TABLES;
SELECT COUNT(*) AS total_rows FROM reviews;

SELECT *
FROM reviews
LIMIT 10;

-- Find the overall complaint statistics
SELECT
    COUNT(*) AS total_reviews,
    SUM(is_complaint) AS total_complaints,
    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative_reviews,
    ROUND(AVG(score), 2) AS average_rating
FROM reviews;

-- Analyse complaints by category
SELECT category,COUNT(*) AS complaint_count
FROM reviews
WHERE is_complaint = 1
GROUP BY category
ORDER BY complaint_count DESC;

-- Verify complaint categories
SELECT
    COUNT(*) AS total_complaints,
    SUM(category IS NULL) AS null_categories,
    COUNT(DISTINCT category) AS distinct_categories
FROM reviews
WHERE is_complaint = 1;

-- Display all 8 categories
SELECT
    TRIM(category) AS category,
    COUNT(*) AS complaint_count
FROM reviews
WHERE is_complaint = 1
GROUP BY TRIM(category)
ORDER BY complaint_count DESC;

-- Analyse complaint priority
SELECT
    priority,
    COUNT(*) AS complaint_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM reviews WHERE is_complaint = 1),
        2
    ) AS percentage
FROM reviews
WHERE is_complaint = 1
GROUP BY priority
ORDER BY
    CASE priority
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
    END;
    
    -- Category vs priority analysis
    SELECT
    TRIM(category) AS category,
    priority,
    COUNT(*) AS complaint_count
FROM reviews
WHERE is_complaint = 1
GROUP BY TRIM(category), priority
ORDER BY
    CASE priority
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
    END,
    complaint_count DESC;

-- Sentiment analysis
SELECT
    sentiment,
    COUNT(*) AS total_reviews,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 2) AS percentage
FROM reviews
GROUP BY sentiment
ORDER BY total_reviews DESC;

-- Rating analysis
SELECT
    score AS rating,
    COUNT(*) AS total_reviews,
    SUM(is_complaint) AS complaints,
    ROUND(AVG(is_complaint) * 100, 2) AS complaint_percentage
FROM reviews
GROUP BY score
ORDER BY score;

-- Negative reviews by category
SELECT
    TRIM(category) AS category,
    COUNT(*) AS negative_reviews
FROM reviews
WHERE sentiment = 'Negative'
GROUP BY TRIM(category)
ORDER BY negative_reviews DESC;

-- High-priority complaints by category
SELECT
    TRIM(category) AS category,
    COUNT(*) AS high_priority_complaints
FROM reviews
WHERE is_complaint = 1
AND priority = 'High'
GROUP BY TRIM(category)
ORDER BY high_priority_complaints DESC;

-- Customer complaint percentage
SELECT
    COUNT(*) AS total_reviews,
    SUM(is_complaint) AS total_complaints,
    ROUND(AVG(is_complaint) * 100, 2) AS complaint_percentage,
    ROUND((1 - AVG(is_complaint)) * 100, 2) AS non_complaint_percentage
FROM reviews;

-- Average rating by sentiment
SELECT
    sentiment,
    ROUND(AVG(score), 2) AS average_rating,
    COUNT(*) AS total_reviews
FROM reviews
GROUP BY sentiment
ORDER BY average_rating DESC;

-- Complaint trends by month
SELECT
    DATE_FORMAT(review_date, '%Y-%m') AS review_month,
    COUNT(*) AS total_reviews,
    SUM(is_complaint) AS total_complaints
FROM reviews
GROUP BY DATE_FORMAT(review_date, '%Y-%m')
ORDER BY review_month;

-- Recent complaints
SELECT reviewId, review_date, content, category, priority,score
FROM reviews
WHERE is_complaint = 1
ORDER BY review_date DESC
LIMIT 20;

-- Category-wise complaint percentage
SELECT
    TRIM(category) AS category,
    COUNT(*) AS complaint_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM reviews WHERE is_complaint = 1),
        2
    ) AS complaint_percentage
FROM reviews
WHERE is_complaint = 1
GROUP BY TRIM(category)
ORDER BY complaint_count DESC;

-- Final overall business summary
SELECT
    COUNT(*) AS total_reviews,
    SUM(is_complaint) AS total_complaints,
    COUNT(*) - SUM(is_complaint) AS non_complaints,
    ROUND(AVG(score), 2) AS average_rating,
    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END)
        AS negative_reviews,
    SUM(CASE WHEN priority = 'High' AND is_complaint = 1 THEN 1 ELSE 0 END)
        AS high_priority_complaints,
    ROUND(AVG(is_complaint) * 100, 2)
        AS complaint_percentage
FROM reviews;
