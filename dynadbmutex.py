import logging
import json
import time
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from dynadbobjectstore import ObjectStore


log = logging.getLogger(__name__)


class MutexException(Exception):
    pass

class MutexAlreadyAcquiredException(MutexException):
    pass

class InvalidParameterException(MutexException):
    pass


class MutexBag(object):

    def __init__(self, aws_conn, table_name):
        if not aws_conn or '.DynamoDBConnection' not in str(type(aws_conn)):
            raise InvalidParameterException("Expecting an instance of boto DynamoDB connection")
        if not table_name:
            raise InvalidParameterException("Expecting a table name")
        self.aws_conn = aws_conn
        self.table_name = table_name
        self.store = None

    def _init_store(self):
        if not self.store:
            self.store = ObjectStore(self.aws_conn, self.table_name)

    def create_table(self):
        """Create the DynamoDB table used by this MutexBag, only if it does not
        already exists.
        """
        self._init_store()
        self.store.create_table()

    def acquire(self, name):
        """Try acquiring a lock on a mutex with this name. Either returns a Mutex instance
        that will need to be freed later on, or a MutexAlreadyAcquiredException."""

        self._init_store()

        log.debug("Trying to acquire mutex lock with name '%s'" % (name))
        try:
            self.store.put(
                'mutex-%s' % name,
                {
                    "timestamp": "%.20f" % time.time(),
                },
                overwrite=False
            )
        except ConditionalCheckFailedException as e:
            log.debug("Failed to acquire lock on mutex '%s'" % (name))
            raise MutexAlreadyAcquiredException()

        return Mutex(self, 'mutex-%s' % name)

    def _release(self, name):
        log.debug("Releasing lock on mutex %s" % name)
        self._init_store()
        self.store.delete(name)


class Mutex(object):

    def __init__(self, bag, name):
        assert bag
        assert name
        self.name = name
        self.bag = bag

    def release(self):
        """Release the mutex."""
        self.bag._release(self.name)
