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
import os
import sys
import socket
import time

from policyd_rate_limit import utils
from policyd_rate_limit.utils import cursor, config


class Pass(Exception):
    pass


class Policyd(object):

    def socket(self):
        # if socket is a string assume it is the path to an unix socket
        if isinstance(config.SOCKET, str):
            try:
                os.remove(config.SOCKET)
            except OSError:
                if os.path.exists(config.SOCKET):
                    raise
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # else asume its a tuple (bind_ip, bind_port)
        elif '.' in config.SOCKET[0]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif ':' in config.SOCKET[0]:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            raise ValueError("bad socket %s" % config.SOCKET)
        self.sock = sock

    def close_socket(self):
        self.sock.close()
        if isinstance(config.SOCKET, str):
            try:
                os.remove(config.SOCKET)
            except OSError as error:
                sys.stderr.write("%s\n" % error)

    def run(self):
        sock = self.sock
        sock.bind(config.SOCKET)
        if isinstance(config.SOCKET, str):
            os.chmod(config.SOCKET, config.socket_permission)
        sock.listen(1)
        while True:
            if config.debug:
                sys.stderr.write('waiting for a connection\n')
            connection, client_address = sock.accept()
            try:
                if config.debug:
                    sys.stderr.write('connection from %s\n' % client_address)
                buffer = []
                while True:
                    data = connection.recv(1024).decode('UTF-8')
                    if config.debug:
                        sys.stderr.write(data)
                    buffer.append(data)
                    if len(data) < 2:
                        data = u"".join(buffer)
                        buffer = [data]
                    if data[-2:] == "\n\n":
                        data = u"".join(buffer)
                        request = {}
                        for line in data.split("\n"):
                            line = line.strip()
                            try:
                                key, value = line.split(u"=", 1)
                                if value:
                                    request[key] = value
                            except ValueError:
                                pass
                        self.action(connection, request)
                        break
            finally:
                # Clean up the connection
                connection.close()

    def action(self, connection, request):
        id = None
        action = config.success_action
        with cursor() as cur:
            try:
                if config.limit_by_sasl and u'sasl_username' in request:
                    id = request[u'sasl_username']
                elif (
                    config.limit_by_ip and
                    u'client_address' in request and
                    utils.is_ip_limited(request[u'client_address'])
                ):
                    id = request[u'client_address']
                else:
                    raise Pass()
                for mail_nb, delta in config.limits:
                    if cur.execute(
                        (
                            "SELECT COUNT(*) FROM mail_count "
                            "WHERE id = %s AND date >= %s"
                        ) % ((utils.format_str,)*2),
                        (id, int(time.time() - delta))
                    ):
                        nb = cur.fetchone()[0]
                        if nb >= mail_nb:
                            action = u"%s Rate limit reach, retry later" % config.fail_action
                            raise Pass()
            except Pass:
                pass
            if action == config.success_action and id is not None:
                if config.debug:
                    sys.stderr.write(u"insert id %s\n" % id)
                cur.execute(
                    "INSERT INTO mail_count VALUES (%s, %s)" % ((utils.format_str,)*2),
                    (id, int(time.time()))
                )
        data = u"action=%s\n\n" % action
        if config.debug:
            sys.stderr.write(data)
        connection.sendall(data.encode('UTF-8'))
