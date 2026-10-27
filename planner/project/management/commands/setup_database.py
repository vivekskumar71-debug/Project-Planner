# setup code
import getpass
import re
import secrets

import MySQLdb
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the configured MySQL database and user, and grant database permissions."

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]
        if database["ENGINE"] != "django.db.backends.mysql":
            raise CommandError("The default database engine must be MySQL.")

        database_name = database["NAME"]
        database_user = database["USER"]
        if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
            raise CommandError("DB_NAME may contain only letters, numbers, and underscores.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", database_user):
            raise CommandError("DB_USER may contain only letters, numbers, and underscores.")

        admin_user = input("MySQL administrator username [root]: ").strip() or "root"
        admin_password = getpass.getpass("MySQL administrator password: ")
        account_host = input("Host allowed for the application user [localhost]: ").strip() or "localhost"
        if not re.fullmatch(r"[A-Za-z0-9_.%-]+", account_host):
            raise CommandError("The application user's host contains unsupported characters.")

        database_password = secrets.token_urlsafe(32)
        connection = None
        try:
            connection = MySQLdb.connect(
                host=database["HOST"] or "localhost",
                port=int(database["PORT"] or 3306),
                user=admin_user,
                passwd=admin_password,
            )
            cursor = connection.cursor()
            quoted_database = f"`{database_name}`"
            quoted_user = connection.literal(database_user).decode("ascii")
            quoted_host = connection.literal(account_host).decode("ascii")
            quoted_password = connection.literal(database_password).decode("ascii")

            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {quoted_database}")
            cursor.execute(
                f"CREATE USER IF NOT EXISTS {quoted_user}@{quoted_host} "
                f"IDENTIFIED BY {quoted_password}"
            )
            cursor.execute(
                f"ALTER USER {quoted_user}@{quoted_host} IDENTIFIED BY {quoted_password}"
            )
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON {quoted_database}.* TO {quoted_user}@{quoted_host}"
            )
            connection.commit()
        except MySQLdb.Error as exc:
            raise CommandError(f"MySQL setup failed: {exc}") from exc
        finally:
            if connection is not None:
                connection.close()

        env_path = settings.BASE_DIR.parent / ".env"
        try:
            self._save_database_password(env_path, database_password)
        except OSError as exc:
            raise CommandError(
                f"MySQL setup succeeded, but the password could not be saved to {env_path}: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Database '{database_name}' and user '{database_user}' are ready; "
                f"all database privileges were granted and DB_PASSWORD was saved to .env."
            )
        )

    @staticmethod
    def _save_database_password(env_path, password):
        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
        pattern = re.compile(r"^(\s*DB_PASSWORD\s*=\s*).*(\r?\n)?$")
        for index, line in enumerate(lines):
            match = pattern.match(line)
            if match:
                newline = match.group(2) or ""
                lines[index] = f"{match.group(1)}'{password}'{newline}"
                break
        else:
            if lines and not lines[-1].endswith(("\n", "\r")):
                lines[-1] += "\n"
            lines.append(f"DB_PASSWORD = '{password}'\n")

        temporary_path = env_path.with_name(f"{env_path.name}.tmp")
        temporary_path.write_text("".join(lines), encoding="utf-8")
        temporary_path.replace(env_path)
