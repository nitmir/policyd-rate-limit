# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License version 3 for
# more details.
#
# You should have received a copy of the GNU General Public License version 3
# along with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# (c) 2015-2016 Valentin Samir
# -*- mode: python; coding: utf-8 -*-
import os
import threading
import collections
import netaddr
import time
import imp
import pwd
import grp
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from policyd_rate_limit.const import SQLITE_DB, MYSQL_DB, PGSQL_DB
from policyd_rate_limit import config as default_config


class Config(object):
    """Act as a config module, missing parameters fallbacks to default_config"""
    def __init__(self, config_file=None):
        if config_file is None:
            # search for config files in the following locations
            config_files = [
                os.path.expanduser("~/.config/policyd-rate-limit.conf"),
                "/etc/policyd-rate-limit.conf",
            ]
        else:
            config_files = [config_file]
        for config_file in config_files:
            if os.path.isfile(config_file):
                try:
                    self._config = imp.load_source('config', config_file)
                    self.config_file = config_file
                    break
                except PermissionError:
                    pass
        # if not config file found, raise en error
        else:
            raise ValueError(
                "No config file found or bad permissions, searched for %s" % (
                    ", ".join(config_files),
                )
            )

        self.limited_netword = [netaddr.IPNetwork(net) for net in self.limited_netword]

    def __getattr__(self, name):
        try:
            return getattr(self._config, name)
        # If an parameter is not defined in the config file, return its default value.
        except AttributeError:
            return getattr(default_config, name)


class LazyConfig(object):
    """A lazy proxy to the Config class allowing to import config before it is initialized"""
    _config = None
    format_str = None

    def __getattr__(self, name):
        if self._config is None:
            raise RuntimeError("config is not initialized")
        return getattr(self._config, name)

    def setup(self, config_file=None):
        """initialize the config"""
        global cursor
        # initialize config
        self._config = Config(config_file)

        # make the cursor class function of the configured backend
        if config.backend == SQLITE_DB:
            cursor = make_cursor("sqlite_cursor", config.backend, config.sqlite_config)
            self.format_str = "?"
        elif config.backend == MYSQL_DB:
            cursor = make_cursor("mysql_cursor", config.backend, config.mysql_config)
            self.format_str = "%s"
        elif config.backend == PGSQL_DB:
            cursor = make_cursor("pgsql_cursor", config.backend, config.pgsql_config)
            self.format_str = "%s"
        else:
            raise RuntimeError("backend %s unknown" % config.backend)


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
    if config.backend == SQLITE_DB:
        try:
            db_dir = os.path.dirname(config.sqlite_config["database"])
            if not os.path.exists(db_dir):
                os.mkdir(db_dir)
            if not os.listdir(db_dir):
                os.chmod(db_dir, 0o700)
                os.chown(db_dir, uid, gid)
        except KeyError:
            pass


def drop_privileges():
    """If current running use is root, drop privileges to user and group set in the config"""
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
        try:
            import MySQLdb
        except ImportError:
            raise ValueError(
                "You need to install the python3 module MySQLdb to use the mysql backend"
            )
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
        try:
            import psycopg2
        except ImportError:
            raise ValueError(
                "You need to install the python3 module psycopg2 to use the postgresql backend"
            )
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
    """Check if ``ip`` is part of a network of ``config.limited_netword``"""
    ip = netaddr.IPAddress(ip)
    for net in config.limited_netword:
        if ip in net:
            return True
    return False


def print_fw(msg, length, filler=' ', align_left=True):
    msg = "%s" % msg
    if len(msg) > length:
        raise ValueError("%r must not be longer than %s" % (msg, length))
    if align_left:
        return "%s%s" % (msg, filler * (length - len(msg)))
    else:
        return "%s%s" % (filler * (length - len(msg)), msg)


def clean():
    """Delete old records from the database"""
    max_delta = 0
    for nb, delta in config.limits:
        max_delta = max(max_delta, delta)
    # remove old record older than 2*max_delta
    expired = int(time.time() - max_delta - max_delta)
    with cursor() as cur:
        cur.execute("DELETE FROM mail_count WHERE date <= %s" % config.format_str, (expired,))
        print("%d records deleted" % cur.rowcount)
        # if report is True, generate a mail report
        if config.report and config.report_to:
            send_report(cur)


def send_report(cur):
    cur.execute("SELECT id, delta, hit FROM limit_report")
    # list to sort ids by hits
    report = list(cur.fetchall())
    if not config.report_only_if_needed or report:
        if report:
            text = ["Below is the table of users who hit a limit since the last cleanup:", ""]
            # dist to groups deltas by ids
            report_d = collections.defaultdict(list)
            max_d = {'id': 2, 'delta': 5, 'hit': 3}
            for (id, delta, hit) in report:
                report_d[id].append((delta, hit))
                max_d['id'] = max(max_d['id'], len(id))
                max_d['delta'] = max(max_d['delta'], len(str(delta)))
                max_d['hit'] = max(max_d['hit'], len(str(hit)))
            # sort by hits
            report.sort(key=lambda x: x[2])
            # table header
            text.append(
                "|%s|%s|%s|" % (
                    print_fw("id", max_d['id']),
                    print_fw("delta", max_d['delta']),
                    print_fw("hit", max_d['hit'])
                )
            )
            # table header/data separation
            text.append(
                "|%s+%s+%s|" % (
                    print_fw("", max_d['id'], filler='-'),
                    print_fw("", max_d['delta'], filler='-'),
                    print_fw("", max_d['hit'], filler='-')
                )
            )

            for (id, _, _) in report:
                # sort by delta
                report_d[id].sort()
                for (delta, hit) in report_d[id]:
                    # add a table row
                    text.append(
                        "|%s|%s|%s|" % (
                            print_fw(id, max_d['id'], align_left=False),
                            print_fw("%ss" % delta, max_d['delta'], align_left=False),
                            print_fw(hit, max_d['hit'], align_left=False)
                        )
                    )
        else:
            text = ["No user hit a limit since the last cleanup"]
        text.extend(["", "-- ", "policyd-rate-limit"])

        # Start building the mail report
        msg = MIMEMultipart()
        msg['Subject'] = config.report_subject or ""
        msg['From'] = config.report_from or ""
        msg['To'] = config.report_to
        msg.attach(MIMEText("\n".join(text), 'plain'))

        # check that smtp_server is wekk formated
        if isinstance(config.smtp_server, tuple):
            if len(config.smtp_server) >= 2:
                server = smtplib.SMTP(config.smtp_server[0], config.smtp_server[1])
            elif len(config.smtp_server) == 1:
                server = smtplib.SMTP(config.smtp_server[0], 25)
            else:
                raise ValueError("bad smtp_server should be a tuple (server_adress, port)")
        else:
            raise ValueError("bad smtp_server should be a tuple (server_adress, port)")

        try:
            # should we use starttls ?
            if config.smtp_starttls:
                server.starttls()
            # should we use credentials ?
            if config.smtp_credentials:
                if isinstance(config.smtp_credentials, tuple) and len(config.smtp_credentials) >= 2:
                    server.login(config.smtp_credentials[0], config.smtp_credentials[1])
                else:
                    ValueError("bad smtp_credentials should be a tuple (login, password)")
            server.sendmail(config.report_from or "", config.report_to, msg.as_string())
        finally:
            server.quit()

        # The mail report has been successfully send, flush limit_report
        cur.execute("DELETE FROM limit_report")


def database_init():
    """Initialize database (create the table and index)"""
    with cursor() as cur:
        query = """CREATE TABLE IF NOT EXISTS mail_count (
      id varchar(40) NOT NULL,
      date int NOT NULL
    );"""
        # if report is enable, also create the table for storing report datas
        if config.report:
            query_report = """CREATE TABLE IF NOT EXISTS limit_report (
      id varchar(40) NOT NULL,
      delta int NOT NULL,
      hit int NOT NULL DEFAULT 0
    );"""
        try:
            if cursor.backend == MYSQL_DB:
                # ignore possible warnings about the table already existing
                warnings.filterwarnings('ignore', category=cursor.backend_module.Warning)
            cur.execute(query)
            if config.report:
                cur.execute(query_report)
        finally:
            warnings.resetwarnings()
        try:
            cur.execute('CREATE INDEX mail_count_index ON mail_count(id, date)')
        except cursor.backend_module.Error as error:
            if error.args[0] == 'index mail_count_index already exists':
                pass
        # if report is enable, create and unique index on (id, delta)
        if config.report:
            try:
                cur.execute('CREATE UNIQUE INDEX limit_report_index ON limit_report(id, delta)')
            except cursor.backend_module.Error as error:
                if error.args[0] == 'index limit_report_index already exists':
                    pass


def hit(cur, delta, id):
    # if no row is updated, (id, delta) do not exists and insert
    cur.execute(
        "UPDATE limit_report SET hit=hit+1 WHERE id = %s and delta = %s" % (
            (config.format_str,)*2
        ),
        (id, delta)
    )
    if cur.rowcount <= 0:
        cur.execute(
            "INSERT INTO limit_report (id, delta, hit) VALUES (%s, %s, 1)" % (
                (config.format_str,)*2
            ),
            (id, delta)
        )


def write_pidfile():
    """write current pid file to ``config.pidfile``"""
    try:
        with open(config.pidfile, 'w') as f:
            f.write("%s" % os.getpid())
    except PermissionError as error:
        raise ValueError("Unable to write pid file, %s." % error)


def remove_pidfile():
    """Try to remove ``config.pidfile``"""
    try:
        os.remove(config.pidfile)
    except OSError:
        pass


def get_config(dotted_string):
    """
        Return the config parameter designated by ``dotted_string``.
        Dots are used as separator between dict and key.
    """
    params = dotted_string.split('.')
    obj = getattr(config, params[0])
    for param in params[1:]:
        obj = obj[param]
    return obj


config = LazyConfig()
