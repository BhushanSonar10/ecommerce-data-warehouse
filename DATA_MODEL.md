# Data Model Documentation

## Overview

This document describes the star schema data model implemented for the e-commerce data warehouse. The design follows dimensional modeling best practices to support efficient analytical queries.

## Star Schema Design

### Fact Table: fact_sales

**Grain**: One row per order line item (most granular level)

This means each row represents a single product within a customer order, allowing for detailed analysis while supporting aggregation to higher levels.

#### Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| sales_key | SERIAL (PK) | Surrogate key | 1, 2, 3... |
| order_id | INTEGER | Business key from source system | 1001, 1002... |
| customer_key | INTEGER (FK) | Foreign key to dim_customers | 1, 2, 3... |
| product_key | INTEGER (FK) | Foreign key to dim_products | 1, 2, 3... |
| order_date_key | INTEGER (FK) | Foreign key to dim_dates | 18628 |
| ship_date_key | INTEGER (FK) | Foreign key to dim_dates | 18629 |
| delivery_date_key | INTEGER (FK) | Foreign key to dim_dates | 18632 |
| payment_date_key | INTEGER (FK) | Foreign key to dim_dates | 18628 |

#### Measures (Numeric Facts)

| Column | Type | Description | Business Rule |
|--------|------|-------------|---------------|
| quantity | INTEGER | Number of units ordered | Must be > 0 |
| unit_price | DECIMAL(10,2) | Price per unit | Must be > 0 |
| total_price | DECIMAL(10,2) | quantity × unit_price | Calculated field |
| shipping_cost | DECIMAL(10,2) | Shipping charges | ≥ 0 |
| tax_amount | DECIMAL(10,2) | Tax charges | ≥ 0 |
| payment_amount | DECIMAL(10,2) | Total payment processed | > 0 |
| transaction_fee | DECIMAL(10,2) | Payment processing fee | ≥ 0 |

#### Attributes (Descriptive Fields)

| Column | Type | Description | Values |
|--------|------|-------------|--------|
| order_status | VARCHAR(20) | Order fulfillment status | delivered, shipped, pending |
| payment_method | VARCHAR(20) | Payment type | credit_card, debit_card, paypal |
| payment_status | VARCHAR(20) | Payment processing status | completed, pending, failed |

### Dimension Tables

#### dim_customers

Customer demographic and contact information for customer analysis.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| customer_key | SERIAL (PK) | Surrogate key | 1, 2, 3... |
| customer_id | INTEGER (UK) | Business key | 1001, 1002... |
| first_name | VARCHAR(50) | Customer first name | John |
| last_name | VARCHAR(50) | Customer last name | Smith |
| email | VARCHAR(100) | Email address | john.smith@email.com |
| phone | VARCHAR(20) | Phone number | 555-0101 |
| address | VARCHAR(200) | Street address | 123 Main St |
| city | VARCHAR(50) | City | New York |
| state | VARCHAR(50) | State/Province | NY |
| zip_code | VARCHAR(10) | Postal code | 10001 |
| country | VARCHAR(50) | Country | USA |
| registration_date | DATE | Account creation date | 2023-01-15 |

#### dim_products

Product catalog information for product performance analysis.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| product_key | SERIAL (PK) | Surrogate key | 1, 2, 3... |
| product_id | INTEGER (UK) | Business key | 1001, 1002... |
| product_name | VARCHAR(200) | Product name | iPhone 14 |
| category | VARCHAR(50) | Product category | Electronics |
| subcategory | VARCHAR(50) | Product subcategory | Smartphones |
| brand | VARCHAR(50) | Brand name | Apple |
| price | DECIMAL(10,2) | Current selling price | 999.00 |
| cost | DECIMAL(10,2) | Product cost | 650.00 |
| weight_kg | DECIMAL(8,3) | Product weight | 0.172 |
| dimensions | VARCHAR(50) | Product dimensions | 146.7x71.5x7.8mm |
| description | TEXT | Product description | Latest iPhone model |
| created_date | DATE | Product creation date | 2023-01-01 |

#### dim_dates

Time dimension for temporal analysis and reporting.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| date_key | SERIAL (PK) | Surrogate key | 18628 |
| date_value | DATE (UK) | Actual date | 2023-05-01 |
| year | INTEGER | Year | 2023 |
| quarter | INTEGER | Quarter (1-4) | 2 |
| month | INTEGER | Month (1-12) | 5 |
| month_name | VARCHAR(20) | Month name | May |
| day | INTEGER | Day of month (1-31) | 1 |
| day_of_week | INTEGER | Day of week (1-7) | 1 (Monday) |
| day_name | VARCHAR(20) | Day name | Monday |
| week_of_year | INTEGER | Week number (1-53) | 18 |
| is_weekend | BOOLEAN | Weekend flag | FALSE |
| is_holiday | BOOLEAN | Holiday flag | FALSE |

## Relationships

### Foreign Key Constraints

```sql
fact_sales.customer_key → dim_customers.customer_key
fact_sales.product_key → dim_products.product_key
fact_sales.order_date_key → dim_dates.date_key
fact_sales.ship_date_key → dim_dates.date_key
fact_sales.delivery_date_key → dim_dates.date_key
fact_sales.payment_date_key → dim_dates.date_key
```

### Cardinality

- **One-to-Many**: Each customer can have multiple orders (1:M)
- **One-to-Many**: Each product can appear in multiple orders (1:M)
- **One-to-Many**: Each date can be associated with multiple transactions (1:M)
- **Many-to-One**: Multiple fact records can reference the same dimension record (M:1)

## Design Decisions

### Surrogate Keys

**Why**: Natural keys from source systems may change, be non-unique across systems, or have performance implications.

**Implementation**: Auto-incrementing integers (SERIAL) provide:
- Stable references that don't change
- Better join performance
- Smaller storage footprint
- Independence from source system changes

### Multiple Date Foreign Keys

**Why**: Different business processes occur on different dates, and analysts need to filter and group by various time perspectives.

**Implementation**: Separate foreign keys for:
- **order_date_key**: When customer placed order
- **ship_date_key**: When order was shipped
- **delivery_date_key**: When order was delivered
- **payment_date_key**: When payment was processed

### Grain Selection

**Why**: Order line item grain provides maximum flexibility for analysis.

**Benefits**:
- Can analyze individual products within orders
- Supports product-level profitability analysis
- Enables detailed customer purchase behavior analysis
- Allows aggregation to any higher level (order, customer, product, time)

### Slowly Changing Dimensions (SCD)

**Current Implementation**: Type 1 (Overwrite)
- Product prices and customer information are overwritten with new values
- Suitable for this use case where historical attribute values aren't critical

**Future Enhancement**: Could implement Type 2 (Historical) for:
- Product price changes over time
- Customer address changes
- Category reassignments

## Indexing Strategy

### Primary Keys
- Clustered indexes on all surrogate keys
- Automatic unique constraint enforcement

### Foreign Keys
```sql
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_order_date ON fact_sales(order_date_key);
CREATE INDEX idx_fact_sales_order_id ON fact_sales(order_id);
```

### Business Keys
```sql
CREATE INDEX idx_dim_customers_id ON dim_customers(customer_id);
CREATE INDEX idx_dim_products_id ON dim_products(product_id);
CREATE INDEX idx_dim_dates_value ON dim_dates(date_value);
```

## Query Patterns

### Typical Analytical Queries

1. **Time-based Analysis**
   ```sql
   SELECT dd.month_name, SUM(fs.total_price)
   FROM fact_sales fs
   JOIN dim_dates dd ON fs.order_date_key = dd.date_key
   GROUP BY dd.month_name;
   ```

2. **Customer Analysis**
   ```sql
   SELECT dc.state, COUNT(DISTINCT fs.order_id)
   FROM fact_sales fs
   JOIN dim_customers dc ON fs.customer_key = dc.customer_key
   GROUP BY dc.state;
   ```

3. **Product Performance**
   ```sql
   SELECT dp.category, SUM(fs.quantity * fs.unit_price)
   FROM fact_sales fs
   JOIN dim_products dp ON fs.product_key = dp.product_key
   GROUP BY dp.category;
   ```

## Data Quality Rules

### Referential Integrity
- All foreign keys must reference valid dimension records
- No orphaned fact records allowed

### Business Rules
- Quantities must be positive integers
- Prices must be positive decimals
- Dates must be valid and logical (ship_date >= order_date)

### Data Validation
- Email addresses must be valid format
- Phone numbers must follow standard format
- State codes must be valid abbreviations

This data model provides a solid foundation for e-commerce analytics while maintaining simplicity and query performance.