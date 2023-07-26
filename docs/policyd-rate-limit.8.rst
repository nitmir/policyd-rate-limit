==================
policyd-rate-limit
==================

-------------------------------
rate limiter SMTP policy daemon
-------------------------------

:Author: Valentin Samir <valentin.samir@crans.org>
:Date: 2016-08-04
:Copyright: GPL-3
:Version: 3.8
:title_upper: policyd-rate-limit
:Manual section: 8
:Manual group: policyd-rate-limit


Synopsis
========

**policyd-rate-limit** [**-h**] [**--clean**] [**--get-config** *configname*] [**--file** *configpath*]


Description
===========

**policyd-rate-limit**)(8) is a SMTP policy daemon written in **python3**)(1) for **postfix**)(1).
It keep track of the number of mails sent by sasl usernames and/or ip addresses over time 
sliding window. A configurable action (see **access**)(5)) is done then a user and/or ip
address exceeds one or more configurable limits.


Setup
=====

For example, for postfix 3.0 and later, you can set in postfix **/etc/postfix/main.cf**
configuration file::

  smtpd_data_restrictions =
    ...,
    check_policy_service { unix:ratelimit/policy, default_action=DUNNO },
    ...

Postfix will ask policyd-rate-limit what to do on mail reception (success or fail action)
and will accept mail if policyd-rate-limit become unavailable.


On previous postfix versions, you must use::

  smtpd_data_restrictions =
    ...,
    check_policy_service unix:ratelimit/policy,
    ...


Options
=======

  **-h**, **--help**
    show this help message and exit

  **--clean**
    clean old records from the database

  **--get-config** *configname*
    return the value of the *configname* configuration parameter. You can get a value in a dictionary
    by using a dotted notation. For instance, for getting the key KEY in the dictionary DICT,
    you should use DICT.KEY for *configname*. You can call the configuration parameter *config_file*
    to known which configuration file is used.

  **-f**, **--file**
    path to a policyd-rate-limit configuration file


Logging
=======

Logging is output to stderr and redirected to **syslog**)(3) by systemd.
Logs are produced only if the **debug** configuration parameter is set to True.


Configuration
=============

If the option **--file** is not specified, **policyd-rate-limit**)(8) try to read its configuration
from the following path and choose the first existing file::

  ~/.config/policyd-rate-limit.conf
  ~/.config/policyd-rate-limit.yaml
  /etc/policyd-rate-limit.conf
  /etc/policyd-rate-limit.yaml

The .conf are the old configuration format. It was a python module and should not be used.
The .yaml are the new configuration format using the YAML syntax. See YAML(3pm) for an overview of
the format.
See **policyd-rate-limit.yaml**)(5) for possible settings.


Exit values
===========

  **0**   Normal exit.

  **1**   Only return then the option **--get-config** is used. Configuration parameter not found.

  **2**   User or group set in the configuration file do not exists.

  **3**   Another instance is already running

  **4**   The configuration parameter SOCKET is malformed

  **5**   Configuration file not found

  **6**   Some error was raised during runtime

  **8**   Error during cleaning

See also
========

| **policyd-rate-limit.yaml**)(5): policyd-rate-limit configuration file
| **master**)(5), Postfix master.cf file syntax
| **access**)(5), Postfix SMTP access control table
