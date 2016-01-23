# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License version 3 for
# more details.
#
# You should have received a copy of the GNU General Public License version 3
# along with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# (c) 2015 Valentin Samir
# -*- mode: python; coding: utf-8 -*-
import os
import sys
import threading
import collections
import netaddr
import time
import imp
import pwd
import grp

from policyd_rate_limit.const import SQLITE_DB, MYSQL_DB, PGSQL_DB
from policyd_rate_limit import config as default_config


class Config(object):
    """Act as a config module, missing parameters fallbacks to default_config"""
    def __init__(self):
        # search for config files in the following locations
        config_files = [
            os.path.expanduser("~/.config/policyd-rate-limit.conf"),
            "/etc/policyd-rate-limit.conf",
        ]
        for config_file in config_files:
            if os.path.isfile(config_file):
                # sys.stdout.write('Using config file "%s"\n' % config_file)
                self.config = imp.load_source('config', config_file)
                break
        # if not config file found, fallback to default config.
        else:
            sys.stdout.write("No config file found, using default config")
            self.config = default_config

        self.limited_netword = [netaddr.IPNetwork(net) for net in self.limited_netword]

    def __getattr__(self, name):
        try:
            return getattr(self.config, name)
        # If an parameter is not defined in the config file, return its default value.
        except AttributeError:
            return getattr(default_config, name)


def make_directories():
    """Create directory for pid and socket and chown if needed"""
    try:
        uid = pwd.getpwnam(config.user).pw_uid
    except KeyError:
        raise ValueError("User %s in config do not exists" % config.user)
    try:
        gid = grp.getgrnam(config.group).gr_gid
    except KeyError:
        raise ValueError("Group %s in config do not exists" % config.group)
    pid_dir = os.path.dirname(config.pidfile)
    if not os.path.exists(pid_dir):
        os.mkdir(pid_dir)
    if not os.listdir(pid_dir):
        os.chmod(pid_dir, 0o755)
        os.chown(pid_dir, uid, gid)
    if isinstance(config.SOCKET, str):
        socket_dir = os.path.dirname(config.SOCKET)
        if not os.path.exists(socket_dir):
            os.mkdir(socket_dir)
        if not os.listdir(socket_dir):
            os.chown(socket_dir, uid, gid)


def drop_privileges():
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(config.user).pw_uid
    running_gid = grp.getgrnam(config.group).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    os.umask(0o077)


def make_cursor(name, backend, config):
    """Create a cursor class usable as a context manager, binding to the backend selected"""
    if backend == MYSQL_DB:
        import MySQLdb
        methods = {
             '_db': collections.defaultdict(lambda: MySQLdb.connect(**config)),
             'backend': MYSQL_DB,
             'backend_module': MySQLdb,
         }
    elif backend == SQLITE_DB:
        import sqlite3
        methods = {
             '_db': collections.defaultdict(lambda: sqlite3.connect(**config)),
             'backend': SQLITE_DB,
             'backend_module': sqlite3,
         }
    elif backend == PGSQL_DB:
        import psycopg2
        methods = {
             '_db': collections.defaultdict(lambda: psycopg2.connect(**config)),
             'backend': PGSQL_DB,
             'backend_module': psycopg2,
         }
    else:
        raise RuntimeError("backend %s unknown" % backend)
    newclass = type(name, (_cursor,), methods)
    return newclass


class _cursor(object):
    """cursor template class"""
    backend = None
    backend_module = None

    @classmethod
    def get_db(cls):
        return cls._db[threading.current_thread()]

    @classmethod
    def set_db(cls, value):
        cls._db[threading.current_thread()] = value

    @classmethod
    def del_db(cls):
        try:
            cls._db[threading.current_thread()].close()
        except:
            pass
        try:
            del cls._db[threading.current_thread()]
        except KeyError:
            pass

    def __enter__(self):
        self.cur = self.get_db().cursor()
        if self.backend in [MYSQL_DB, PGSQL_DB]:
            try:
                if self.backend == MYSQL_DB:
                    self.cur.execute("DO 0")
                else:
                    self.cur.execute("SELECT 0")
                    self.cur.fetchone()
            except self.backend_module.Error as error:
                # SQL server has gone away, probably a timeout
                if error.args[0] in [2006, 8000, 8003, 8006]:
                    self.del_db()
                    self.cur.close()
                    self.cur = self.get_db().cursor()
        return self.cur

    def __exit__(self, exc_type, exc_value, traceback):
        self.cur.close()
        self.get_db().commit()


def is_ip_limited(ip):
    ip = netaddr.IPAddress(ip)
    for net in config.limited_netword:
        if ip in net:
            return True
    return False


def clean():
    """Delete old records from the database"""
    max_delta = 0
    for nb, delta in config.limits:
        max_delta = max(max_delta, delta)
    # remove old record older than 2*max_delta
    expired = int(time.time() - max_delta - max_delta)
    with cursor() as cur:
        cur.execute("DELETE FROM mail_count WHERE date <= %s" % format_str, (expired,))
        print("%d records deleted" % cur.rowcount)


def database_init():
    """Initialize database (create the table and index)"""
    with cursor() as cur:
        query = """CREATE TABLE IF NOT EXISTS mail_count (
      id varchar(40) NOT NULL,
      date int(32) NOT NULL
    );"""
        cur.execute(query)
        try:
            cur.execute('CREATE INDEX mail_count_index ON mail_count(id, date)')
        except cursor.backend_module.Error as error:
            if error.args[0] == 'index mail_count_index already exists':
                pass


def write_pidfile():
    try:
        with open(config.pidfile, 'w') as f:
            f.write("%s" % os.getpid())
    except PermissionError as error:
        raise ValueError("Unable to write pid file, %s." % error)


def remove_pidfile():
    try:
        os.remove(config.pidfile)
    except OSError:
        pass


# initialize config
config = Config()

# make the cursor class function of the configured backend
if config.backend == SQLITE_DB:
    cursor = make_cursor("sqlite_cursor", config.backend, config.sqlite_config)
    format_str = "?"
elif config.backend == MYSQL_DB:
    cursor = make_cursor("mysql_cursor", config.backend, config.mysql_config)
    format_str = "%s"
elif config.backend == PGSQL_DB:
    cursor = make_cursor("pgsql_cursor", config.backend, config.pgsql_config)
    format_str = "%s"
else:
    raise RuntimeError("backend %s unknown" % config.backend)




