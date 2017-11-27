from __future__ import absolute_import
from pymapd import connect
from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, ERROR, WARNING, DEBUG, INFO
from threading import Timer
import datetime
import pymapd

connection_attrs = {
    'user': 'mapd',
    'password': 'HyperInteractive',
    'host': 'localhost',
    'port': '9091',
    'dbname': 'mapd',
}

translate_qual_operator = {
    '=':            '=',
    '>':            '>',
    '>=':           '>=',
    '<':            '<',
    '<=':           '<=',
    '~~':           'like',
    '~~*':          'ilike',
    '!~~':          'not like',
    '!~~*':         'not ilike',
    ('=', True):    'in',
    ('<>', False):  'not in'
}


class pgFDW_mapd(ForeignDataWrapper):

    def __init__(self, options, columns):
        super(pgFDW_mapd, self).__init__(options, columns)
        for attribute in connection_attrs.keys():
            if attribute not in options:
                log_to_postgres('The ' + attribute + ' parameter should be defined. defaulting to :' +
                                connection_attrs.get(attribute), WARNING)
                setattr(self, attribute, connection_attrs.get(attribute))
            else:
                setattr(self, attribute, options.get(attribute))
        self.connection = connect(user=self.user, password=self.password,
                                  host=self.host, port=self.port, dbname=self.dbname)
        self.idle_timeout = options.get('idle_timeout', 300)
        self.idle_timeout_timer = Timer(
            self.idle_timeout, self.close_connection)
        self.idle_timeout_timer.start()
        self.limit = options.get('limit', 100000)
        self.query = options.get('query', None)
        if self.query != None:
            self.table_name = "(" + options.get('query') + ")"
        else:
            self.table_name = options.get('table_name', None)

    def close_connection(self):
        log_to_postgres(
            "Idle timeout occurred; the Session has been disconnected", INFO)
        self.connection.close()

    def return_formatted_value(self, value):
        if type(value) is str or type(value) is unicode:
            ret_value = "'" + value + "'"
        elif type(value) is datetime.datetime:
            ret_value = "'" + str(value) + "'"
        else:
            ret_value = str(value)
        return ret_value

    def execute(self, quals, columns):
        log_to_postgres(
            "timer ." + str(self.idle_timeout_timer.is_alive), INFO)
        if self.connection is None or self.connection.closed == 1:
            self.connection = connect(
                user=self.user, password=self.password, host=self.host, port=self.port, dbname=self.dbname)
        self.idle_timeout_timer.cancel()
        self.idle_timeout_timer = Timer(
            self.idle_timeout, self.close_connection)
        self.idle_timeout_timer.start()
        statement = u""
        statement = "SELECT {0} from {1}".format(
            ",".join(columns), self.table_name)
        isWhereDefined = False
        for qualifier in quals:
            translated_qo = translate_qual_operator.get(
                qualifier.operator, qualifier.operator)
            if translated_qo == 'not ilike':
                log_to_postgres('The operator ' + translated_qo +
                                ' is not supported on MAPD', ERROR)
                self.connection.close()
                return
            if isWhereDefined is False:
                statement = statement + " WHERE " + qualifier.field_name + \
                    " " + translated_qo
                isWhereDefined = True
            else:
                statement = statement + " AND " + qualifier.field_name + \
                    " " + translated_qo
            if translated_qo == qualifier.operator or translated_qo != 'in':
                statement = statement + " " + \
                    self.return_formatted_value(qualifier.value)
            elif translated_qo == 'in':
                statement = statement + " ( {0} )".format(",".join(
                    [self.return_formatted_value(in_value) for in_value in qualifier.value]))
            if self.limit != -1:
                statement = statement + " limit" + str(self.limit)
        resultSet = self.connection.execute(statement)

        for row in resultSet:
            row_returned = {}
            idx = 0
            for column_name in columns:
                row_returned[column_name] = row[idx]
                idx = idx + 1
            yield row_returned
