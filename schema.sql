-- Drop tables if they exist
DROP TABLE IF EXISTS dataset_score_issues CASCADE;
DROP TABLE IF EXISTS dataset_version_scores CASCADE;
DROP TABLE IF EXISTS annotations CASCADE;
DROP TABLE IF EXISTS dataset_versions CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS domains CASCADE;
DROP TABLE IF EXISTS formats CASCADE;

-- Domains lookup table
CREATE TABLE domains (
    domain_id SERIAL PRIMARY KEY,
    domain_name VARCHAR(100) NOT NULL
);

-- Formats lookup table
CREATE TABLE formats (
    format_id SERIAL PRIMARY KEY,
    format_name VARCHAR(100) NOT NULL
);

-- Users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL
);

-- User Roles
CREATE TABLE user_roles (
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    role_id INT REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Datasets
CREATE TABLE datasets (
    dataset_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    domain VARCHAR(100),
    format VARCHAR(100),
    source VARCHAR(255),
    created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dataset Versions
CREATE TABLE dataset_versions (
    version_id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    version_tag VARCHAR(50) NOT NULL,
    changelog TEXT,
    file_size_mb NUMERIC(10,2),
    total_samples INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Annotations
CREATE TABLE annotations (
    annotation_id SERIAL PRIMARY KEY,
    version_id INT REFERENCES dataset_versions(version_id) ON DELETE CASCADE,
    annotated_by INT REFERENCES users(user_id),
    sample_id VARCHAR(100),
    label VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    annotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dataset Version Scores
CREATE TABLE dataset_version_scores (
    score_id SERIAL PRIMARY KEY,
    version_id INT REFERENCES dataset_versions(version_id) ON DELETE CASCADE,
    overall_score NUMERIC(5,2),
    completeness NUMERIC(5,2),
    accuracy NUMERIC(5,2),
    consistency NUMERIC(5,2),
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dataset Score Issues
CREATE TABLE dataset_score_issues (
    issue_id SERIAL PRIMARY KEY,
    score_id INT REFERENCES dataset_version_scores(score_id) ON DELETE CASCADE,
    issue_type VARCHAR(100),
    description TEXT,
    severity VARCHAR(50)
);

-- -------------------------
-- SAMPLE DATA
-- -------------------------

INSERT INTO domains (domain_name) VALUES ('Computer Vision'), ('NLP'), ('Healthcare'), ('Finance'), ('Robotics');

INSERT INTO formats (format_name) VALUES ('CSV'), ('JSON'), ('Parquet'), ('HDF5'), ('TFRecord');

INSERT INTO roles (role_name) VALUES ('Admin'), ('Annotator'), ('Reviewer'), ('Viewer');

INSERT INTO users (name, email, password_hash) VALUES
('Alice Johnson', 'alice@example.com', 'hashed_pw'),
('Bob Smith', 'bob@example.com', 'hashed_pw'),
('Carol White', 'carol@example.com', 'hashed_pw'),
('David Brown', 'david@example.com', 'hashed_pw');

INSERT INTO user_roles (user_id, role_id) VALUES
(1, 1), (2, 2), (3, 3), (4, 4);

INSERT INTO datasets (name, description, domain, format, source, created_by) VALUES
('ImageNet Subset', 'Subset of ImageNet for CV tasks', 'Computer Vision', 'TFRecord', 'kaggle.com', 1),
('Twitter Sentiment', 'Tweets labeled for sentiment analysis', 'NLP', 'CSV', 'twitter.com', 2),
('Medical Records', 'Anonymized patient records', 'Healthcare', 'JSON', 'hospital_data.org', 1),
('Stock Prices', 'Daily stock price history', 'Finance', 'CSV', 'yahoo_finance.com', 3);

INSERT INTO dataset_versions (dataset_id, version_tag, changelog, file_size_mb, total_samples) VALUES
(1, 'v1.0', 'Initial release', 512.50, 10000),
(1, 'v1.1', 'Removed duplicates', 498.00, 9800),
(2, 'v1.0', 'Initial release', 45.20, 50000),
(3, 'v1.0', 'First anonymized batch', 120.00, 3000),
(4, 'v1.0', 'Historical data 2020-2024', 89.50, 25000);

INSERT INTO annotations (version_id, annotated_by, sample_id, label, status) VALUES
(1, 2, 'img_001', 'cat', 'completed'),
(1, 2, 'img_002', 'dog', 'completed'),
(2, 3, 'img_003', 'car', 'pending'),
(3, 2, 'tweet_001', 'positive', 'completed'),
(3, 3, 'tweet_002', 'negative', 'completed'),
(4, 2, 'rec_001', 'diabetic', 'review');

INSERT INTO dataset_version_scores (version_id, overall_score, completeness, accuracy, consistency) VALUES
(1, 92.50, 95.00, 91.00, 91.50),
(2, 94.00, 97.00, 93.00, 92.00),
(3, 88.00, 85.00, 90.00, 89.00),
(4, 79.50, 80.00, 78.00, 80.50),
(5, 96.00, 98.00, 95.00, 95.00);

INSERT INTO dataset_score_issues (score_id, issue_type, description, severity) VALUES
(1, 'Missing Values', 'Some image labels are missing', 'medium'),
(2, 'Duplicate Entries', 'Minor duplicate tweets detected', 'low'),
(3, 'Inconsistent Labels', 'Label format inconsistency in batch 3', 'high'),
(4, 'Outliers', 'Extreme stock price values detected', 'medium');