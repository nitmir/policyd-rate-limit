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
from policyd_rate_limit.const import SQLITE_DB, MYSQL_DB, PGSQL_DB  # noqa: F401

debug = True

user = "policyd-rate-limit"
group = "policyd-rate-limit"
pidfile = "/var/run/policyd-rate-limit/policyd-rate-limit.pid"

mysql_config = {
    "user": "username",
    "passwd": "*****",
    "db": "database",
    "host": "localhost",
    "charset": 'utf8',
}

sqlite_config = {
    "database": "/var/lib/policyd-rate-limit/db.sqlite3",
}

pgsql_config = {
    "database": "database",
    "user": "username",
    "password": "*****",
    "host": "localhost",
}

backend = SQLITE_DB

# SOCKET=("127.0.0.1", 8552)
SOCKET = "/var/spool/postfix/ratelimit/policy"
socket_permission = 0o666

# list of (number of mails, number of seconds)
limits = [
    (10, 60),  # limit to 10 mails by minutes
    (150, 86400),  # limits to 150 mails by days
]

# dict of id -> limit list. Used to override limits and use custom limits for
# a particular id. Use an empty list for no limits for a particular id.
# ids are sasl usernames or ip addresses
limits_by_id = {}

limit_by_sasl = True
limit_by_sender = False
limit_by_ip = False

limited_networks = []

# actions return to postfix, see http://www.postfix.org/access.5.html for a list of actions.
success_action = "dunno"
fail_action = "defer_if_permit Rate limit reach, retry later"
# action to return to postfix when we are unable to contect the database backend
db_error_action = "dunno"


# if True, send a report to report_email about users reaching limits each time --clean is called
report = False
# from who to send emails reports
report_from = None
# address to send emails reports to. It can be a single email or a list of emails
report_to = None
# subject of the report email
report_subject = "policyd-rate-limit report"
# add number of seconds from the limits list for which you want to be reported
report_limits = [86400]
# only send a report if some users have reach a reported limit
report_only_if_needed = True

# The smtp server to use to send emails (host, port)
smtp_server = ("localhost", 25)
# Should we use starttls (you should set this to True if you use smtp_credentials)
smtp_starttls = False
# Should we use credentials to connect to smtp_server ? if yes set ("user", "password"), else None
smtp_credentials = None

# The time in seconds before an unused socket gets closed
delay_to_close = 300

# count mode. 0 for RCPT, 1 for DATA
count_mode = 0
