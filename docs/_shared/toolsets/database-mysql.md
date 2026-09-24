Connect HolmesGPT to MySQL databases to analyze query performance, investigate slow queries, optimize indexes, examine database health, and read data for troubleshooting.

You can configure multiple MySQL instances with different names (e.g., `orders-rds`, `analytics-mysql`, `staging-mysql`).

## Creating a Read-Only User

```sql
-- Create user
CREATE USER 'holmes_readonly'@'%' IDENTIFIED BY 'your_secure_password';

-- Grant read-only permissions
GRANT SELECT, SHOW VIEW, PROCESS ON *.* TO 'holmes_readonly'@'%';

-- Grant access to performance schema
GRANT SELECT ON performance_schema.* TO 'holmes_readonly'@'%';
GRANT SELECT ON information_schema.* TO 'holmes_readonly'@'%';

FLUSH PRIVILEGES;
```

**For specific database only:**
```sql
CREATE USER 'holmes_readonly'@'%' IDENTIFIED BY 'your_secure_password';
GRANT SELECT, SHOW VIEW ON your_database.* TO 'holmes_readonly'@'%';
GRANT SELECT ON performance_schema.* TO 'holmes_readonly'@'%';
GRANT SELECT ON information_schema.* TO 'holmes_readonly'@'%';
GRANT PROCESS ON *.* TO 'holmes_readonly'@'%';
FLUSH PRIVILEGES;
```

## Configuration

```holmes-config
secrets:
  MYSQL_URL:
    description: Database connection URL
    example: 'mysql+pymysql://holmes_readonly:your_secure_password@mysql.example.com:3306/orders'
secret_name: mysql-credentials
toolsets:
  orders-mysql:
    type: database
    config:
      connection_url: "{{ env.MYSQL_URL }}"
    llm_instructions: "Orders database with customer and product data"
```

**Multiple instances**, instead of the block above:

```holmes-config
secrets:
  ORDERS_MYSQL_URL:
    description: Database connection URL
    example: 'mysql+pymysql://holmes_readonly:your_secure_password@mysql.example.com:3306/orders'
  ANALYTICS_MYSQL_URL:
    description: Database connection URL
    example: 'mysql+pymysql://analyst:pass@analytics-mysql.internal:3306/analytics'
secret_name: mysql-credentials
toolsets:
  orders-mysql:
    type: database
    config:
      connection_url: "{{ env.ORDERS_MYSQL_URL }}"
    llm_instructions: "Orders database with customer and product data"

  analytics-mysql:
    type: database
    config:
      connection_url: "{{ env.ANALYTICS_MYSQL_URL }}"
    llm_instructions: "Analytics database for reporting queries"
```

**Connection URL format:**
```
mysql+pymysql://[username]:[password]@[host]:[port]/[database]
```

## Configuration Options

- **connection_url** (required): MySQL connection URL
- **read_only** (default: `true`): Only allow SELECT/SHOW/DESCRIBE/EXPLAIN/WITH statements
- **verify_ssl** (default: `true`): Verify SSL certificates
- **max_rows** (default: `200`): Maximum rows to return (1-10000)
- **llm_instructions**: Context about this database

## Common Use Cases

```
"Analyze slow query: SELECT * FROM orders WHERE created_at > '2024-01-01'"
```

```
"Show table structure for products and suggest indexes"
```

```
"What are the 10 largest tables?"
```

```
"Check for missing indexes on frequently queried columns"
```
