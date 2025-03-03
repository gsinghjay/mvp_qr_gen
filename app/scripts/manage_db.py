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
import shutil
import sqlite3
import sys
import traceback
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

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
        self.ensure_directories()
        loggers["operations"].info(
            _(
                "DatabaseManager initialized",
                db_path=str(db_path),
                backup_dir=str(backup_dir),
                alembic_ini=str(alembic_ini),
            )
        )

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            loggers["operations"].info(
                _(
                    "Directories verified",
                    backup_dir=str(self.backup_dir),
                    db_dir=str(self.db_path.parent),
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
        if not self.db_path.exists():
            loggers["backups"].info(
                _("No database file exists, skipping backup", db_path=str(self.db_path))
            )
            yield None
            return

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"qr_codes_{timestamp}.db"

        try:
            loggers["backups"].info(
                _(
                    "Creating database backup",
                    source=str(self.db_path),
                    destination=str(backup_path),
                )
            )
            shutil.copy2(self.db_path, backup_path)

            # Log backup file size
            backup_size = backup_path.stat().st_size
            loggers["backups"].info(
                _(
                    "Backup created successfully",
                    backup_path=str(backup_path),
                    size_bytes=backup_size,
                )
            )

            yield backup_path

            # Cleanup old backups (keep last 5)
            self._cleanup_old_backups()
        except Exception as e:
            loggers["errors"].error(
                _("Backup failed", error=str(e), traceback=traceback.format_exc())
            )
            raise

    def _cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old database backups, keeping only the most recent ones."""
        try:
            backups = sorted(
                self.backup_dir.glob("qr_codes_*.db"),
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
        if not self.db_path.exists():
            loggers["operations"].info(_("No database file exists", db_path=str(self.db_path)))
            return None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version_num FROM alembic_version")
                result = cursor.fetchone()
                revision = result[0] if result else None
                loggers["operations"].info(
                    _("Current database revision retrieved", revision=revision)
                )
                return revision
        except sqlite3.OperationalError as e:
            loggers["operations"].info(_("No alembic_version table found", error=str(e)))
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
            # Remove existing database if it exists
            if self.db_path.exists():
                self.db_path.unlink()

            loggers["operations"].info(_("Creating new database", db_path=str(self.db_path)))

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
            if self.db_path.exists():
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
        Validate if the database file is a valid SQLite database with required tables.
        Returns True if valid, False otherwise.
        """
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

                loggers["operations"].info(_("Database validation successful"))
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


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument("--init", action="store_true", help="Initialize a fresh database")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    parser.add_argument("--check", action="store_true", help="Check if migrations are needed")
    parser.add_argument("--validate", action="store_true", help="Validate database structure")
    args = parser.parse_args()

    try:
        manager = DatabaseManager(DB_PATH, BACKUP_DIR, ALEMBIC_INI)

        if args.validate:
            loggers["operations"].info(_("Validating database"))
            is_valid = manager.validate_database()
            sys.exit(0 if is_valid else 1)

        if args.init:
            loggers["operations"].info(_("Initializing database"))
            if not manager.init_database():
                sys.exit(1)
            sys.exit(0)

        if args.migrate:
            loggers["operations"].info(_("Running database migrations"))
            if not manager.run_migrations():
                sys.exit(1)
            sys.exit(0)

        if args.check:
            loggers["operations"].info(_("Database upgrade check"))
            needs_upgrade = manager.needs_upgrade()
            sys.exit(1 if needs_upgrade else 0)

    except Exception as e:
        loggers["errors"].error(
            _("Script execution failed", error=str(e), traceback=traceback.format_exc())
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
