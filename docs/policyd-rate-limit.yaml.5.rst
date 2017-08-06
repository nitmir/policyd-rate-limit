=======================
policyd-rate-limit.yaml
=======================

-------------------------------------------
policyd-rate-limit configuration parameters
-------------------------------------------

:Author: Valentin Samir <valentin.samir@crans.org>
:Date: 2016-08-04
:Copyright: GPL-3
:Version: 3.8
:title_upper: policyd-rate-limit.yaml
:Manual section: 5
:Manual group: policyd-rate-limit


Description
===========

**policyd-rate-limit**)(8) was using a **python**)(1) style configuration file and not use a
**yaml**)(3pm) file which is reads on startup. .conf files are the old python format confguration
files and .yaml the new ones. Old style configuration files are deprecated and should not be used.

If the **--file** option if not set, it searches for configuration files on the following paths::

  ~/.config/policyd-rate-limit.conf
  ~/.config/policyd-rate-limit.yaml
  /etc/policyd-rate-limit.conf
  /etc/policyd-rate-limit.yaml

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
  The configuration to connect to a postgresql server. It should be a dictionary of parameters to give
  to the psycopg2.connect function. See the python3-psycopg2 documentations.
**sqlite_config**
  The configuration to connect to a sqlite3 database. It should be a dictionary of parameters to give
  to the sqlite3.connect function. See the python3 documentations.
**backend**
  Which data backend to use. Possible values are 0 for sqlite3, 1 for mysql and 2 for postgresql.
  The default is 0, use the sqlite3 backend.
**SOCKET**
  The socket to bind to. Can be a path to an unix socket or a couple [ip, port]. The default is
  "/var/spool/postfix/ratelimit/policy". policyd-rate-limit will try to create the parent
  directory and chown it if it do not exists.
**socket_permission**
  Permissions on the unix socket (if unix socket used). The default is 0o666.
**limits**
  A list of couple [number of emails, number of seconds]. If one of the element of the list is
  exceeded (more than 'number of emails' on 'number of seconds' for an ip address or an sasl
  username), postfix will return a temporary failure.
**limits_by_id**
  A dictionary of id -> limit list (see limits). Used to override limits and use custom limits for
  a particular id. Use an empty list for no limits for a particular id. Ids are sasl usernames or
  ip addresses. The default is {}.
**limit_by_sasl**
  Apply limits by sasl usernames. The default is True.
**limit_by_sender**
  Apply limits by sender addresses if sasl username is not found. The defaut is ``False``.
**limit_by_ip**
  Apply limits by ip addresses if sasl username is not found. The default is False.
**limited_networks**
  A list of ip networks in cidr notation on which limits are applied. An empty list is equal to
  limit_by_ip = False, put "0.0.0.0/0" and ::/0 for every ip addresses.
**success_action**
  If no limits are reach, which action postfix should do. The default is "dunno". See **access**)(5)
  for possible actions.
**fail_action**
  If a limit is reach, which action postfix should do.
  The default is "defer_if_permit Rate limit reach, retry later".
  See **access**)(5) for possible actions.
**db_error_action**
  If we are unable to to contect the database backend, which action postfix should do.
  The default is "dunno".
  See **access**)(5) for possible actions.
**config_file**
  This parameter is automatically set to the path of the configuration file currently in use.
  You can call it in conjunction with **--get-config** to known which configuration file is used.


**report**
  if True, send a report to **report_to** about users reaching limits each time
  --clean is called. The default is False.
**report_from**
  From who to send emails reports. It must be defined when **report** is True.
**report_to**
  Address to send emails reports to. It must be defined when **report** is True.
**report_subject**
  Subject of the report email. The default is "policyd-rate-limit report".
**report_limits**
  List of number of seconds from the limits list for which you want to be reported.
  The default is [86400].
**report_only_if_needed**
  Only send a report if some users have reach a reported limit. The default is True.


**smtp_server**
  The smtp server to use to send emails ["host", port].
  The default is ["localhost", 25].
**smtp_starttls**
  Should we use starttls to send mails ? (you should set this to True if
  you use **smtp_credentials**). The default is False.
**smtp_credentials**
  Should we use credentials to connect to smtp_server ?
  if yes set ["user", "password"], else null. The default is null.


See also
========

| **policyd-rate-limit**)(8)
