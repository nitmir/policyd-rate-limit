Policyd rate limit
==================


.. image:: https://img.shields.io/pypi/v/policyd-rate-limit.svg
    :target: https://pypi.python.org/pypi/policyd-rate-limit

.. image:: https://img.shields.io/pypi/l/policyd-rate-limit.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.html

Postfix policyd server allowing to limit the number of mails accepted by
postfix over several time periods, by sasl usernames and/or ip addresses.


Installation
------------

First, create the user that will run the daemon and its home directory::

    mkdir -p /var/lib/policyd-rate-limit
    useradd policyd-rate-limit -d /var/lib/policyd-rate-limit

Depending of the backend storage you planning to use, you may need to install additional packages.
(The default settings use the sqlite3 bakends and do not need extra packages).

* `mysqldb <https://github.com/PyMySQL/mysqlclient-python>`_
  (``sudo apt-get install python3-mysqldb`` on debian like systems) for the mysql backend.
* `psycopg2 <https://pypi.python.org/pypi/psycopg2>`_
  (``sudo apt-get install python3-psycopg2`` on debian like systems) fot the postgreysql backend

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

You should run ``policyd-rate-limit --clean`` on a regular basis to delete old records from the
database. It could be wise to put it in a daily cron, for example::

    0 0 * * * policyd-rate-limit /usr/local/bin/policyd-rate-limit --clean >/dev/null

Settings
--------

``policyd-rate-limit`` search for its config first in ``~/.config/policyd-rate-limit.conf``
If not found, then in ``/etc/policyd-rate-limit.conf``, and if not found use the default config.

* ``debug``: make ``policyd-rate-limit`` output logs to stderr.
  The default is True.
* ``user``: The user ``policyd-rate-limit`` will use to drop privileges.
  The default is ``"policyd-rate-limit"``.
* ``group``: The group ``policyd-rate-limit`` will use to drop privileges.
  The defaut is ``"policyd-rate-limit"``.
* ``pidfile``: path where the program will try to write its pid to.
  The default is ``"/var/run/policyd-rate-limit/policyd-rate-limit.pid"``.
  ``policyd-rate-limit`` will try to create the parent directory and chown it if it do not exists.
* ``mysql_config``: The config to connect to a mysql server
* ``pgsql_config``: The config to connect to a postgreysql server
* ``sqlite_config``: The config to connect to a sqlite3 database.
* ``backend``: Which data backend to use. Possible values are ``0`` for sqlite3, ``1`` for mysql
  and ``2`` for postgreysql. The default is ``0``, use the sqlite3 backend.
* ``SOCKET``: The socket to bind to. Can be a path to an unix socket or a couple (ip, port).
  The default is ``"/var/spool/postfix/ratelimit/policy"``.
  ``policyd-rate-limit`` will try to create the parent directory and chown it if it do not exists.
* ``socket_permission``: Permissions on the unix socket (if unix socket used).
  The default is ``0o666``.
* ``limits``: A list of couple (number of emails, number of seconds). If one of the element of the
  list is exeeded (more than 'number of emails' on 'number of seconds' for an ip address or an sasl
  username), postfix will return a temporary failure.
* ``limit_by_sasl``: Apply limits by sasl usernames. The default is ``True``.
* ``limit_by_ip``: Apply limits by ip addresses. The default is ``False``.
* ``limited_netword``: A list of ip networks in cidr notation on which limits are applied. An empty
  list is equal to ``limit_by_ip = False``, put ``"0.0.0.0/0"`` and ``::/0`` for every ip addresses.
* ``success_action``: If not limits are reach, which action postfix should do. The default is
  ``"dunno"``. See http://www.postfix.org/access.5.html for possible actions.
* ``fail_action``: If a limit is reach, which action postfix should do. The default is
  ``"defer_if_permit Rate limit reach, retry later"``.
  See http://www.postfix.org/access.5.html for possible actions.
* ``config_file``: This parameter is automatically set to the path of the configuration file
  currently in use. You can call it conjunction with **--get-config** to known which configuration
  file is used.


* ``report``: if ``True``, send a report to ``report_to`` about users reaching limits each time
  --clean is called. The default is ``False``.
* ``report_from``: From who to send emails reports. It must be defined when ``report`` is ``True``.
* ``report_to``: Address to send emails reports to. It must be defined when ``report`` is ``True``.
* ``report_subject``: Subject of the report email. The default is ``"policyd-rate-limit report"``.
* ``report_limits``: List of number of seconds from the limits list for which you want to be reported.
  The default is ``[86400]``.


* ``smtp_server``: The smtp server to use to send emails ``("host", port)``.
  The default is ``("localhost", 25)``.
* ``smtp_starttls``: Should we use starttls to send mails ? (you should set this to ``True`` if
  you use ``smtp_credentials``). The default is ``False``.
* ``smtp_credentials``: Should we use credentials to connect to smtp_server ?
  if yes set ``("user", "password")``, else ``None``. The default is ``None``.


Postfix settings
----------------

/etc/postfix/main.cf::

    smtpd_recipient_restrictions =
        ...,
        check_policy_service {unix:ratelimit/policy, default_action=DUNNO},
        ...
