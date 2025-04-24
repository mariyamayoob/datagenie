-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS datagenie;
USE datagenie;

-- Create table: customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    customer_since DATE,
    status VARCHAR(20) -- e.g., Active, Inactive, Suspended
);

-- Create table: credit_transactions
CREATE TABLE IF NOT EXISTS credit_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    transaction_date DATE,
    amount DECIMAL(10, 2),
    transaction_type VARCHAR(50), -- e.g., Purchase, Payment, Fee
    description TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create table: loan_transactions
CREATE TABLE IF NOT EXISTS loan_transactions (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    loan_type VARCHAR(50), -- e.g., Auto, Home, Consumer
    loan_amount DECIMAL(12, 2),
    opened_date DATE,
    maturity_date DATE,
    status VARCHAR(20), -- e.g., Active, Closed, Defaulted
    interest_rate DECIMAL(5, 2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Insert demo data if empty
-- Customers
INSERT INTO customers (first_name, last_name, email, phone, customer_since, status)
SELECT * FROM (
    SELECT 'Alice', 'Johnson', 'alice.j@example.com', '1234567890', '2021-03-01', 'Active' UNION ALL
    SELECT 'Bob', 'Smith', 'bob.smith@example.com', '2345678901', '2022-06-15', 'Active' UNION ALL
    SELECT 'Carol', 'Lee', 'carol.lee@example.com', '3456789012', '2020-09-10', 'Suspended' UNION ALL
    SELECT 'David', 'Kim', 'david.kim@example.com', '4567890123', '2023-01-25', 'Active' UNION ALL
    SELECT 'Eve', 'Martinez', 'eve.m@example.com', '5678901234', '2021-11-30', 'Inactive' UNION ALL
    SELECT 'Frank', 'White', 'frank.w@example.com', '6789012345', '2022-03-19', 'Active' UNION ALL
    SELECT 'Grace', 'Chen', 'grace.c@example.com', '7890123456', '2020-02-14', 'Active' UNION ALL
    SELECT 'Hank', 'Green', 'hank.g@example.com', '8901234567', '2023-04-02', 'Active' UNION ALL
    SELECT 'Ivy', 'Nguyen', 'ivy.n@example.com', '9012345678', '2019-08-08', 'Inactive' UNION ALL
    SELECT 'Jack', 'Brown', 'jack.b@example.com', '0123456789', '2021-05-21', 'Active'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM customers);

-- Credit transactions
INSERT INTO credit_transactions (customer_id, transaction_date, amount, transaction_type, description)
SELECT customer_id, CURDATE() - INTERVAL FLOOR(RAND() * 365) DAY, ROUND(RAND() * 1000, 2), 
    ELT(FLOOR(1 + RAND() * 3), 'Purchase', 'Payment', 'Fee'), 'Sample transaction'
FROM customers
ORDER BY RAND()
LIMIT 50;

-- Loan transactions
INSERT INTO loan_transactions (customer_id, loan_type, loan_amount, opened_date, maturity_date, status, interest_rate)
SELECT customer_id, 
       ELT(FLOOR(1 + RAND() * 3), 'Auto', 'Home', 'Consumer'), 
       ROUND(RAND() * 20000 + 5000, 2),
       CURDATE() - INTERVAL FLOOR(RAND() * 1000) DAY,
       CURDATE() + INTERVAL FLOOR(RAND() * 1000) DAY,
       ELT(FLOOR(1 + RAND() * 3), 'Active', 'Closed', 'Defaulted'),
       ROUND(RAND() * 10, 2)
FROM customers
ORDER BY RAND()
LIMIT 25;
