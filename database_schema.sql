-- Expense Splitter Database Schema
-- This file documents the database structure for reference
-- People table - stores all individuals involved in expenses
CREATE TABLE person (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Recurring transactions table - templates for recurring expenses
CREATE TABLE recurring_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10, 2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    paid_by VARCHAR(100) NOT NULL,
    category VARCHAR(20) DEFAULT 'Other',
    recurrence_type VARCHAR(20) NOT NULL,
    -- 'weekly', 'monthly', 'yearly'
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    last_generated TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Expenses table - individual expense records
CREATE TABLE expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10, 2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    paid_by VARCHAR(100) NOT NULL,
    category VARCHAR(20) DEFAULT 'Other',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recurring_transaction_id INTEGER,
    FOREIGN KEY (recurring_transaction_id) REFERENCES recurring_transaction(id)
);
-- Expense splits table - defines how each expense is split among people
CREATE TABLE expense_split (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    person_name VARCHAR(100) NOT NULL,
    split_type VARCHAR(20) NOT NULL,
    -- 'equal', 'percentage', 'exact'
    split_value DECIMAL(10, 2),
    -- percentage value or exact amount (null for equal)
    calculated_amount DECIMAL(10, 2) NOT NULL,
    -- final amount this person owes
    FOREIGN KEY (expense_id) REFERENCES expense(id) ON DELETE CASCADE
);
-- Indexes for better performance
CREATE INDEX idx_expense_paid_by ON expense(paid_by);
CREATE INDEX idx_expense_category ON expense(category);
CREATE INDEX idx_expense_created_at ON expense(created_at);
CREATE INDEX idx_expense_split_expense_id ON expense_split(expense_id);
CREATE INDEX idx_expense_split_person_name ON expense_split(person_name);
CREATE INDEX idx_recurring_transaction_paid_by ON recurring_transaction(paid_by);
CREATE INDEX idx_recurring_transaction_is_active ON recurring_transaction(is_active);
-- Sample data for testing (optional)
-- Run these INSERT statements to populate with test data
-- Insert sample people
INSERT INTO person (name)
VALUES ('Shantanu'),
    ('Sanket'),
    ('Om');
-- Insert sample expenses with splits
-- (Note: In the actual application, this is handled by the Python code)
/*
 Database Design Notes:
 ======================
 
 1. **Person Table**: 
 - Stores unique individuals
 - Auto-created when mentioned in expenses
 - Simple name-based identification
 
 2. **Expense Table**:
 - Core expense records
 - Links to person who paid
 - Supports categories for analytics
 - Optional link to recurring transactions
 
 3. **ExpenseSplit Table**:
 - Defines how each expense is divided
 - Supports three split types: equal, percentage, exact
 - Stores calculated final amounts for each person
 - Cascade deletes with expenses
 
 4. **RecurringTransaction Table**:
 - Templates for regular expenses
 - Supports weekly/monthly/yearly recurrence
 - Tracks last generation date
 - Can be activated/deactivated
 
 5. **Split Calculation Logic**:
 - Priority: Exact amounts → Percentages → Equal splits
 - Remaining amount after exact/percentage is split equally
 - Validation ensures totals don't exceed 100%
 
 6. **Settlement Algorithm**:
 - Calculates net balance for each person (paid - owes)
 - Optimizes transactions to minimize settlement count
 - Matches debtors with creditors efficiently
 */