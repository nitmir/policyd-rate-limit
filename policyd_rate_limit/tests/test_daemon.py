# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License version 3 for
# more details.
#
# You should have received a copy of the GNU General Public License version 3
# along with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# (c) 2016 Valentin Samir
import os
import tempfile
from unittest import TestCase

from policyd_rate_limit.tests import utils as test_utils


class DaemonTestCase(TestCase):

    def setUp(self):
        self.base_config = dict(
            SOCKET=tempfile.mktemp('.sock'),
            sqlite_config={"database": tempfile.mktemp('.sqlite3')},
            pidfile=tempfile.mktemp('.pid'),
            limit_by_sasl=True,
            limit_by_ip=True,
            limited_networks=["192.168.0.0/16", "ffee::/64"],
            debug=True,
            report=True,
            report_limits=[60, 86400],
            user="root",
            group="root",
            count_mode=0,
        )

    def tearDown(self):
        if os.path.isfile(self.base_config["sqlite_config"]["database"]):
            os.remove(self.base_config["sqlite_config"]["database"])

    def test_main_unix_socket(self):
        with test_utils.lauch(self.base_config) as cfg:
            self.base_test(cfg)

    def test_main_afinet_socket(self):
        self.base_config["SOCKET"] = ["127.0.0.1", 27184]
        with test_utils.lauch(self.base_config) as cfg:
            self.base_test(cfg)

    # travis CI/Github Action has no IPv6 support
    # def test_main_afinet6_socket(self):
    #     self.base_config["SOCKET"] = ["::1", 27184]
    #     with test_utils.lauch(self.base_config) as cfg:
    #         self.base_test(cfg)

    def test_no_debug_no_report(self):
        self.base_config["debug"] = False
        self.base_config["report"] = False
        with test_utils.lauch(self.base_config) as cfg:
            self.base_test(cfg)

    def test_limit(self):
        with test_utils.lauch(self.base_config) as cfg:
            for i in range(10):
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
            # the eleventh counted requests should fail
            data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")

    def test_limit_batch(self):
        with test_utils.lauch(self.base_config) as cfg:
            # Send a batch of mails
            for i in range(10):
                data = test_utils.send_policyd_request(
                    cfg["SOCKET"], sasl_username="test", instance="test"
                )
                self.assertEqual(data.strip(), b"action=dunno")
            # the eleventh counted requests should fail and the 10 previous should be discard
            data = test_utils.send_policyd_request(
                cfg["SOCKET"], sasl_username="test", instance="test"
            )
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")
            # The limit should have be reverted (cf instance)
            for i in range(10):
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
            # the eleventh counted requests should fail
            data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")

    def test_limit_batch2(self):
        self.base_config["count_mode"] = 1
        with test_utils.lauch(self.base_config) as cfg:
            # Send a batch of mails
            data = test_utils.send_policyd_request(
                cfg["SOCKET"], sasl_username="test", protocol_state="DATA", recipient_count=11
            )
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")
            # The limit should have be reverted (cf instance)
            data = test_utils.send_policyd_request(
                cfg["SOCKET"], sasl_username="test", protocol_state="DATA", recipient_count=10
            )
            self.assertEqual(data.strip(), b"action=dunno")
            # the eleventh counted requests should fail
            data = test_utils.send_policyd_request(
                cfg["SOCKET"], sasl_username="test", protocol_state="DATA", recipient_count=1
            )
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")

    def test_slow_connection(self):
        with test_utils.lauch(self.base_config) as cfg:
            with test_utils.sock(cfg["SOCKET"]) as s:
                msg = test_utils.postfix_request(sasl_username="test")
                i = 0
                s.send(msg[i:10])
                i += 10
                # run another request before the previous one is ended
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
                s.send(msg[i:1])
                i += 1
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
                s.send(msg[i:])
                datal = []
                datal.append(s.recv(2))
                # run another request before the previous one is ended
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
                datal.append(s.recv(1024))
                data = b"".join(datal)
                self.assertEqual(data.strip(), b"action=dunno")

    def test_database_unavailable(self):
        # create the database
        with open(self.base_config["sqlite_config"]["database"], 'a'):
            pass
        # make it unavailable
        os.chmod(self.base_config["sqlite_config"]["database"], 0)
        # lauch policyd-rate-limit with the database navailable
        with test_utils.lauch(self.base_config) as cfg:
            # as long as the database is unavailable, all response should be dunno
            for i in range(20):
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
            # make the database available, it should be initialized upon the next request
            os.chmod(self.base_config["sqlite_config"]["database"], 0o644)
            # these requests should be counted
            for i in range(10):
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
                self.assertEqual(data.strip(), b"action=dunno")
            # the eleventh counted requests should fail
            data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")

    def test_bad_config(self):
        self.base_config["backend"] = 1000
        with test_utils.lauch(self.base_config, get_process=True) as p:
            self.assertEqual(p.wait(), 5)

    def test_get_config(self):
        with test_utils.lauch(
            self.base_config,
            get_process=True,
            options=["--get-config", "pidfile"]
        ) as p:
            self.assertEqual(p.wait(), 0)
            self.assertEqual(p.stdout.read(), self.base_config["pidfile"].encode())
        with test_utils.lauch(
            self.base_config,
            get_process=True,
            options=["--get-config", "sqlite_config.database"]
        ) as p:
            self.assertEqual(p.wait(), 0)
            self.assertEqual(
                p.stdout.read(),
                self.base_config["sqlite_config"]["database"].encode()
            )
        with test_utils.lauch(
            self.base_config,
            get_process=True,
            options=["--get-config", "foo"]
        ) as p:
            self.assertEqual(p.wait(), 1)
        with test_utils.lauch(
            None,
            get_process=True,
            options=["--get-config", "pidfile"]
        ) as p:
            self.assertEqual(p.wait(), 0)
            self.assertEqual(
                p.stdout.read(),
                b'/var/run/policyd-rate-limit/policyd-rate-limit.pid'
            )

    def test_no_config_file_found(self):
        with test_utils.lauch(None, get_process=True) as p:
            self.assertEqual(p.wait(), 5)

    def test_already_running(self):
        with test_utils.lauch(self.base_config, no_coverage=True, get_process=True) as p1:
            pid = p1.pid
            with test_utils.lauch(self.base_config, get_process=True) as p2:
                self.assertEqual(p2.wait(), 3)
        with open(self.base_config["pidfile"], 'w') as f:
            f.write("%s" % pid)
        try:
            with test_utils.lauch(self.base_config, get_process=True) as p:
                pass
            self.assertEqual(p.wait(), 0)
            with open(self.base_config["pidfile"], 'w') as f:
                f.write("foo")
            with test_utils.lauch(self.base_config, get_process=True) as p:
                pass
            self.assertEqual(p.wait(), 0)
            with open(self.base_config["pidfile"], 'w') as f:
                f.write("")
            os.chmod(self.base_config["pidfile"], 0)
            with test_utils.lauch(self.base_config, get_process=True) as p:
                self.assertEqual(p.wait(timeout=5), 6)
        finally:
            try:
                os.remove(self.base_config["pidfile"])
            except OSError:
                pass

    def test_bad_socket_bind_address(self):
        self.base_config["SOCKET"] = ["toto", 1234]
        with test_utils.lauch(self.base_config, get_process=True, no_wait=True) as p:
            self.assertEqual(p.wait(), 4)
        self.base_config["SOCKET"] = ["192.168::1", 1234]
        with test_utils.lauch(self.base_config, get_process=True, no_wait=True) as p:
            self.assertEqual(p.wait(), 6)

    def test_clean(self):
        self.base_config["report_to"] = "foo@example.com"
        with test_utils.lauch(self.base_config, options=["--clean"], get_process=True) as p:
            self.assertEqual(p.wait(), 0)
        self.base_config["report_only_if_needed"] = False
        self.base_config["smtp_server"] = "localhost"
        with test_utils.lauch(self.base_config, options=["--clean"], get_process=True) as p:
            self.assertEqual(p.wait(), 8)

    def test_limits_by_id(self):
        self.base_config["limits_by_id"] = {'foo': [[2, 60]], 'bar': []}
        with test_utils.lauch(self.base_config) as cfg:
            self.base_test(cfg)
            for i in range(20):
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="bar")
                self.assertEqual(data.strip(), b"action=dunno")
            for i in range(2):
                data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="foo")
                self.assertEqual(data.strip(), b"action=dunno")
            data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="foo")
            self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")

    def base_test(self, cfg):
        # test limit by sasl username
        for i in range(10):
            data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
            self.assertEqual(data.strip(), b"action=dunno")
        data = test_utils.send_policyd_request(cfg["SOCKET"], sasl_username="test")
        self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")
        # test limit by ip
        for i in range(10):
            data = test_utils.send_policyd_request(cfg["SOCKET"], client_address="192.168.0.1")
            self.assertEqual(data.strip(), b"action=dunno")
        data = test_utils.send_policyd_request(cfg["SOCKET"], client_address="192.168.0.1")
        self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")
        # test limit by ip in ipv6
        for i in range(10):
            data = test_utils.send_policyd_request(cfg["SOCKET"], client_address="ffee::1")
            self.assertEqual(data.strip(), b"action=dunno")
        data = test_utils.send_policyd_request(cfg["SOCKET"], client_address="ffee::1")
        self.assertEqual(data.strip(), b"action=defer_if_permit Rate limit reach, retry later")
        # test limit by ip not limited
        for i in range(10):
            data = test_utils.send_policyd_request(cfg["SOCKET"], client_address="10.0.0.1")
            self.assertEqual(data.strip(), b"action=dunno")
        data = test_utils.send_policyd_request(cfg["SOCKET"], client_address="10.0.0.1")
        self.assertEqual(data.strip(), b"action=dunno")
        # test with bad protocol state
        for i in range(10):
            data = test_utils.send_policyd_request(
                cfg["SOCKET"],
                sasl_username="test",
                protocol_state="VRFY"
            )
            self.assertEqual(data.strip(), b"action=dunno")
        data = test_utils.send_policyd_request(
            cfg["SOCKET"],
            sasl_username="test",
            protocol_state="VRFY"
        )
        self.assertEqual(data.strip(), b"action=dunno")
