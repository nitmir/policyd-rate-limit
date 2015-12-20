#!/usr/bin/env python3
from setuptools import setup

import sys
import os

DESC = """Postfix rate limit policy server implemented in Python3."""
with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()
data_files = []


def add_data_file(dir, file, check_dir=False, mkdir=False):
    path = os.path.join(dir, os.path.basename(file))
    if not os.path.isfile(path):
        if not check_dir or mkdir or os.path.isdir(dir):
            if mkdir:
                try:
                    os.mkdir(dir)
                except OSError:
                    pass
            data_files.append((dir, [file]))

# if install as root populate /etc
if os.getuid() == 0:
    add_data_file("/etc", 'policyd_rate_limit/policyd-rate-limit.conf')
    add_data_file('/etc/init.d', 'policyd_rate_limit/init/policyd-rate-limit')
    add_data_file(
        "/etc/systemd/system",
        'policyd_rate_limit/init/policyd-rate-limit.service',
        check_dir=True
    )
    try:
        os.mkdir("/var/lib/policyd-rate-limit")
    except OSError:
        pass
    try:
        os.mkdir("/var/spool/postfix/ratelimit/")
    except OSError:
        pass
    os.system("useradd policyd-rate-limit -d /var/lib/policyd-rate-limit")
    os.system(
        "chown policyd-rate-limit:policyd-rate-limit "
        "/var/lib/policyd-rate-limit "
        "/var/spool/postfix/ratelimit/"
    )
# else user user .config dir
else:
    conf_dir = os.path.expanduser("~/.config/")
    add_data_file(conf_dir, 'policyd_rate_limit/policyd-rate-limit.conf', mkdir=True)


setup(
    name='policyd-rate-limit',
    version='0.1',
    description=DESC,
    long_description=README,
    author='Valentin Samir',
    author_email='valentin.samir@crans.org',
    # url='https://launchpad.net/pypolicyd-spf',
    packages=['policyd_rate_limit'],
    package_data={
        'policyd_rate_limit': [
            'policyd-rate-limit.conf',
            'init/policyd-rate-limit',
            'init/policyd-rate-limit.service',
        ]
    },
    keywords=['Postfix', 'rate limit', 'email'],
    scripts=['policyd-rate-limit'],
    data_files=data_files,
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Email :: Mail Transport Agents',
        'Topic :: Communications :: Email :: Filters',
    ],
    install_requires=["netaddr >= 0.7"],
    zip_safe=False,
)

if sys.version_info < (2, 6):
    raise Exception("pypolicyd-spf requires python2.6/2.7 or python3.2 and later.")
