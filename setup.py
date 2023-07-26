#!/usr/bin/env python3
from setuptools import setup

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
    add_data_file("/etc", 'policyd_rate_limit/policyd-rate-limit.yaml')
    add_data_file('/etc/init.d', 'init/policyd-rate-limit')
    add_data_file(
        "/etc/systemd/system",
        'init/policyd-rate-limit.service',
        check_dir=True
    )
# else use user .config dir
else:
    conf_dir = os.path.expanduser("~/.config/")
    add_data_file(conf_dir, 'policyd_rate_limit/policyd-rate-limit.yaml', mkdir=True)


setup(
    name='policyd-rate-limit',
    version='1.1.0',
    description=DESC,
    long_description=README,
    author='Valentin Samir',
    author_email='valentin.samir@crans.org',
    license='GPLv3',
    url='https://github.com/nitmir/policyd-rate-limit',
    download_url="https://github.com/nitmir/policyd-rate-limit/releases/latest",
    packages=['policyd_rate_limit', 'policyd_rate_limit.tests'],
    package_data={
        'policyd_rate_limit': [
            'policyd-rate-limit.conf',
            'policyd-rate-limit.yaml',
        ]
    },
    keywords=['Postfix', 'rate', 'limit', 'email'],
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
    install_requires=["PyYAML >= 3.11"],
    zip_safe=False,
)
