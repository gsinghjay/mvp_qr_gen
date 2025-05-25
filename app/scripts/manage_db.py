#!/usr/bin/env python3
"""
Database management script for handling migrations and database operations.
Provides a robust way to handle Alembic migrations with proper error handling,
backups, and environment-specific behavior for PostgreSQL.
"""
import argparse
import json
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Constants
BACKUP_DIR = "/app/data/backups"
ALEMBIC_INI = "/app/alembic.ini"
LOG_DIR = "/logs/database"
LOG_FILE = "operations.log"
ERROR_LOG = "errors.log"
MIGRATION_LOG = "migrations.log"
BACKUP_LOG = "backups.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# PostgreSQL connection info (from environment variables)
PG_DATABASE_URL = os.getenv("PG_DATABASE_URL")
POSTGRES_USER = os.getenv("POSTGRES_USER", "pguser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pgpassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "qrdb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

class StructuredMessage:
    """Structured logging message formatter."""

    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        """Format the log message as JSON."""
        log_dict = {
            "message": self.message,
            "timestamp": datetime.now(UTC).isoformat(),
            "source": "database_manager",
            **self.kwargs,
        }
        return json.dumps(log_dict)


# Create _ as a shortcut for StructuredMessage
_ = StructuredMessage


class ProgressIndicator:
    """Simple progress indicator for long-running operations."""
    
    def __init__(self, message: str, interval: float = 1.0):
        self.message = message
        self.interval = interval
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the progress indicator."""
        self.running = True
        self.thread = threading.Thread(target=self._show_progress)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the progress indicator."""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _show_progress(self):
        """Show progress dots."""
        dots = 0
        while self.running:
            dots = (dots + 1) % 4
            progress = "." * dots + " " * (3 - dots)
            print(f"\r{self.message}{progress}", end="", flush=True)
            time.sleep(self.interval)
        print()  # New line when done


def setup_logging():
    """Configure logging with multiple handlers for different log types."""
    # Create logs directory
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    json_formatter = logging.Formatter("%(message)s")
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Create and configure handlers
    handlers = {
        "operations": logging.handlers.RotatingFileHandler(
            log_dir / LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=LOG_BACKUP_COUNT
        ),
        "errors": logging.handlers.RotatingFileHandler(
            log_dir / ERROR_LOG, maxBytes=MAX_LOG_SIZE, backupCount=LOG_BACKUP_COUNT
        ),
        "migrations": logging.handlers.RotatingFileHandler(
            log_dir / MIGRATION_LOG, maxBytes=MAX_LOG_SIZE, backupCount=LOG_BACKUP_COUNT
        ),
        "backups": logging.handlers.RotatingFileHandler(
            log_dir / BACKUP_LOG, maxBytes=MAX_LOG_SIZE, backupCount=LOG_BACKUP_COUNT
        ),
        "console": logging.StreamHandler(),
    }

    # Set formatters
    for name, handler in handlers.items():
        handler.setFormatter(json_formatter if name != "console" else console_formatter)
        handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add handlers to logger
    for handler in handlers.values():
        root_logger.addHandler(handler)

    # Create specialized loggers
    loggers = {
        "operations": logging.getLogger("operations"),
        "errors": logging.getLogger("errors"),
        "migrations": logging.getLogger("migrations"),
        "backups": logging.getLogger("backups"),
    }

    # Configure specialized loggers
    for name, logger in loggers.items():
        logger.setLevel(logging.INFO)
        logger.addHandler(handlers[name])
        logger.propagate = False

    return loggers


# Initialize loggers
loggers = setup_logging()


class DatabaseManager:
    """Handles PostgreSQL database operations including migrations and backups."""

    def __init__(self, backup_dir: str, alembic_ini: str):
        self.backup_dir = Path(backup_dir)
        self.alembic_ini = Path(alembic_ini)
        
        # Create SQLAlchemy engine for database operations
        self.engine = create_engine(PG_DATABASE_URL)
        loggers["operations"].info(
            _(
                "PostgreSQL DatabaseManager initialized",
                pg_database_url=PG_DATABASE_URL,
                backup_dir=str(backup_dir),
                alembic_ini=str(alembic_ini),
            )
        )
            
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            loggers["operations"].info(
                _(
                    "Directories verified",
                    backup_dir=str(self.backup_dir),
                )
            )
        except Exception as e:
            loggers["errors"].error(
                _(
                    "Failed to create directories",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            raise

    @contextmanager
    def backup_database(self):
        """Create a backup of the database before operations."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        
        # PostgreSQL backup using pg_dump
        backup_path = self.backup_dir / f"qrdb_{timestamp}.sql"
        try:
            print(f"🔄 Creating PostgreSQL database backup...")
            print(f"   Database: {POSTGRES_DB}")
            print(f"   Destination: {backup_path}")
            
            loggers["backups"].info(
                _(
                    "Creating PostgreSQL database backup",
                    database=POSTGRES_DB,
                    destination=str(backup_path),
                )
            )
            
            # Test database connectivity first
            print("🔍 Testing database connectivity...")
            progress = ProgressIndicator("   Connecting to database")
            progress.start()
            
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("SELECT COUNT(*) FROM qr_codes"))
                    qr_count = result.scalar()
                    progress.stop()
                    print(f"✅ Database connected successfully. Found {qr_count} QR codes to backup.")
            except Exception as e:
                progress.stop()
                print(f"❌ Database connection failed: {e}")
                raise
            
            # Create pg_dump command with proper environment variables for authentication
            env = os.environ.copy()
            env["PGPASSWORD"] = POSTGRES_PASSWORD
            
            pg_dump_cmd = [
                "pg_dump",
                "-h", POSTGRES_HOST,
                "-p", POSTGRES_PORT,
                "-U", POSTGRES_USER,
                "-d", POSTGRES_DB,
                "-f", str(backup_path),
                "--format=c",      # Custom format (compressed)
                "--verbose",       # Verbose output for debugging
                "--no-tablespaces", # Don't include tablespace info
                "--no-privileges", # Don't dump privileges
                "--no-owner"       # Don't dump ownership info
            ]
            
            print("🚀 Starting backup process...")
            print(f"   Command: {' '.join(pg_dump_cmd[:7])} [credentials hidden]")
            print("   Note: Backup will run while API is active (production-safe)")
            
            # Start progress indicator
            backup_progress = ProgressIndicator("   Creating backup")
            backup_progress.start()
            
            # Execute pg_dump with timeout and special handling for active connections
            try:
                # Use Popen for better control and to capture output in real-time
                process = subprocess.Popen(
                    pg_dump_cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
                
                backup_progress.stop()
                
                if process.returncode == 0:
                    print("✅ Backup process completed successfully!")
                    if stderr and "WARNING" in stderr:
                        print(f"   Warnings: {stderr}")
                else:
                    print(f"❌ Backup process failed with exit code {process.returncode}")
                    if stdout:
                        print(f"   STDOUT: {stdout}")
                    if stderr:
                        print(f"   STDERR: {stderr}")
                    raise subprocess.CalledProcessError(process.returncode, pg_dump_cmd, stdout, stderr)
                
            except subprocess.TimeoutExpired:
                backup_progress.stop()
                print("❌ Backup process timed out after 5 minutes")
                process.kill()
                process.wait()
                raise
            except Exception as e:
                backup_progress.stop()
                print(f"❌ Backup process failed: {e}")
                raise
            
            # Check and report backup file size
            if backup_path.exists():
                backup_size = backup_path.stat().st_size
                backup_size_mb = backup_size / (1024 * 1024)
                print(f"📊 Backup file created: {backup_size:,} bytes ({backup_size_mb:.2f} MB)")
                
                loggers["backups"].info(
                    _(
                        "PostgreSQL backup created successfully",
                        backup_path=str(backup_path),
                        size_bytes=backup_size,
                        stdout=process.stdout.decode(),
                        stderr=process.stderr.decode(),
                    )
                )
            else:
                print("❌ Backup file was not created!")
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Copy to external backups directory if it exists
            external_backup_dir = Path("/app/backups")
            if external_backup_dir.exists() and external_backup_dir.is_dir():
                print("📁 Copying backup to external directory...")
                external_backup_path = external_backup_dir / backup_path.name
                try:
                    copy_progress = ProgressIndicator("   Copying file")
                    copy_progress.start()
                    shutil.copy2(backup_path, external_backup_path)
                    copy_progress.stop()
                    print(f"✅ Backup copied to: {external_backup_path}")
                    
                    loggers["backups"].info(
                        _(
                            "Backup copied to external directory",
                            source=str(backup_path),
                            destination=str(external_backup_path),
                        )
                    )
                except Exception as e:
                    copy_progress.stop()
                    print(f"⚠️  Failed to copy backup to external directory: {e}")
                    loggers["errors"].warning(
                        _(
                            "Failed to copy backup to external directory",
                            error=str(e),
                            source=str(backup_path),
                            destination=str(external_backup_path),
                        )
                    )
            else:
                print("ℹ️  External backup directory not available")
            
            yield backup_path
            
            # Cleanup old backups (keep last 5)
            print("🧹 Cleaning up old backups...")
            cleanup_progress = ProgressIndicator("   Cleaning old files")
            cleanup_progress.start()
            self._cleanup_old_backups("sql")
            cleanup_progress.stop()
            print("✅ Cleanup completed")
            
        except subprocess.TimeoutExpired as e:
            print(f"❌ Backup operation timed out after {e.timeout} seconds")
            loggers["errors"].error(
                _(
                    "PostgreSQL backup timed out",
                    timeout=e.timeout,
                    traceback=traceback.format_exc(),
                )
            )
            raise
        except subprocess.CalledProcessError as e:
            print(f"❌ PostgreSQL backup failed with exit code {e.returncode}")
            if e.stdout:
                print(f"   STDOUT: {e.stdout.decode()}")
            if e.stderr:
                print(f"   STDERR: {e.stderr.decode()}")
            
            loggers["errors"].error(
                _(
                    "PostgreSQL backup failed",
                    error=str(e),
                    exit_code=e.returncode,
                    stdout=e.stdout.decode() if e.stdout else "",
                    stderr=e.stderr.decode() if e.stderr else "",
                    traceback=traceback.format_exc(),
                )
            )
            raise
        except Exception as e:
            print(f"❌ Backup failed with unexpected error: {e}")
            loggers["errors"].error(
                _("Backup failed", error=str(e), traceback=traceback.format_exc())
            )
            raise

    def _cleanup_old_backups(self, extension="sql", keep_count: int = 5):
        """Clean up old database backups, keeping only the most recent ones."""
        try:
            # Handle PostgreSQL (.sql) backups
            filename_pattern = f"qrdb_*.{extension}"
            
            backups = sorted(
                self.backup_dir.glob(filename_pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            for old_backup in backups[keep_count:]:
                loggers["backups"].info(_("Removing old backup", backup_path=str(old_backup)))
                old_backup.unlink()
        except Exception as e:
            loggers["errors"].warning(
                _(
                    "Failed to cleanup old backups",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )

    def get_current_revision(self) -> str:
        """Get current database revision."""
        try:
            # For PostgreSQL, use SQLAlchemy to query
            with self.engine.connect() as connection:
                try:
                    result = connection.execute(text("SELECT version_num FROM alembic_version"))
                    row = result.fetchone()
                    revision = row[0] if row else None
                    loggers["operations"].info(
                        _("Current PostgreSQL database revision retrieved", revision=revision)
                    )
                    return revision
                except SQLAlchemyError:
                    loggers["operations"].info(_("No alembic_version table found in PostgreSQL"))
                    return None
                        
        except Exception as e:
            loggers["errors"].error(
                _(
                    "Error getting current revision",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            raise

    def get_head_revision(self) -> str:
        """Get the latest available revision."""
        try:
            config = Config(self.alembic_ini)
            script = ScriptDirectory.from_config(config)
            head = script.get_current_head()
            loggers["operations"].info(_("Head revision retrieved", revision=head))
            return head
        except Exception as e:
            loggers["errors"].error(
                _(
                    "Error getting head revision",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            raise

    def needs_upgrade(self) -> bool:
        """Check if database needs to be upgraded."""
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()
            needs_upgrade = current != head
            loggers["operations"].info(
                _(
                    "Checked upgrade status",
                    current_revision=current,
                    head_revision=head,
                    needs_upgrade=needs_upgrade,
                )
            )
            return needs_upgrade
        except Exception as e:
            loggers["errors"].error(
                _(
                    "Error checking upgrade status",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            raise

    def init_database(self):
        """Initialize a fresh database."""
        try:
            # For PostgreSQL, we don't need to delete the database
            # Instead, we'll drop all tables and recreate them
            with self.engine.connect() as connection:
                # Drop alembic_version table if it exists
                try:
                    connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    connection.commit()
                except SQLAlchemyError as e:
                    loggers["errors"].warning(_(
                        "Error dropping alembic_version table",
                        error=str(e)
                    ))
                    
                # Drop other tables
                try:
                    connection.execute(text("DROP TABLE IF EXISTS qr_codes"))
                    connection.commit()
                except SQLAlchemyError as e:
                    loggers["errors"].warning(_(
                        "Error dropping qr_codes table",
                        error=str(e)
                    ))
                    
            loggers["operations"].info(_("PostgreSQL database tables dropped for reinitialization"))

            # Create a fresh database and run initial migration
            config = Config(self.alembic_ini)
            command.upgrade(config, "head")

            loggers["operations"].info(_("Database initialized successfully"))
            return True

        except Exception as e:
            loggers["errors"].error(
                _(
                    "Database initialization failed",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            return False

    def run_migrations(self):
        """Run database migrations."""
        try:
            config = Config(self.alembic_ini)
            current = self.get_current_revision()
            head = self.get_head_revision()

            if current is None:
                # For a fresh database, run all migrations
                loggers["migrations"].info(_("Running initial migrations"))
                command.upgrade(config, "head")
            else:
                # For existing database, run any pending migrations
                loggers["migrations"].info(
                    _("Running migrations", from_revision=current, to_revision=head)
                )
                command.upgrade(config, "head")

            # Verify the migration
            new_current = self.get_current_revision()
            if new_current != head:
                raise Exception(
                    f"Migration failed: current revision {new_current} does not match head {head}"
                )

            loggers["migrations"].info(
                _("Migrations completed successfully", current_revision=new_current)
            )
            return True
        except Exception as e:
            loggers["errors"].error(
                _("Migration failed", error=str(e), traceback=traceback.format_exc())
            )
            return False

    def validate_database(self) -> bool:
        """
        Validate if the database is valid with required tables.
        Returns True if valid, False otherwise.
        """
        try:
            with self.engine.connect() as connection:
                # Check if PostgreSQL is accessible
                try:
                    connection.execute(text("SELECT 1"))
                except SQLAlchemyError:
                    loggers["operations"].warning(_("Cannot connect to PostgreSQL database"))
                    return False
                    
                # Check if it's at the latest migration
                if self.needs_upgrade():
                    loggers["operations"].warning(_("Database needs migration"))
                    return False
                    
                # Check for required tables
                try:
                    result = connection.execute(text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    ))
                    tables = {row[0] for row in result}
                    
                    required_tables = {"qr_codes", "alembic_version"}
                    missing_tables = required_tables - tables
                    
                    if missing_tables:
                        loggers["operations"].warning(
                            _("Missing required tables", missing=list(missing_tables))
                        )
                        return False
                except SQLAlchemyError as e:
                    loggers["operations"].warning(_("Error checking tables", error=str(e)))
                    return False
                    
                # Verify qr_codes table structure if it exists
                if "qr_codes" in tables:
                    try:
                        result = connection.execute(text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_schema = 'public' AND table_name = 'qr_codes'"
                        ))
                        columns = {row[0] for row in result}
                        
                        required_columns = {
                            "id",
                            "content",
                            "qr_type",
                            "redirect_url",
                            "created_at",
                            "scan_count",
                            "last_scan_at",
                            "fill_color",
                            "back_color",
                            "size",
                            "border",
                        }
                        missing_columns = required_columns - columns
                        
                        if missing_columns:
                            loggers["operations"].warning(
                                _(
                                    "Missing required columns in qr_codes table",
                                    missing=list(missing_columns),
                                )
                            )
                            return False
                    except SQLAlchemyError as e:
                        loggers["operations"].warning(_("Error checking columns", error=str(e)))
                        return False
                        
            loggers["operations"].info(_("PostgreSQL database validation successful"))
            return True
            
        except Exception as e:
            loggers["errors"].error(
                _(
                    "Error validating PostgreSQL database",
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            return False

    def restore_database(self, backup_filename: str):
        """
        Restore database from a backup file.
        
        CRITICAL SAFETY NOTE: This operation should only be performed when the API service is stopped
        to prevent data corruption and application crashes.
        
        Args:
            backup_filename: Name of the backup file (e.g., 'qrdb_20250525_043343.sql')
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("🚨 CRITICAL SAFETY WARNING:")
            print("   Database restore should only be performed with API service stopped")
            print("   This operation will drop all tables and restore from backup")
            print()
            
            # Safety warning
            loggers["backups"].warning(
                _(
                    "CRITICAL: Database restore should only be performed with API service stopped",
                    warning="This operation will drop all tables and restore from backup"
                )
            )
            # Look for backup file in both internal and external backup directories
            print(f"🔍 Searching for backup file: {backup_filename}")
            backup_path = None
            search_dirs = [self.backup_dir, Path("/app/backups")]
            
            for backup_dir in search_dirs:
                potential_path = backup_dir / backup_filename
                print(f"   Checking: {potential_path}")
                if potential_path.exists():
                    backup_path = potential_path
                    print(f"✅ Found backup file: {backup_path}")
                    break
            
            if not backup_path:
                print(f"❌ Backup file '{backup_filename}' not found in any of these directories:")
                for dir_path in search_dirs:
                    print(f"   - {dir_path}")
                
                loggers["errors"].error(
                    _(
                        "Backup file not found",
                        filename=backup_filename,
                        searched_dirs=[str(self.backup_dir), "/app/backups"]
                    )
                )
                return False
            
            loggers["backups"].info(
                _(
                    "Starting PostgreSQL database restore",
                    backup_file=str(backup_path),
                    database=POSTGRES_DB
                )
            )
            
            # Create a safety backup before restore
            safety_backup_timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            safety_backup_path = self.backup_dir / f"qrdb_{safety_backup_timestamp}_before_restore.sql"
            
            loggers["backups"].info(
                _(
                    "Creating safety backup before restore",
                    destination=str(safety_backup_path)
                )
            )
            
            # Create safety backup
            env = os.environ.copy()
            env["PGPASSWORD"] = POSTGRES_PASSWORD
            
            safety_backup_cmd = [
                "pg_dump",
                "-h", POSTGRES_HOST,
                "-p", POSTGRES_PORT,
                "-U", POSTGRES_USER,
                "-d", POSTGRES_DB,
                "-f", str(safety_backup_path),
                "--format=c"
            ]
            
            subprocess.run(
                safety_backup_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            
            loggers["backups"].info(
                _(
                    "Safety backup created successfully",
                    backup_path=str(safety_backup_path)
                )
            )
            
            # Drop existing database content and restore
            loggers["backups"].info(_("Dropping existing database content"))
            
            with self.engine.connect() as connection:
                # Drop tables in correct order (considering foreign keys)
                try:
                    connection.execute(text("DROP TABLE IF EXISTS scan_logs CASCADE"))
                    connection.execute(text("DROP TABLE IF EXISTS qr_codes CASCADE"))
                    connection.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                    connection.commit()
                    loggers["backups"].info(_("Existing tables dropped successfully"))
                except SQLAlchemyError as e:
                    loggers["errors"].warning(
                        _("Error dropping tables", error=str(e))
                    )
            
            # Restore from backup using pg_restore
            loggers["backups"].info(_("Restoring from backup file"))
            
            restore_cmd = [
                "pg_restore",
                "-h", POSTGRES_HOST,
                "-p", POSTGRES_PORT,
                "-U", POSTGRES_USER,
                "-d", POSTGRES_DB,
                "--no-owner",  # don't restore ownership
                "--no-privileges",  # don't restore privileges
                "--single-transaction",  # restore in a single transaction
                "--exit-on-error",  # exit on first error
                str(backup_path)
            ]
            
            process = subprocess.run(
                restore_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=300,  # 5 minute timeout
            )
            
            loggers["backups"].info(
                _(
                    "Database restore completed successfully",
                    backup_file=str(backup_path),
                    stdout=process.stdout.decode(),
                    stderr=process.stderr.decode()
                )
            )
            
            # Validate the restored database
            if self.validate_database():
                loggers["backups"].info(_("Restored database validation successful"))
                return True
            else:
                loggers["errors"].error(_("Restored database validation failed"))
                return False
                
        except subprocess.CalledProcessError as e:
            loggers["errors"].error(
                _(
                    "Database restore failed",
                    error=str(e),
                    stdout=e.stdout.decode() if e.stdout else "",
                    stderr=e.stderr.decode() if e.stderr else "",
                    traceback=traceback.format_exc(),
                )
            )
            return False
        except Exception as e:
            loggers["errors"].error(
                _(
                    "Database restore failed",
                    error=str(e),
                    traceback=traceback.format_exc()
                )
            )
            return False


def run_cli():
    """Process command line arguments."""
    parser = argparse.ArgumentParser(description="PostgreSQL database management tool")
    parser.add_argument("--init", action="store_true", help="Initialize a fresh database")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    parser.add_argument("--check", action="store_true", help="Check if migrations are needed")
    parser.add_argument("--validate", action="store_true", help="Validate database structure")
    parser.add_argument("--create-backup", action="store_true", help="Create a database backup")
    parser.add_argument("--restore", type=str, help="Restore database from backup file (provide filename)")

    args = parser.parse_args()

    if not (args.init or args.migrate or args.check or args.validate or args.create_backup or args.restore):
        parser.print_help()
        return

    db_manager = DatabaseManager(
        backup_dir=BACKUP_DIR,
        alembic_ini=ALEMBIC_INI,
    )

    # Check for backup request first
    if args.create_backup:
        try:
            with db_manager.backup_database():
                loggers["operations"].info(_("Backup created successfully"))
                return
        except Exception as e:
            loggers["errors"].error(
                _("Failed to create backup", error=str(e))
            )
            sys.exit(1)

    # Check for restore request
    if args.restore:
        try:
            success = db_manager.restore_database(args.restore)
            if success:
                loggers["operations"].info(_("Database restored successfully"))
            else:
                loggers["errors"].error(_("Database restore failed"))
                sys.exit(1)
        except Exception as e:
            loggers["errors"].error(
                _("Failed to restore database", error=str(e))
            )
            sys.exit(1)

    # Other operations
    if args.init:
        db_manager.init_database()

    if args.check:
        needs_upgrade = db_manager.needs_upgrade()
        if needs_upgrade:
            loggers["operations"].info(_("Database needs migration"))
            sys.exit(1)
        else:
            loggers["operations"].info(_("Database is up to date"))

    if args.validate:
        is_valid = db_manager.validate_database()
        if not is_valid:
            loggers["operations"].error(_("Database validation failed"))
            sys.exit(1)
        else:
            loggers["operations"].info(_("Database validation successful"))

    if args.migrate:
        db_manager.run_migrations()


if __name__ == "__main__":
    run_cli()
