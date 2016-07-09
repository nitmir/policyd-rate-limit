=======================
policyd-rate-limit.conf
=======================

-------------------------------------------
policyd-rate-limit configuration parameters
-------------------------------------------

:Author: Valentin Samir <valentin.samir@crans.org>
:Date: 2016-07-09
:Copyright: GPL-3
:Version: 3.8
:title_upper: policyd-rate-limit.conf
:Manual section: 5
:Manual group: policyd-rate-limit


Description
===========

**policyd-rate-limit**)(8) uses a **python**)(1) style configuration file which is reads on startup.
If the **--file** option if not set, it searches for configuration files on the following paths::

  ~/.config/policyd-rate-limit.conf
  /etc/policyd-rate-limit.conf

and exits if not found.


Settings
========

**debug**
  Make policyd-rate-limit output logs to stderr. The default is True.
**user**
  The user policyd-rate-limit will use to drop privileges. The default is "policyd-rate-limit".
**group**
  The group policyd-rate-limit will use to drop privileges. The default is "policyd-rate-limit".
**pidfile**
  path where the program will try to write its pid to. The default is
  "/var/run/policyd-rate-limit/policyd-rate-limit.pid". policyd-rate-limit will try to create
  the parent directory and chown it if it do not exists.
**mysql_config**
  The configuration to connect to a mysql server. It should be a dictionary of parameters to give
  to the MySQLdb.connect function. See the python3-mysqldb documentations.
**pgsql_config**
  The configuration to connect to a postgreysql server. It should be a dictionary of parameters to give
  to the psycopg2.connect function. See the python3-psycopg2 documentations.
**sqlite_config**
  The configuration to connect to a sqlite3 database. It should be a dictionary of parameters to give
  to the sqlite3.connect function. See the python3 documentations.
**backend**
  Which data backend to use. Possible values are 0 for sqlite3, 1 for mysql and 2 for postgreysql.
  The default is 0, use the sqlite3 backend.
**SOCKET**
  The socket to bind to. Can be a path to an unix socket or a couple (ip, port). The default is
  "/var/spool/postfix/ratelimit/policy". policyd-rate-limit will try to create the parent
  directory and chown it if it do not exists.
**socket_permission**
  Permissions on the unix socket (if unix socket used). The default is 0o666.
**limits**
  A list of couple (number of emails, number of seconds). If one of the element of the list is
  exceeded (more than 'number of emails' on 'number of seconds' for an ip address or an sasl
  username), postfix will return a temporary failure.
**limit_by_sasl**
  Apply limits by sasl usernames. The default is True.
**limit_by_ip**
  Apply limits by ip addresses. The default is False.
**limited_netword**
  A list of ip networks in cidr notation on which limits are applied. An empty list is equal to
  limit_by_ip = False, put "0.0.0.0/0" and ::/0 for every ip addresses.
**success_action**
  If no limits are reach, which action postfix should do. The default is "dunno". See **access**)(5)
  for possible actions.
**fail_action**
  If a limit is reach, which action postfix should do.
  The default is "defer_if_permit Rate limit reach, retry later".
  See **access**)(5) for possible actions.

See also
========

| **policyd-rate-limit**)(8)
