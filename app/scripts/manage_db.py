#!/usr/bin/env python3
"""
Database management script for handling migrations and database operations.
Provides a more robust way to handle Alembic migrations with proper error handling,
backups, and environment-specific behavior.
"""
import argparse
import json
import logging
import logging.handlers
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
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
DB_PATH = "/app/data/qr_codes.db"
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

# Determine if we should use PostgreSQL
USE_POSTGRES = PG_DATABASE_URL is not None and os.getenv("USE_POSTGRES", "false").lower() == "true"

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
    """Handles database operations including migrations and backups."""

    def __init__(self, db_path: str, backup_dir: str, alembic_ini: str):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.alembic_ini = Path(alembic_ini)
        self.use_postgres = USE_POSTGRES
        
        # Create SQLAlchemy engine for database operations
        if self.use_postgres:
            self.engine = create_engine(PG_DATABASE_URL)
            loggers["operations"].info(
                _(
                    "PostgreSQL DatabaseManager initialized",
                    pg_database_url=PG_DATABASE_URL,
                    backup_dir=str(backup_dir),
                    alembic_ini=str(alembic_ini),
                )
            )
        else:
            self.engine = create_engine(f"sqlite:///{db_path}")
            loggers["operations"].info(
                _(
                    "SQLite DatabaseManager initialized",
                    db_path=str(db_path),
                    backup_dir=str(backup_dir),
                    alembic_ini=str(alembic_ini),
                )
            )
            
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            if not self.use_postgres:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            loggers["operations"].info(
                _(
                    "Directories verified",
                    backup_dir=str(self.backup_dir),
                    db_dir=str(self.db_path.parent) if not self.use_postgres else "N/A (PostgreSQL)",
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
        
        if self.use_postgres:
            # PostgreSQL backup using pg_dump
            backup_path = self.backup_dir / f"qrdb_{timestamp}.sql"
            try:
                loggers["backups"].info(
                    _(
                        "Creating PostgreSQL database backup",
                        database=POSTGRES_DB,
                        destination=str(backup_path),
                    )
                )
                
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
                    "--format=c"  # Custom format (compressed)
                ]
                
                # Execute pg_dump
                process = subprocess.run(
                    pg_dump_cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                
                # Log backup file size
                backup_size = backup_path.stat().st_size
                loggers["backups"].info(
                    _(
                        "PostgreSQL backup created successfully",
                        backup_path=str(backup_path),
                        size_bytes=backup_size,
                        stdout=process.stdout.decode(),
                        stderr=process.stderr.decode(),
                    )
                )
                
                # Copy to external backups directory if it exists
                external_backup_dir = Path("/app/backups")
                if external_backup_dir.exists() and external_backup_dir.is_dir():
                    external_backup_path = external_backup_dir / backup_path.name
                    try:
                        shutil.copy2(backup_path, external_backup_path)
                        loggers["backups"].info(
                            _(
                                "Backup copied to external directory",
                                source=str(backup_path),
                                destination=str(external_backup_path),
                            )
                        )
                    except Exception as e:
                        loggers["errors"].warning(
                            _(
                                "Failed to copy backup to external directory",
                                error=str(e),
                                source=str(backup_path),
                                destination=str(external_backup_path),
                            )
                        )
                
                yield backup_path
                
                # Cleanup old backups (keep last 5)
                self._cleanup_old_backups("sql")
                
            except subprocess.CalledProcessError as e:
                loggers["errors"].error(
                    _(
                        "PostgreSQL backup failed",
                        error=str(e),
                        stdout=e.stdout.decode() if e.stdout else "",
                        stderr=e.stderr.decode() if e.stderr else "",
                        traceback=traceback.format_exc(),
                    )
                )
                raise
            except Exception as e:
                loggers["errors"].error(
                    _("Backup failed", error=str(e), traceback=traceback.format_exc())
                )
                raise
                
        else:
            # SQLite backup (existing functionality)
            if not self.db_path.exists():
                loggers["backups"].info(
                    _("No database file exists, skipping backup", db_path=str(self.db_path))
                )
                yield None
                return

            backup_path = self.backup_dir / f"qr_codes_{timestamp}.db"

            try:
                loggers["backups"].info(
                    _(
                        "Creating SQLite database backup",
                        source=str(self.db_path),
                        destination=str(backup_path),
                    )
                )
                shutil.copy2(self.db_path, backup_path)

                # Log backup file size
                backup_size = backup_path.stat().st_size
                loggers["backups"].info(
                    _(
                        "SQLite backup created successfully",
                        backup_path=str(backup_path),
                        size_bytes=backup_size,
                    )
                )

                # Copy to external backups directory if it exists
                external_backup_dir = Path("/app/backups")
                if external_backup_dir.exists() and external_backup_dir.is_dir():
                    external_backup_path = external_backup_dir / backup_path.name
                    try:
                        shutil.copy2(backup_path, external_backup_path)
                        loggers["backups"].info(
                            _(
                                "Backup copied to external directory",
                                source=str(backup_path),
                                destination=str(external_backup_path),
                            )
                        )
                    except Exception as e:
                        loggers["errors"].warning(
                            _(
                                "Failed to copy backup to external directory",
                                error=str(e),
                                source=str(backup_path),
                                destination=str(external_backup_path),
                            )
                        )

                yield backup_path

                # Cleanup old backups (keep last 5)
                self._cleanup_old_backups("db")
            except Exception as e:
                loggers["errors"].error(
                    _("Backup failed", error=str(e), traceback=traceback.format_exc())
                )
                raise

    def _cleanup_old_backups(self, extension="db", keep_count: int = 5):
        """Clean up old database backups, keeping only the most recent ones."""
        try:
            # Handle both SQLite (.db) and PostgreSQL (.sql) backups
            filename_pattern = f"qr_codes_*.{extension}" if extension == "db" else f"qrdb_*.{extension}"
            
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
            if self.use_postgres:
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
            else:
                # For SQLite, use sqlite3 (existing functionality)
                if not self.db_path.exists():
                    loggers["operations"].info(_("No database file exists", db_path=str(self.db_path)))
                    return None
                    
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("SELECT version_num FROM alembic_version")
                        result = cursor.fetchone()
                        revision = result[0] if result else None
                        loggers["operations"].info(
                            _("Current SQLite database revision retrieved", revision=revision)
                        )
                        return revision
                    except sqlite3.OperationalError:
                        loggers["operations"].info(_("No alembic_version table found"))
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
            if self.use_postgres:
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
            else:
                # For SQLite, follow existing procedure
                if self.db_path.exists():
                    self.db_path.unlink()
                    
            db_identifier = "PostgreSQL database" if self.use_postgres else f"SQLite database at {str(self.db_path)}"
            loggers["operations"].info(_("Creating new database", db_identifier=db_identifier))

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
            if not self.use_postgres and self.db_path.exists():
                self.db_path.unlink()
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
        if self.use_postgres:
            # PostgreSQL validation
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
                
        else:
            # SQLite validation (existing functionality)
            if not self.db_path.exists():
                loggers["operations"].info(_("Database file does not exist", db_path=str(self.db_path)))
                return False

            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # First check if it's a valid SQLite database
                    try:
                        cursor.execute("PRAGMA integrity_check")
                    except sqlite3.DatabaseError:
                        loggers["operations"].warning(_("Database file is corrupted"))
                        return False

                    # Check if it's at the latest migration
                    if self.needs_upgrade():
                        loggers["operations"].warning(_("Database needs migration"))
                        return False

                    # Check for required tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = {row[0] for row in cursor.fetchall()}

                    required_tables = {"qr_codes", "alembic_version"}
                    missing_tables = required_tables - tables

                    if missing_tables:
                        loggers["operations"].warning(
                            _("Missing required tables", missing=list(missing_tables))
                        )
                        return False

                    # Verify qr_codes table structure
                    cursor.execute("PRAGMA table_info(qr_codes)")
                    columns = {row[1] for row in cursor.fetchall()}
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

                    loggers["operations"].info(_("SQLite database validation successful"))
                    return True

            except sqlite3.DatabaseError as e:
                loggers["operations"].warning(_("Invalid SQLite database", error=str(e)))
                return False
            except Exception as e:
                loggers["errors"].error(
                    _(
                        "Error validating database",
                        error=str(e),
                        traceback=traceback.format_exc(),
                    )
                )
                return False


def run_cli():
    """Process command line arguments."""
    parser = argparse.ArgumentParser(description="Database management tool")
    parser.add_argument("--init", action="store_true", help="Initialize a fresh database")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    parser.add_argument("--check", action="store_true", help="Check if migrations are needed")
    parser.add_argument("--validate", action="store_true", help="Validate database structure")
    parser.add_argument("--postgres", action="store_true", help="Force PostgreSQL mode for testing")
    parser.add_argument("--create-backup", action="store_true", help="Create a database backup")

    args = parser.parse_args()

    # Override USE_POSTGRES based on command line for testing
    global USE_POSTGRES
    if args.postgres:
        USE_POSTGRES = True
        loggers["operations"].info(_("PostgreSQL mode enabled via command line"))

    if not (args.init or args.migrate or args.check or args.validate or args.create_backup):
        parser.print_help()
        return

    db_manager = DatabaseManager(
        db_path=DB_PATH,
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
