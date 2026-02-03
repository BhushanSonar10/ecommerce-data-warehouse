# E-Commerce Data Warehouse Architecture

## Overview

This project implements a complete batch ETL pipeline that transforms raw e-commerce CSV data into an analytics-ready data warehouse using containerized services.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw CSV Data  │    │   Python ETL    │    │   PostgreSQL    │
│                 │───▶│                 │───▶│  Data Warehouse │
│ • customers.csv │    │ • Data Cleaning │    │                 │
│ • products.csv  │    │ • Transformations│    │ • Star Schema   │
│ • orders.csv    │    │ • Quality Checks│    │ • Fact Tables   │
│ • payments.csv  │    │ • Load Process  │    │ • Dimensions    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Docker Container│    │ Analytics Queries│
                       │                 │    │                 │
                       │ • ETL Service   │    │ • Revenue Reports│
                       │ • Orchestration │    │ • Customer Analysis│
                       │ • Logging       │    │ • Product Performance│
                       └─────────────────┘    └─────────────────┘
```

## Components

### 1. Data Sources
- **Format**: CSV files
- **Files**: customers.csv, products.csv, orders.csv, payments.csv
- **Volume**: Small-scale realistic e-commerce data
- **Storage**: Local filesystem mounted to Docker containers

### 2. ETL Pipeline (Python)
- **Framework**: Pandas for data manipulation
- **Database Connectivity**: psycopg2 + SQLAlchemy
- **Features**:
  - Data cleaning and validation
  - Type conversions and standardization
  - Business rule enforcement
  - Error handling and logging
  - Data quality checks

### 3. Data Warehouse (PostgreSQL)
- **Schema**: Star schema design
- **Deployment**: Docker container
- **Features**:
  - ACID compliance
  - Foreign key constraints
  - Indexing for performance
  - Connection pooling

### 4. Containerization (Docker)
- **Orchestration**: Docker Compose
- **Services**: PostgreSQL database, Python ETL
- **Benefits**: Reproducible deployments, environment isolation

## Data Model Design

### Star Schema Architecture

The data warehouse uses a star schema optimized for analytical queries:

```
                    ┌─────────────────┐
                    │   dim_dates     │
                    │                 │
                    │ • date_key (PK) │
                    │ • date_value    │
                    │ • year, month   │
                    │ • day_name      │
                    │ • is_weekend    │
                    └─────────────────┘
                             │
                             │
┌─────────────────┐         │         ┌─────────────────┐
│  dim_customers  │         │         │  dim_products   │
│                 │         │         │                 │
│ • customer_key  │         │         │ • product_key   │
│   (PK)          │         │         │   (PK)          │
│ • customer_id   │         │         │ • product_id    │
│ • name, email   │         │         │ • name, brand   │
│ • address       │         │         │ • category      │
│ • city, state   │         │         │ • price, cost   │
└─────────────────┘         │         └─────────────────┘
         │                  │                  │
         │                  │                  │
         │         ┌─────────────────┐         │
         └────────▶│   fact_sales    │◀────────┘
                   │                 │
                   │ • sales_key (PK)│
                   │ • order_id      │
                   │ • customer_key  │
                   │   (FK)          │
                   │ • product_key   │
                   │   (FK)          │
                   │ • date_keys     │
                   │   (FK)          │
                   │ • quantity      │
                   │ • unit_price    │
                   │ • total_price   │
                   │ • shipping_cost │
                   │ • tax_amount    │
                   └─────────────────┘
```

### Grain Definition

**Fact Table Grain**: One row per order line item
- Each row represents a single product within an order
- Allows analysis at the most detailed level
- Supports aggregation to order, customer, or product levels

### Dimension Tables

1. **dim_customers**: Customer demographic and contact information
2. **dim_products**: Product catalog with pricing and attributes
3. **dim_dates**: Time dimension for temporal analysis

### Fact Table

**fact_sales**: Transactional data with measures and foreign keys
- **Measures**: quantity, prices, costs, fees
- **Attributes**: order status, payment method
- **Foreign Keys**: Links to all dimension tables

## ETL Process Flow

### 1. Extract Phase
```python
# Load CSV files into pandas DataFrames
customers_df = pd.read_csv('customers.csv')
products_df = pd.read_csv('products.csv')
orders_df = pd.read_csv('orders.csv')
payments_df = pd.read_csv('payments.csv')
```

### 2. Transform Phase
```python
# Data cleaning and standardization
- Convert data types (dates, numbers)
- Standardize text fields (case, whitespace)
- Validate business rules (positive quantities)
- Generate surrogate keys
- Create date dimension
```

### 3. Load Phase
```python
# Load dimensions first (for referential integrity)
1. Load dim_customers
2. Load dim_products  
3. Load dim_dates
4. Retrieve surrogate keys
5. Create and load fact_sales
```

### 4. Quality Assurance
```python
# Automated data quality checks
- Row count validation
- Null value detection
- Foreign key integrity
- Data range validation
- Business rule compliance
```

## Deployment Architecture

### Docker Services

1. **PostgreSQL Container**
   - Image: postgres:15
   - Port: 5432
   - Volume: Persistent data storage
   - Health checks: Connection validation

2. **ETL Container**
   - Base: python:3.11-slim
   - Dependencies: pandas, psycopg2, sqlalchemy
   - Volumes: Data and SQL files mounted
   - Depends on: PostgreSQL health check

### Environment Configuration

```yaml
Environment Variables:
- DB_HOST=postgres
- DB_PORT=5432
- DB_NAME=ecommerce_dw
- DB_USER=postgres
- DB_PASSWORD=postgres
```

## Performance Considerations

### Database Optimization
- **Indexes**: Created on foreign keys and frequently queried columns
- **Constraints**: Foreign key relationships enforce data integrity
- **Data Types**: Optimized for storage and query performance

### ETL Optimization
- **Batch Processing**: Processes all data in single transaction
- **Memory Management**: Uses pandas for efficient data manipulation
- **Error Handling**: Comprehensive logging and rollback capabilities

## Scalability Considerations

### Current Limitations
- Single-node PostgreSQL deployment
- In-memory data processing with pandas
- Synchronous ETL execution

### Future Enhancements
- **Database**: Read replicas, partitioning, connection pooling
- **ETL**: Incremental loads, parallel processing, chunked processing
- **Monitoring**: Metrics collection, alerting, performance monitoring

## Security Features

### Database Security
- Environment variable configuration
- Container network isolation
- No hardcoded credentials

### Data Protection
- Transaction rollback on failures
- Data validation before loading
- Audit trail through logging

## Monitoring and Logging

### ETL Monitoring
```python
- Execution status logging
- Row count validation
- Data quality check results
- Error tracking and reporting
- Performance metrics
```

### Database Monitoring
- Connection health checks
- Query performance tracking
- Storage utilization monitoring

## Business Value

### Analytics Capabilities
1. **Revenue Analysis**: Monthly trends, growth rates
2. **Product Performance**: Top sellers, profitability
3. **Customer Insights**: Lifetime value, segmentation
4. **Operational Metrics**: Payment processing, fulfillment

### Reporting Benefits
- **Consistent Data**: Single source of truth
- **Historical Analysis**: Time-series reporting
- **Flexible Queries**: Star schema supports various analyses
- **Performance**: Optimized for analytical workloads

This architecture provides a solid foundation for business analytics while maintaining simplicity and reproducibility for development environments.