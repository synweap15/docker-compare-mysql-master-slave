#!/bin/bash
set -e

if [[ "$1" == "cron" ]]; then
    # Parse environment variables for cron job
    if [[ -z "$CRON_SCHEDULE" ]]; then
        echo "Error: CRON_SCHEDULE environment variable is required for cron mode"
        exit 1
    fi
    
    # Build the command from environment variables
    CMD="/usr/local/bin/python /app/mysql_compare.py"
    
    [[ -n "$MASTER_HOST" ]] && CMD="$CMD --master-host $MASTER_HOST"
    [[ -n "$MASTER_PORT" ]] && CMD="$CMD --master-port $MASTER_PORT"
    [[ -n "$MASTER_USER" ]] && CMD="$CMD --master-user $MASTER_USER"
    [[ -n "$MASTER_PASSWORD" ]] && CMD="$CMD --master-password $MASTER_PASSWORD"
    
    [[ -n "$SLAVE_HOST" ]] && CMD="$CMD --slave-host $SLAVE_HOST"
    [[ -n "$SLAVE_PORT" ]] && CMD="$CMD --slave-port $SLAVE_PORT"
    [[ -n "$SLAVE_USER" ]] && CMD="$CMD --slave-user $SLAVE_USER"
    [[ -n "$SLAVE_PASSWORD" ]] && CMD="$CMD --slave-password $SLAVE_PASSWORD"
    
    [[ -n "$DATABASE" ]] && CMD="$CMD --database $DATABASE"
    [[ -n "$TABLES" ]] && CMD="$CMD --tables $TABLES"
    [[ -n "$MAX_DIFFERENCE_PERCENT" ]] && CMD="$CMD --max-difference-percent $MAX_DIFFERENCE_PERCENT"
    
    [[ -n "$SENDGRID_API_KEY" ]] && CMD="$CMD --sendgrid-api-key $SENDGRID_API_KEY"
    [[ -n "$MAIL_FROM" ]] && CMD="$CMD --mail-from $MAIL_FROM"
    [[ -n "$MAIL_TO" ]] && CMD="$CMD --mail-to $MAIL_TO"
    
    CMD="$CMD --schedule $CRON_SCHEDULE"
    
    echo "Starting MySQL comparison with schedule: $CRON_SCHEDULE"
    echo "Command: $CMD"
    
    exec $CMD
    
elif [[ "$1" == "run-once" ]]; then
    # Build the command for one-time run
    CMD="/usr/local/bin/python /app/mysql_compare.py --run-once"
    
    [[ -n "$MASTER_HOST" ]] && CMD="$CMD --master-host $MASTER_HOST"
    [[ -n "$MASTER_PORT" ]] && CMD="$CMD --master-port $MASTER_PORT"
    [[ -n "$MASTER_USER" ]] && CMD="$CMD --master-user $MASTER_USER"
    [[ -n "$MASTER_PASSWORD" ]] && CMD="$CMD --master-password $MASTER_PASSWORD"
    
    [[ -n "$SLAVE_HOST" ]] && CMD="$CMD --slave-host $SLAVE_HOST"
    [[ -n "$SLAVE_PORT" ]] && CMD="$CMD --slave-port $SLAVE_PORT"
    [[ -n "$SLAVE_USER" ]] && CMD="$CMD --slave-user $SLAVE_USER"
    [[ -n "$SLAVE_PASSWORD" ]] && CMD="$CMD --slave-password $SLAVE_PASSWORD"
    
    [[ -n "$DATABASE" ]] && CMD="$CMD --database $DATABASE"
    [[ -n "$TABLES" ]] && CMD="$CMD --tables $TABLES"
    [[ -n "$MAX_DIFFERENCE_PERCENT" ]] && CMD="$CMD --max-difference-percent $MAX_DIFFERENCE_PERCENT"
    
    [[ -n "$SENDGRID_API_KEY" ]] && CMD="$CMD --sendgrid-api-key $SENDGRID_API_KEY"
    [[ -n "$MAIL_FROM" ]] && CMD="$CMD --mail-from $MAIL_FROM"
    [[ -n "$MAIL_TO" ]] && CMD="$CMD --mail-to $MAIL_TO"
    
    echo "Running MySQL comparison once"
    echo "Command: $CMD"
    
    exec $CMD
    
else
    # Pass through to mysql_compare.py with all arguments
    exec python /app/mysql_compare.py "$@"
fi