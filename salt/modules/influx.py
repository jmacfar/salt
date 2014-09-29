# -*- coding: utf-8 -*-
'''
InfluxDB - A distributed time series database

Module to provide InfluxDB compatibility to Salt
(compatible with InfluxDB version 0.5+)

.. versionadded:: 2014.7.0

:depends:    - influxdb Python module

:configuration: This module accepts connection configuration details either as
    parameters or as configuration settings in /etc/salt/minion on the relevant
    minions::

        influxdb.host: 'localhost'
        influxdb.port: 8086
        influxdb.user: 'root'
        influxdb.password: 'root'

    This data can also be passed into pillar. Options passed into opts will
    overwrite options passed into pillar.
'''
try:
    import influxdb
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False

import logging

log = logging.getLogger(__name__)


# Define the module's virtual name
__virtualname__ = 'influxdb'


def __virtual__():
    '''
    Only load if influxdb lib is present
    '''
    if HAS_INFLUXDB:
        return __virtualname__
    return False


def _client(user=None, password=None, host=None, port=None):
    if not user:
        user = __salt__['config.option']('influxdb.user', 'root')
    if not password:
        password = __salt__['config.option']('influxdb.password', 'root')
    if not host:
        host = __salt__['config.option']('influxdb.host', 'localhost')
    if not port:
        port = __salt__['config.option']('influxdb.port', 8086)
    return influxdb.InfluxDBClient(
        host=host, port=port, username=user, password=password)


def db_list(user=None, password=None, host=None, port=None):
    """
    List all InfluxDB databases

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.db_list
        salt '*' influxdb.db_list <user> <password> <host> <port>

    """
    client = _client(user=user, password=password, host=host, port=port)
    return client.get_database_list()


def db_exists(name, user=None, password=None, host=None, port=None):
    '''
    Checks if a database exists in InfluxDB

    name
        Database name to create

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.db_exists <name>
        salt '*' influxdb.db_exists <name> <user> <password> <host> <port>
    '''
    dbs = db_list(user, password, host, port)
    if not isinstance(dbs, list):
        return False
    return name in [db['name'] for db in dbs]


def db_create(name, user=None, password=None, host=None, port=None):
    """
    Create a database

    name
        Database name to create

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.db_create <name>
        salt '*' influxdb.db_create <name> <user> <password> <host> <port>
    """
    if db_exists(name):
        log.info('DB {0!r} already exists'.format(name))
        return False
    client = _client(user=user, password=password, host=host, port=port)
    return client.create_database(name)


def db_remove(name, user=None, password=None, host=None, port=None):
    """
    Remove a database

    name
        Database name to remove

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.db_remove <name>
        salt '*' influxdb.db_remove <name> <user> <password> <host> <port>
    """
    if not db_exists(name):
        log.info('DB {0!r} does not exist'.format(name))
        return False
    client = _client(user=user, password=password, host=host, port=port)
    return client.delete_database(name)


def user_list(database=None, user=None, password=None, host=None, port=None):
    """
    List cluster admins or database users.

    If a database is specified: it will return database users list.
    If a database is not specified: it will return cluster admins list.

    database
        The database to list the users from

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.user_list
        salt '*' influxdb.user_list <database>
        salt '*' influxdb.user_list <database> <user> <password> <host> <port>
    """
    client = _client(user=user, password=password, host=host, port=port)
    if database:
        client.switch_db(database)
        return client.get_database_users()
    return client.get_list_cluster_admins()


def user_exists(
        name, database=None, user=None, password=None, host=None, port=None):
    '''
    Checks if a cluster admin or database user exists.

    If a database is specified: it will check for database user existence.
    If a database is not specified: it will check for cluster admin existence.

    name
        User name

    database
        The database to check for the user to exist

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.user_exists <name>
        salt '*' influxdb.user_exists <name> <database>
        salt '*' influxdb.user_exists <name> <database> <user> <password> <host> <port>
    '''
    users = user_list(database, user, password, host, port)
    if not isinstance(users, list):
        return False
    return name in [u['name'] for u in users]


def user_create(name, passwd, database=None, user=None, password=None,
                host=None, port=None):
    """
    Create a cluster admin or a database user.

    If a database is specified: it will create database user.
    If a database is not specified: it will create a cluster admin.

    name
        User name for the new user to create

    passwd
        Password for the new user to create

    database
        The database to create the user in

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.user_create <name> <passwd>
        salt '*' influxdb.user_create <name> <passwd> <database>
        salt '*' influxdb.user_create <name> <passwd> <database> <user> <password> <host> <port>
    """
    if user_exists(name, database):
        if database:
            log.info('User {0!r} already exists for DB {0!r}'.format(
                name, database))
        else:
            log.info('Cluster admin {0!r} already exists'.format(name))
        return False
    client = _client(user=user, password=password, host=host, port=port)
    if database:
        client.switch_db(database)
        return client.add_database_user(name, passwd)
    return client.add_cluster_admin(name, passwd)


def user_chpass(name, passwd, database=None, user=None, password=None,
                host=None, port=None):
    """
    Change password for a cluster admin or a database user.

    If a database is specified: it will update database user password.
    If a database is not specified: it will update cluster admin password.

    name
        User name for whom to change the password

    passwd
        New password

    database
        The database on which to operate

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.user_chpass <name> <passwd>
        salt '*' influxdb.user_chpass <name> <passwd> <database>
        salt '*' influxdb.user_chpass <name> <passwd> <database> <user> <password> <host> <port>
    """
    if not user_exists(name, database):
        if database:
            log.info('User {0!r} does not exist for DB {0!r}'.format(
                name, database))
        else:
            log.info('Cluster admin {0!r} does not exist'.format(name))
        return False
    client = _client(user=user, password=password, host=host, port=port)
    if database:
        client.switch_db(database)
        return client.update_database_user_password(name, passwd)
    return client.update_cluster_admin_password(name, passwd)


def user_remove(name, database=None, user=None, password=None, host=None,
                port=None):
    """
    Remove a cluster admin or a database user.

    If a database is specified: it will remove the database user.
    If a database is not specified: it will remove the cluster admin.

    name
        User name to remove

    database
        The database to remove the user from

    user
        User name for the new user to delete

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.user_remove <name>
        salt '*' influxdb.user_remove <name> <database>
        salt '*' influxdb.user_remove <name> <database> <user> <password> <host> <port>
    """
    if not user_exists(name, database):
        if database:
            log.info('User {0!r} does not exist for DB {0!r}'.format(
                name, database))
        else:
            log.info('Cluster admin {0!r} does not exist'.format(name))
        return False
    client = _client(user=user, password=password, host=host, port=port)
    if database:
        client.switch_db(database)
        return client.delete_database_user(user)
    return client.delete_cluster_admin(user)


def query(database, query, time_precision='s', chunked=False, user=None,
          password=None, host=None, port=None):
    """
    Querying data

    database
        The database to query

    query
        Query to be executed

    time_precision
        Time precision to use ('s', 'm', or 'u')

    chunked
        Whether is chunked or not

    user
        The user to connect as

    password
        The password of the user

    host
        The host to connect to

    port
        The port to connect to

    CLI Example:

    .. code-block:: bash

        salt '*' influxdb.query <database> <query>
        salt '*' influxdb.query <database> <query> <time_precision> <chunked> <user> <password> <host> <port>
    """
    client = _client(user=user, password=password, host=host, port=port)
    client.switch_db(database)
    return client.query(query, time_precision=time_precision, chunked=chunked)
