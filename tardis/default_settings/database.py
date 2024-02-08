# Dictionary containing the settings for all databases to be used.
# The DATABASES setting must configure a default database;
# any number of additional databases may also be specified.
DATABASES = {
    "default": {
        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        "ENGINE": "django.db.backends.sqlite3",
        # Name of the database to use. For SQLite, it's the full path.
        "NAME": "db.sqlite3",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}
