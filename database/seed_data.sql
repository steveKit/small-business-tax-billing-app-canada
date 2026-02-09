-- Tax Billing Application Seed Data
-- Correct CRA Tax Rates for Canada 2025-2026

-- ============================================
-- FEDERAL TAX BRACKETS 2025 (Correct CRA values)
-- ============================================
INSERT INTO federal_tax_brackets (year, min_income, max_income, rate) VALUES
    (2025, 0.00, 57375.00, 0.1450),
    (2025, 57375.01, 114750.00, 0.2050),
    (2025, 114750.01, 177882.00, 0.2600),
    (2025, 177882.01, 253414.00, 0.2900),
    (2025, 253414.01, NULL, 0.3300);

-- ============================================
-- FEDERAL TAX BRACKETS 2026 (Correct CRA values)
-- ============================================
INSERT INTO federal_tax_brackets (year, min_income, max_income, rate) VALUES
    (2026, 0.00, 58523.00, 0.1400),
    (2026, 58523.01, 117045.00, 0.2050),
    (2026, 117045.01, 181440.00, 0.2600),
    (2026, 181440.01, 258482.00, 0.2900),
    (2026, 258482.01, NULL, 0.3300);

-- ============================================
-- PROVINCIAL TAX BRACKETS 2025 (Correct values)
-- ============================================

-- Ontario 2025
INSERT INTO provincial_tax_brackets (province, year, min_income, max_income, rate) VALUES
    ('ON', 2025, 0.00, 52886.00, 0.0505),
    ('ON', 2025, 52886.01, 105775.00, 0.0915),
    ('ON', 2025, 105775.01, 150000.00, 0.1116),
    ('ON', 2025, 150000.01, 220000.00, 0.1216),
    ('ON', 2025, 220000.01, NULL, 0.1316);

-- ============================================
-- PROVINCIAL TAX BRACKETS 2026 (Correct CRA values)
-- ============================================

-- Ontario 2026
INSERT INTO provincial_tax_brackets (province, year, min_income, max_income, rate) VALUES
    ('ON', 2026, 0.00, 53891.00, 0.0505),
    ('ON', 2026, 53891.01, 107785.00, 0.0915),
    ('ON', 2026, 107785.01, 150000.00, 0.1116),
    ('ON', 2026, 150000.01, 220000.00, 0.1216),
    ('ON', 2026, 220000.01, NULL, 0.1316);

-- ============================================
-- SALES TAX RATES 2025 (HST/GST/PST)
-- ============================================
INSERT INTO sales_tax_rates (province, year, gst_rate, pst_rate, hst_rate, qst_rate, tax_type) VALUES
    -- HST Provinces (combined federal+provincial)
    ('ON', 2025, 0.0500, 0.0000, 0.1300, 0.0000, 'HST');

-- ============================================
-- SALES TAX RATES 2026 (HST/GST/PST)
-- ============================================
INSERT INTO sales_tax_rates (province, year, gst_rate, pst_rate, hst_rate, qst_rate, tax_type) VALUES
    -- HST Provinces (combined federal+provincial)
    ('ON', 2026, 0.0500, 0.0000, 0.1300, 0.0000, 'HST');

-- ============================================
-- DEFAULT TAX YEAR SETTINGS
-- ============================================
INSERT INTO tax_years (year, presumed_annual_income, notes) VALUES
    (2025, 80000.00, 'Default presumed annual income for 2025 tax withholding calculations'),
    (2026, 80000.00, 'Default presumed annual income for 2026 tax withholding calculations');

-- ============================================
-- DEFAULT BUSINESS SETTINGS (placeholder)
-- ============================================
INSERT INTO business_settings (
    business_name,
    province,
    payment_terms,
    auto_backup_enabled,
    backup_retention_count
) VALUES (
    'My Business',
    'ON',
    'Net 30',
    TRUE,
    30
);
