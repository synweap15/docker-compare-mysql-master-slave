# MySQL Master-Slave Replication Monitor

A Docker-based tool for monitoring MySQL master-slave replication by comparing row counts in tables and sending email alerts when discrepancies exceed specified thresholds.

Also see

## Features

- **Periodic Monitoring**: Configurable cron-like scheduling
- **Row Count Comparison**: Compares row counts between master and slave databases
- **Table Filtering**: Option to monitor specific tables or all tables
- **Email Alerts**: Sends HTML email notifications when differences exceed threshold
- **Always Send Reports**: Optional flag to send comprehensive reports after every check
- **Flexible Deployment**: Docker container with environment variable configuration

## Quick Start

### Using Docker Compose

1. Copy the `docker-compose.yml` file and modify the environment variables:

```yaml
environment:
  # MySQL Configuration
  - MASTER_HOST=your-master-host
  - MASTER_USER=your-username
  - MASTER_PASSWORD=your-password
  - SLAVE_HOST=your-slave-host
  - SLAVE_USER=your-username  
  - SLAVE_PASSWORD=your-password
  - DATABASE=your-database
  
  # Monitoring Configuration
  - MAX_DIFFERENCE_PERCENT=5.0
  - CRON_SCHEDULE=*/10  # Every 10 minutes
  
  # Email Configuration (optional)
  - SENDGRID_API_KEY=your-sendgrid-api-key
  - MAIL_FROM=alerts@yourcompany.com
  - MAIL_TO=admin@yourcompany.com,ops@yourcompany.com
```

2. Run the container:

```bash
docker-compose up -d
```

### Using Docker Run

```bash
docker build -t mysql-compare .

# Run once
docker run --rm mysql-compare run-once \
  --master-host mysql-master \
  --master-user root \
  --master-password password \
  --slave-host mysql-slave \
  --slave-user root \
  --slave-password password \
  --database mydb \
  --max-difference-percent 5.0

# Run with schedule
docker run -d mysql-compare cron \
  -e MASTER_HOST=mysql-master \
  -e MASTER_USER=root \
  -e MASTER_PASSWORD=password \
  -e SLAVE_HOST=mysql-slave \
  -e SLAVE_USER=root \
  -e SLAVE_PASSWORD=password \
  -e DATABASE=mydb \
  -e CRON_SCHEDULE="*/10" \
  -e MAX_DIFFERENCE_PERCENT=5.0 \
  -e SENDGRID_API_KEY=your-api-key \
  -e MAIL_FROM=alerts@yourcompany.com \
  -e MAIL_TO=admin@yourcompany.com
```

## Configuration

### Environment Variables

#### MySQL Configuration (Required)
- `MASTER_HOST`: MySQL master server hostname/IP
- `MASTER_PORT`: MySQL master server port (default: 3306)
- `MASTER_USER`: MySQL master username
- `MASTER_PASSWORD`: MySQL master password
- `SLAVE_HOST`: MySQL slave server hostname/IP
- `SLAVE_PORT`: MySQL slave server port (default: 3306)
- `SLAVE_USER`: MySQL slave username
- `SLAVE_PASSWORD`: MySQL slave password
- `DATABASE`: Database name to monitor

#### Monitoring Configuration
- `TABLES`: Comma-separated list of specific tables to monitor (optional, monitors all tables if not specified)
- `MAX_DIFFERENCE_PERCENT`: Maximum allowed difference percentage before sending alert (default: 0.0)
- `CRON_SCHEDULE`: Schedule for periodic checks (see Schedule Formats below)

#### Email Configuration (Optional)
- `SENDGRID_API_KEY`: SendGrid API key for email notifications
- `MAIL_FROM`: From email address
- `MAIL_TO`: Comma-separated list of recipient email addresses
- `ALWAYS_SEND_REPORT`: Set to "true" to send comprehensive reports after every check

### Schedule Formats

The `CRON_SCHEDULE` environment variable supports these formats:

- `*/N` - Every N minutes (e.g., `*/5` for every 5 minutes)
- `@hourly` - Every hour
- `@daily` - Every day

### Command Line Usage

You can also run the script directly with command line arguments:

```bash
python mysql_compare.py \
  --master-host mysql-master \
  --master-user root \
  --master-password password \
  --slave-host mysql-slave \
  --slave-user root \
  --slave-password password \
  --database mydb \
  --tables users,orders \
  --max-difference-percent 5.0 \
  --schedule "*/10" \
  --sendgrid-api-key your-api-key \
  --mail-from alerts@yourcompany.com \
  --mail-to admin@yourcompany.com,ops@yourcompany.com \
  --always-send-report
```

#### Command Line Options

- `--master-host`, `--master-port`, `--master-user`, `--master-password`: Master MySQL connection
- `--slave-host`, `--slave-port`, `--slave-user`, `--slave-password`: Slave MySQL connection  
- `--database`: Database name to compare
- `--tables`: Comma-separated list of specific tables (optional)
- `--max-difference-percent`: Maximum allowed difference percentage (default: 0.0)
- `--schedule`: Cron-like schedule for periodic runs
- `--run-once`: Run comparison once and exit
- `--sendgrid-api-key`: SendGrid API key for email notifications
- `--mail-from`, `--mail-to`: Email addresses
- `--always-send-report`: Always send comprehensive reports after each check

## Email Notifications

The tool supports two types of email notifications:

### Alerts (Default Behavior)
When the difference percentage between master and slave row counts exceeds the configured threshold, an HTML email alert is sent containing:

- Database name and timestamp
- Table comparison results showing only tables with significant differences:
  - Master row count
  - Slave row count  
  - Absolute difference
  - Percentage difference

### Comprehensive Reports (--always-send-report flag)
When the `--always-send-report` flag is enabled, emails are sent after every check regardless of alert status, containing:

- Database name and timestamp
- Complete table comparison results for all monitored tables:
  - Master row count
  - Slave row count
  - Absolute difference
  - Percentage difference
  - Status (OK/ALERT)


## Building from Source

```bash
git clone <repository-url>
cd mysql-compare
docker build -t mysql-compare .
```

