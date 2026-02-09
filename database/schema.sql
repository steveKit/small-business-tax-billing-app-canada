-- Tax Billing Application Database Schema
-- PostgreSQL with UUID primary keys

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- BUSINESS SETTINGS TABLE
-- ============================================
CREATE TABLE business_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(50) NOT NULL DEFAULT 'ON',
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    hst_number VARCHAR(50),
    payment_terms VARCHAR(100) DEFAULT 'Net 30',
    payment_instructions TEXT,
    backup_path VARCHAR(500),
    auto_backup_enabled BOOLEAN DEFAULT TRUE,
    backup_retention_count INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CLIENTS TABLE
-- ============================================
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(50),
    postal_code VARCHAR(20),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for active clients lookup
CREATE INDEX idx_clients_active ON clients(is_active) WHERE is_active = TRUE;

-- ============================================
-- TAX YEAR SETTINGS TABLE
-- ============================================
CREATE TABLE tax_years (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INTEGER NOT NULL UNIQUE,
    presumed_annual_income DECIMAL(12, 2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FEDERAL TAX BRACKETS TABLE
-- ============================================
CREATE TABLE federal_tax_brackets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INTEGER NOT NULL,
    min_income DECIMAL(12, 2) NOT NULL,
    max_income DECIMAL(12, 2), -- NULL means no upper limit
    rate DECIMAL(5, 4) NOT NULL, -- e.g., 0.1500 for 15%
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_federal_bracket UNIQUE (year, min_income)
);

-- Index for year lookup
CREATE INDEX idx_federal_tax_brackets_year ON federal_tax_brackets(year);

-- ============================================
-- PROVINCIAL TAX BRACKETS TABLE
-- ============================================
CREATE TABLE provincial_tax_brackets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    province VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    min_income DECIMAL(12, 2) NOT NULL,
    max_income DECIMAL(12, 2), -- NULL means no upper limit
    rate DECIMAL(5, 4) NOT NULL, -- e.g., 0.0505 for 5.05%
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_provincial_bracket UNIQUE (province, year, min_income)
);

-- Index for province/year lookup
CREATE INDEX idx_provincial_tax_brackets_province_year ON provincial_tax_brackets(province, year);

-- ============================================
-- HST/GST/PST RATES TABLE
-- ============================================
CREATE TABLE sales_tax_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    province VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    gst_rate DECIMAL(5, 4) NOT NULL DEFAULT 0.0500, -- Federal GST (5%)
    pst_rate DECIMAL(5, 4) DEFAULT 0.0000, -- Provincial Sales Tax
    hst_rate DECIMAL(5, 4) DEFAULT 0.0000, -- Harmonized Sales Tax (replaces GST+PST)
    qst_rate DECIMAL(5, 4) DEFAULT 0.0000, -- Quebec Sales Tax
    tax_type VARCHAR(20) NOT NULL, -- 'HST', 'GST+PST', 'GST+QST', 'GST'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_sales_tax UNIQUE (province, year)
);

-- Index for province/year lookup
CREATE INDEX idx_sales_tax_rates_province_year ON sales_tax_rates(province, year);

-- ============================================
-- INVOICES TABLE
-- ============================================
CREATE TYPE invoice_status AS ENUM ('draft', 'pending', 'paid', 'cancelled');

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL, -- Single line description of work
    billed_date DATE NOT NULL,
    due_date DATE NOT NULL,
    year_billed INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM billed_date)::INTEGER) STORED,
    subtotal DECIMAL(12, 2) NOT NULL,
    tax_rate DECIMAL(5, 4) NOT NULL, -- The rate applied at time of invoice
    tax_type VARCHAR(20) NOT NULL, -- 'HST', 'GST+PST', etc.
    tax_amount DECIMAL(12, 2) NOT NULL,
    total DECIMAL(12, 2) NOT NULL,
    status invoice_status NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_invoices_client ON invoices(client_id);
CREATE INDEX idx_invoices_year ON invoices(year_billed);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_billed_date ON invoices(billed_date);

-- ============================================
-- PAYMENTS TABLE
-- ============================================
CREATE TYPE payment_method AS ENUM ('bank_transfer', 'cheque', 'cash', 'credit_card', 'e_transfer', 'other');

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
    amount DECIMAL(12, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method payment_method NOT NULL DEFAULT 'bank_transfer',
    reference_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for invoice lookup
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_date ON payments(payment_date);

-- ============================================
-- BACKUP LOG TABLE
-- ============================================
CREATE TABLE backup_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT,
    backup_type VARCHAR(50) NOT NULL, -- 'auto', 'manual'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_business_settings_updated_at
    BEFORE UPDATE ON business_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tax_years_updated_at
    BEFORE UPDATE ON tax_years
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS
-- ============================================

-- View for tax summary by year
CREATE OR REPLACE VIEW v_tax_summary AS
SELECT 
    i.year_billed,
    COUNT(*) FILTER (WHERE i.status = 'paid') AS paid_invoice_count,
    COUNT(*) FILTER (WHERE i.status = 'pending') AS pending_invoice_count,
    COALESCE(SUM(i.subtotal) FILTER (WHERE i.status = 'paid'), 0) AS total_revenue_paid,
    COALESCE(SUM(i.subtotal) FILTER (WHERE i.status = 'pending'), 0) AS total_revenue_pending,
    COALESCE(SUM(i.tax_amount) FILTER (WHERE i.status = 'paid'), 0) AS total_tax_collected_paid,
    COALESCE(SUM(i.tax_amount) FILTER (WHERE i.status = 'pending'), 0) AS total_tax_collected_pending,
    COALESCE(SUM(i.total) FILTER (WHERE i.status = 'paid'), 0) AS total_amount_paid,
    COALESCE(SUM(i.total) FILTER (WHERE i.status = 'pending'), 0) AS total_amount_pending
FROM invoices i
WHERE i.status IN ('paid', 'pending')
GROUP BY i.year_billed;

-- View for client invoice summary
CREATE OR REPLACE VIEW v_client_summary AS
SELECT 
    c.id AS client_id,
    c.name AS client_name,
    COUNT(i.id) AS total_invoices,
    COALESCE(SUM(i.total), 0) AS total_billed,
    COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.total ELSE 0 END), 0) AS total_paid,
    COALESCE(SUM(CASE WHEN i.status = 'pending' THEN i.total ELSE 0 END), 0) AS total_pending
FROM clients c
LEFT JOIN invoices i ON c.id = i.client_id
GROUP BY c.id, c.name;
