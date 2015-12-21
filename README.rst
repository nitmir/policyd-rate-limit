Policyd rate limit
==================


.. image:: https://img.shields.io/pypi/v/policyd-rate-limit.svg
    :target: https://pypi.python.org/pypi/policyd-rate-limit

.. image:: https://img.shields.io/pypi/l/policyd-rate-limit.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.html

Postfix policyd server allowing to limit the number of mail accepted by
postfix over severals time periods, by sasl usernames and/or ip addresses.


Installation
------------

First, create the user that will run the daemon and its home directory::

    mkdir -p /var/lib/policyd-rate-limit
    useradd policyd-rate-limit -d /var/lib/policyd-rate-limit

Install with pip::

    sudo pip3 install policyd-rate-limit

or from source code::

    sudo make install

This will install the ``policyd_rate_limit`` module, the ``policyd-rate-limit`` binary,
copy the default config to ``/etc/policyd-rate-limit.conf`` if the file do not exists,
copy an init script to ``/etc/init.d/policyd-rate-limit`` and an unit file to
``/etc/systemd/system/policyd-rate-limit.service``.

After the installation, you may need to run ``sudo systemctl daemon-reload`` for make the unit
file visible by systemd.

You should ran ``policyd-rate-limit --clean`` on a regular basis to delete old records from the
database. It could be wise to put it in a daily cron, for example::

    0 0 * * * policyd-rate-limit /usr/local/bin/policyd-rate-limit --clean >/dev/null

Settings
--------

``policyd-rate-limit`` search for its config first in ``~/.config/policyd-rate-limit.conf``
If not found, then in ``/etc/policyd-rate-limit.conf``, and if not found use the default config.

* ``debug``: make ``policyd-rate-limit`` output to stderr all of its exanges with postfix.
  The default is True.
* ``mysql_config``: The config to connect to a mysql server
* ``pgsql_config``: The config to connect to a postgreysql server
* ``sqlite_config``: The config to connect to a sqlite3 database.
* ``backend``: Which data backend to use. Possible values are ``0`` for sqlite3, ``1`` for mysql
  and ``2`` for postgreysql. The default is ``0``, use the sqlite3 backend.
* ``SOCKET``: The socket to bind to. Can be a path to an unix socket or a couple (ip, port).
  The default is ``"/var/spool/postfix/ratelimit/policy"``
* ``socket_permission``: Permissions on the unix socket (if unix socket used).
  The default is ``0o666``.
* ``limits``: A list of couple (number of emails, number of seconds). If one of the element of the
  list is exeeded (more than 'number of emails' on 'number of seconds' for an ip address or an sasl
  username), postfix will return a temporary failure.
* ``limit_by_sasl``: Apply limits by sasl usernames. The default is ``True``.
* ``limit_by_ip``: Apply limits by ip addresses. The default is ``False``.
* ``limited_netword``: A list of ip networks in cidr notation on which limits are applied. An empty
  list is equal to ``limit_by_ip = False``, put ``"0.0.0.0/0"`` and ``::/0`` for every ip addresses.




Postfix settings
----------------

/etc/postfix/main.cf::

    smtpd_recipient_restrictions =
        ...
        check_policy_service unix:ratelimit/policy
        ...
