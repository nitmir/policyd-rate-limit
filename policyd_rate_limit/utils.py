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
import imp

from policyd_rate_limit.const import SQLITE_DB, MYSQL_BD, PGSQL_BD


def import_config():
    if os.path.isfile(os.path.expanduser("~/.config/policyd-rate-limit.conf")):
        sys.stderr.write(
            'Using config file "%s"\n' % os.path.expanduser("~/.config/policyd-rate-limit.conf")
        )
        config = imp.load_source('config', os.path.expanduser("~/.config/policyd-rate-limit.conf"))
    elif os.path.isfile("/etc/policyd-rate-limit.conf"):
        sys.stderr.write('Using config file "/etc/policyd-rate-limit.conf"\n')
        config = imp.load_source('config', "/etc/policyd-rate-limit.conf")
    else:
        sys.stderr.write("No config file found, using default config")
        from policyd_rate_limit import config
    return config


config = import_config()


def make_cursor(name, backend, config):
    if backend == MYSQL_BD:
        import MySQLdb
        methods = {
             '_db': collections.defaultdict(lambda: MySQLdb.connect(**config)),
             'backend': MYSQL_BD,
             'backend_module': MySQLdb,
         }
    elif backend == SQLITE_DB:
        import sqlite3
        methods = {
             '_db': collections.defaultdict(lambda: sqlite3.connect(**config)),
             'backend': SQLITE_DB,
             'backend_module': sqlite3,
         }
    elif backend == PGSQL_BD:
        import psycopg2
        methods = {
             '_db': collections.defaultdict(lambda: psycopg2.connect(**config)),
             'backend': PGSQL_BD,
             'backend_module': psycopg2,
         }
    else:
        raise RuntimeError("backend %s unknown" % backend)
    newclass = type(name, (_cursor,), methods)
    return newclass


class _cursor(object):
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
        if self.backend in [MYSQL_BD, PGSQL_BD]:
            try:
                if self.backend == MYSQL_BD:
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

if config.backend == SQLITE_DB:
    cursor = make_cursor("sqlite_cursor", config.backend, config.sqlite_config)
    format_str = "?"
elif config.backend == MYSQL_BD:
    cursor = make_cursor("mysql_cursor", config.backend, config.mysql_config)
    format_str = "%s"
elif config.backend == PGSQL_BD:
    cursor = make_cursor("pgsql_cursor", config.backend, config.pgsql_config)
    format_str = "%s"
else:
    raise RuntimeError("backend %s unknown" % config.backend)

with cursor() as cur:
    query = """CREATE TABLE IF NOT EXISTS "mail_count" (
  "id" varchar(40) NOT NULL,
  "date" int(32) NOT NULL
);"""
    cur.execute(query)
    try:
        cur.execute('CREATE INDEX mail_count_index ON mail_count(id, date)')
    except cursor.backend_module.Error as error:
        if error.args[0] == 'index mail_count_index already exists':
            pass


config.limited_netword = [netaddr.IPNetwork(net) for net in config.limited_netword]
