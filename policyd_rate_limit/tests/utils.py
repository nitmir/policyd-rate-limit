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

import os
import sys
import socket
import yaml
import tempfile
import subprocess
import time
from contextlib import contextmanager


POSTFIX_TEMPLATE = """request=smtpd_access_policy
protocol_state=%(protocol_state)s
protocol_name=ESMTP
client_address=%(client_address)s
client_name=mail.example.com
reverse_client_name=mail.example.com
helo_name=mail.example.com
sender=bar@example.com
recipient=foo@example.com
recipient_count=0
queue_id=
instance=fd3.57cea9c4.143ea.0
size=0
etrn_domain=
stress=
sasl_method=
sasl_username=%(sasl_username)s
sasl_sender=
ccert_subject=
ccert_issuer=
ccert_fingerprint=
ccert_pubkey_fingerprint=
encryption_protocol=TLSv1.2
encryption_cipher=ECDHE-RSA-AES256-GCM-SHA384
encryption_keysize=256

"""


def postfix_request(sasl_username="", client_address="127.0.0.1", protocol_state="RCPT"):
    return (POSTFIX_TEMPLATE % {
                "sasl_username": sasl_username,
                "client_address": client_address,
                "protocol_state": protocol_state
            }).encode("utf-8")


@contextmanager
def sock(addr):
    if isinstance(addr, str):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    elif '.' in addr[0]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif ':' in addr[0]:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        raise ValueError(addr)
    try:
        s.connect(addr)
        yield s
    finally:
        s.close()


def send_policyd_request(addr, sasl_username="", client_address="127.0.0.1", protocol_state="RCPT"):
    with sock(addr) as s:
        s.send(
            postfix_request(sasl_username, client_address, protocol_state)
        )
        data = s.recv(1024)
        return data


def test_socket(addr):
    with sock(addr):
        return True


def gen_config(new_config):
    default_config = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'policyd-rate-limit.yaml')
    )
    with open(default_config) as f:
        config = yaml.load(f)
    config.update(new_config)
    cfg_path = tempfile.mktemp('.yaml')
    with open(cfg_path, 'w') as f:
        yaml.dump(config, f)
    return cfg_path


def launch_instance(new_config, options=None, no_coverage=False):
    if new_config:
        cfg_path = gen_config(new_config)
    else:
        cfg_path = None
    bin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'policyd-rate-limit')
    )
    # if bin_path do not exists, search in the PATH
    if not os.path.isfile(bin_path):
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"\'')
            bin_path = os.path.join(path, 'policyd-rate-limit')
            if os.path.isfile(bin_path):
                sys.stderr.write("Using %s\n" % bin_path)
                break
        else:
            raise RuntimeError("The binary policyd-rate-limit was not found, impossible to test it")
    if no_coverage:
        cmd = []
    else:
        cmd = ["coverage", "run"]
        if launch_instance.i > 0:
            cmd.append("-a")
    cmd.append(bin_path)
    if new_config:
        cmd.extend(["--file", cfg_path])
    if options is not None:
        cmd.extend(options)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    launch_instance.i += 1
    return (p, cfg_path)
launch_instance.i = 0


@contextmanager
def lauch(new_config, get_process=False, options=None, no_coverage=False, no_wait=False):
    (p, cfg_path) = launch_instance(new_config, options=options, no_coverage=no_coverage)
    try:
        if cfg_path:
            with open(cfg_path) as f:
                cfg = yaml.load(f)
            if not no_wait:
                time.sleep(0.01)
                for i in range(100):
                    try:
                        test_socket(cfg["SOCKET"])
                        break
                    except (ConnectionRefusedError, FileNotFoundError):
                        time.sleep(0.01)
        else:
            cfg = None
        if get_process:
            yield p
        else:
            yield cfg
    finally:
        p.stdout.close()
        try:
            os.kill(p.pid, 10)
            try:
                p.wait(timeout=1)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=1)
        except OSError as error:
            if error.errno != 3:  # No such process
                raise
        if cfg_path:
            os.remove(cfg_path)


def test(**new_config):
    def wraps(funct):
        def f(*args, **kwargs):
            with lauch(new_config) as cfg:
                kwargs["cfg"] = cfg
                ret = funct(*args, **kwargs)
            return ret
        return f
    return wraps
