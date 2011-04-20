"""
 Command for backup database
"""
from os import makedirs
from os.path import exists, join
import subprocess
import time

from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    help = "Backup database. Only Mysql and Postgresql engines are implemented"

    option_list = BaseCommand.option_list + (
        make_option('-r', '--restore', default=False,
            help='Restore database instead of dumping it'),
        make_option('-d', '--database', default=False,
            help='Database settings to be used'),
        )

    def handle(self, *args, **options):
        from django.conf import settings

        database = options.get('database')
        if not database:
            database = 'default'
        db_settings = settings.DATABASES[database]

        self.engine = db_settings['ENGINE'].rsplit('.', 1)[-1]
        self.db = db_settings['NAME']
        self.user = db_settings['USER']
        self.passwd = db_settings['PASSWORD']
        self.host = db_settings['HOST']
        self.port = db_settings['PORT']

        infile = options.get('restore')
        if infile:
            self.restore(infile)
        else:
            self.backup()

    def backup(self):
        backup_dir = 'backups'
        if not exists(backup_dir):
            makedirs(backup_dir)
        outfile = join(backup_dir, 'backup_%s.sql' % time.strftime('%y%m%d%S'))

        if self.engine == 'mysql':
            print 'Doing Mysql backup to database %s into %s'\
                % (self.db, outfile)
            self.do_mysql_backup(outfile)
        elif self.engine in ('postgresql_psycopg2', 'postgresql'):
            print 'Doing Postgresql backup to database %s into %s'\
                % (self.db, outfile)
            self.do_postgresql_backup(outfile)
        else:
            print 'Backup in %s engine not implemented' % self.engine

    def restore(self, infile):
        if self.engine == 'mysql':
            print 'Doing Mysql restore to database %s from %s'\
                % (self.db, infile)
            self.do_mysql_restore(infile)
        elif self.engine in ('postgresql_psycopg2', 'postgresql'):
            print 'Doing Postgresql restore to database %s from %s'\
                % (self.db, infile)
            self.do_postgresql_restore(infile)
        else:
            print 'Restore in %s engine not implemented' % self.engine

    def do_mysql_backup(self, outfile):
        args = []
        if self.user:
            args += ["--user=%s" % self.user]
        if self.passwd:
            args += ["--password=%s" % self.passwd]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        args += [self.db]

        pipe = subprocess.Popen('mysqldump %s' % ' '.join(args),
                               shell=True,
                               stdout=open(outfile, 'w'),
                               stderr=subprocess.PIPE)

        stdout, stderr = pipe.communicate()
        if stderr:
            print stderr

    def do_mysql_restore(self, infile):
        args = []
        if self.user:
            args += ["--user=%s" % self.user]
        if self.passwd:
            args += ["--password=%s" % self.passwd]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        args += [self.db]

        pipe = subprocess.Popen('mysql %s' % ' '.join(args),
                                shell=True,
                                stdin=open(infile),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        stdout, stderr = pipe.communicate()
        if stdout:
            print stdout
        if stderr:
            print stderr

    def do_postgresql_backup(self, outfile):
        args = []
        if self.user:
            args += ["--username=%s" % self.user]
        if self.passwd:
            args += ["--password"]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        if self.db:
            args += [self.db]

        pipe = subprocess.Popen('pg_dump %s ' % ' '.join(args),
                                shell=True,
                                stdout=open(outfile, 'w'),
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)
        if self.passwd:
            stdout, stderr = pipe.communicate('%s\n' % self.passwd)
        else:
            stdout, stderr = pipe.communicate()
        if stdout:
            print stdout
        if stderr:
            print stderr

    def do_postgresql_restore(self, infile):
        args = []
        if self.user:
            args += ["--username=%s" % self.user]
        if self.passwd:
            args += ["--password"]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        if self.db:
            args += ["--dbname=%s" % self.db]

        pipe = subprocess.Popen('psql %s -f %s' % (' '.join(args), infile),
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)
        if self.passwd:
            stdout, stderr = pipe.communicate('%s\n' % self.passwd)
        else:
            stdout, stderr = pipe.communicate()
        if stdout:
            print stdout
        if stderr:
            print stderr
