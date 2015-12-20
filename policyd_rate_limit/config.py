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
from policyd_rate_limit.const import SQLITE_DB, MYSQL_BD, PGSQL_BD

debug = True

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

limit_by_sasl = True
limit_by_ip = False

limited_netword = [
]
