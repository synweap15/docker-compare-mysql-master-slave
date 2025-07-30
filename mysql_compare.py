#!/usr/bin/env python3

import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Dict

import mysql.connector
import requests
import schedule
from mysql.connector import Error

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MySQLComparator:
    def __init__(self, master_config: dict, slave_config: dict, database: str, validate_on_init: bool = False):
        self.master_config = master_config
        self.slave_config = slave_config
        self.database = database
        
        if validate_on_init:
            self.validate_connections()

    def _connect_to_mysql(self, config: dict) -> mysql.connector.MySQLConnection:
        try:
            connection = mysql.connector.connect(**config)
            return connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise

    def validate_connections(self) -> None:
        """Validate connections to both master and slave databases"""
        logger.info("Validating MySQL connections...")
        
        # Test master connection
        try:
            logger.info(f"Testing connection to master: {self.master_config['host']}:{self.master_config['port']}")
            master_conn = self._connect_to_mysql(self.master_config)
            master_conn.database = self.database
            cursor = master_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            master_conn.close()
            logger.info("Master connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to master database: {e}")
            raise SystemExit(f"Cannot connect to master database at {self.master_config['host']}:{self.master_config['port']} - {e}")

        # Test slave connection  
        try:
            logger.info(f"Testing connection to slave: {self.slave_config['host']}:{self.slave_config['port']}")
            slave_conn = self._connect_to_mysql(self.slave_config)
            slave_conn.database = self.database
            cursor = slave_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            slave_conn.close()
            logger.info("Slave connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to slave database: {e}")
            raise SystemExit(f"Cannot connect to slave database at {self.slave_config['host']}:{self.slave_config['port']} - {e}")
            
        logger.info("All database connections validated successfully")

    def _get_table_row_count(
        self, connection: mysql.connector.MySQLConnection, table: str
    ) -> int:
        cursor = connection.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Error as e:
            logger.error(f"Error counting rows in table {table}: {e}")
            return 0
        finally:
            cursor.close()

    def _get_all_tables(self, connection: mysql.connector.MySQLConnection) -> list[str]:
        cursor = connection.cursor()
        try:
            cursor.execute(f"SHOW TABLES FROM `{self.database}`")
            tables = [table[0] for table in cursor.fetchall()]
            return tables
        except Error as e:
            logger.error(f"Error getting tables from database {self.database}: {e}")
            return []
        finally:
            cursor.close()

    def compare_tables(
        self, tables: list[str] | None = None, max_difference_percent: float = 0.0
    ) -> dict[str, dict]:
        master_conn = None
        slave_conn = None
        results = {}

        try:
            master_conn = self._connect_to_mysql(self.master_config)
            slave_conn = self._connect_to_mysql(self.slave_config)

            master_conn.database = self.database
            slave_conn.database = self.database

            if tables is None:
                tables = self._get_all_tables(master_conn)

            for table in tables:
                master_count = self._get_table_row_count(master_conn, table)
                slave_count = self._get_table_row_count(slave_conn, table)

                difference = abs(master_count - slave_count)
                if master_count > 0:
                    difference_percent = (difference / master_count) * 100
                else:
                    difference_percent = 100.0 if slave_count > 0 else 0.0

                status = "OK"
                if difference_percent > max_difference_percent:
                    status = "ALERT"

                results[table] = {
                    "master_count": master_count,
                    "slave_count": slave_count,
                    "difference": difference,
                    "difference_percent": difference_percent,
                    "status": status,
                }

                logger.info(
                    f"Table {table}: Master={master_count}, Slave={slave_count}, "
                    f"Diff={difference} ({difference_percent:.2f}%), Status={status}"
                )

        except Exception as e:
            logger.error(f"Error during comparison: {e}")
            raise
        finally:
            if master_conn and master_conn.is_connected():
                master_conn.close()
            if slave_conn and slave_conn.is_connected():
                slave_conn.close()

        return results


class EmailNotifier:
    def __init__(self, sendgrid_api_key: str, from_email: str, to_emails: list[str], project_name: str = "MySQL Replication Monitor"):
        self.sendgrid_api_key = sendgrid_api_key
        self.from_email = from_email
        self.to_emails = to_emails
        self.project_name = project_name

    def send_report(
        self, results: Dict[str, Dict], database: str, force_send: bool = False
    ):
        alert_tables = {
            table: data for table, data in results.items() if data["status"] == "ALERT"
        }

        if not alert_tables and not force_send:
            return

        if alert_tables:
            subject = f"[{self.project_name}] MySQL Replication Alert - Database: {database}"
        else:
            subject = f"[{self.project_name}] MySQL Replication Report - Database: {database}"

        if alert_tables:
            body = f"""
            <html>
            <body>
            <h2>{self.project_name} - MySQL Master-Slave Replication Alert</h2>
            <p><strong>Project:</strong> {self.project_name}</p>
            <p><strong>Database:</strong> {database}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>Tables with significant differences:</h3>
            <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Table</th>
                <th>Master Count</th>
                <th>Slave Count</th>
                <th>Difference</th>
                <th>Difference %</th>
            </tr>
            """

            for table, data in alert_tables.items():
                body += f"""
                <tr>
                    <td>{table}</td>
                    <td>{data['master_count']}</td>
                    <td>{data['slave_count']}</td>
                    <td>{data['difference']}</td>
                    <td>{data['difference_percent']:.2f}%</td>
                </tr>
                """
        else:
            body = f"""
            <html>
            <body>
            <h2>{self.project_name} - MySQL Master-Slave Replication Report</h2>
            <p><strong>Project:</strong> {self.project_name}</p>
            <p><strong>Database:</strong> {database}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>All tables status:</h3>
            <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Table</th>
                <th>Master Count</th>
                <th>Slave Count</th>
                <th>Difference</th>
                <th>Difference %</th>
                <th>Status</th>
            </tr>
            """

            for table, data in results.items():
                body += f"""
                <tr>
                    <td>{table}</td>
                    <td>{data['master_count']}</td>
                    <td>{data['slave_count']}</td>
                    <td>{data['difference']}</td>
                    <td>{data['difference_percent']:.2f}%</td>
                    <td>{data['status']}</td>
                </tr>
                """

        body += """
        </table>
        </body>
        </html>
        """

        try:
            # Construct email recipients
            to_json = [{"email": email.strip()} for email in self.to_emails]

            # SendGrid API payload
            sendgrid_payload = {
                "personalizations": [{"to": to_json, "subject": subject}],
                "from": {"email": self.from_email},
                "content": [{"type": "text/html", "value": body}],
            }

            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=sendgrid_payload,
            )

            if response.status_code == 202:
                if alert_tables:
                    logger.info(f"Alert email sent to {', '.join(self.to_emails)}")
                else:
                    logger.info(f"Report email sent to {', '.join(self.to_emails)}")
            else:
                logger.error(
                    f"Failed to send email. Status: {response.status_code}, Response: {response.text}"
                )

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="MySQL Master-Slave Row Count Comparator"
    )
    parser.add_argument("--master-host", required=True, help="Master MySQL host")
    parser.add_argument(
        "--master-port", type=int, default=3306, help="Master MySQL port"
    )
    parser.add_argument("--master-user", required=True, help="Master MySQL username")
    parser.add_argument(
        "--master-password", required=True, help="Master MySQL password"
    )

    parser.add_argument("--slave-host", required=True, help="Slave MySQL host")
    parser.add_argument("--slave-port", type=int, default=3306, help="Slave MySQL port")
    parser.add_argument("--slave-user", required=True, help="Slave MySQL username")
    parser.add_argument("--slave-password", required=True, help="Slave MySQL password")

    parser.add_argument("--database", required=True, help="Database name to compare")
    parser.add_argument(
        "--tables", help="Comma-separated list of specific tables to check"
    )
    parser.add_argument(
        "--max-difference-percent",
        type=float,
        default=0.0,
        help="Maximum allowed difference percentage before alert",
    )

    parser.add_argument(
        "--schedule",
        help='Cron-like schedule (e.g., "*/5 * * * *" for every 5 minutes)',
    )
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")

    parser.add_argument(
        "--sendgrid-api-key", help="SendGrid API key for email notifications"
    )
    parser.add_argument("--mail-from", help="From email address")
    parser.add_argument("--mail-to", help="Comma-separated list of recipient emails")
    parser.add_argument(
        "--always-send-report",
        action="store_true",
        help="Always send report after each check, even if no alerts (default: only send on alerts)",
    )
    parser.add_argument(
        "--project-name",
        default="MySQL Replication Monitor",
        help="Project name to include in email notifications (default: MySQL Replication Monitor)",
    )

    args = parser.parse_args()

    master_config = {
        "host": args.master_host,
        "port": args.master_port,
        "user": args.master_user,
        "password": args.master_password,
    }

    slave_config = {
        "host": args.slave_host,
        "port": args.slave_port,
        "user": args.slave_user,
        "password": args.slave_password,
    }

    comparator = MySQLComparator(master_config, slave_config, args.database)
    
    # Validate connections on startup
    try:
        comparator.validate_connections()
    except SystemExit as e:
        logger.error(f"Connection validation failed: {e}")
        sys.exit(1)

    email_notifier = None
    if all([args.sendgrid_api_key, args.mail_to]):
        # Use provided mail_from or default
        mail_from = args.mail_from or "noreply@mysql-monitor.local"
        to_emails = [email.strip() for email in args.mail_to.split(",")]
        email_notifier = EmailNotifier(
            args.sendgrid_api_key,
            mail_from,
            to_emails,
            args.project_name,
        )

    tables = None
    if args.tables:
        tables = [table.strip() for table in args.tables.split(",")]

    def run_comparison():
        try:
            logger.info("Starting MySQL comparison...")
            results = comparator.compare_tables(tables, args.max_difference_percent)

            if email_notifier:
                email_notifier.send_report(
                    results, args.database, args.always_send_report
                )

            logger.info("Comparison completed successfully")

        except Exception as e:
            logger.error(f"Comparison failed: {e}")

    if args.run_once:
        run_comparison()
    elif args.schedule:
        # Parse simple schedule formats
        if args.schedule.startswith("*/"):
            minutes = int(args.schedule.split("/")[1].split()[0])
            schedule.every(minutes).minutes.do(run_comparison)
        elif args.schedule == "@hourly":
            schedule.every().hour.do(run_comparison)
        elif args.schedule == "@daily":
            schedule.every().day.do(run_comparison)
        else:
            logger.error(
                "Unsupported schedule format. Use */N for every N minutes, @hourly, or @daily"
            )
            sys.exit(1)

        logger.info(f"Scheduled to run: {args.schedule}")
        
        # Run the first check immediately
        logger.info("Running initial comparison...")
        run_comparison()

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        logger.error("Either --run-once or --schedule must be specified")
        sys.exit(1)


if __name__ == "__main__":
    main()
