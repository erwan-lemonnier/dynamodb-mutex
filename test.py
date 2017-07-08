#!/usr/bin/env python

# Illustrate using dynadbmutex for acquiring/releasing a mutex lock
#
# Assuming you set the following environment variables:
# * AWS_DEFAULT_REGION: your aws region (ex: eu-west-1)
# * AWS_ACCESS_KEY_ID: your aws access key
# * AWS_SECRET_ACCESS_KEY: your aws secret key


import os
import sys
import json
import logging
from unittest import TestCase
from boto import dynamodb2
from boto.dynamodb2.exceptions import ItemNotFound
from dynadbmutex import MutexBag, Mutex, MutexAlreadyAcquiredException

# Setup logging
log = logging.getLogger(__name__)
root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(levelname)s %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
logging.getLogger('boto').setLevel(logging.INFO)


class Test(TestCase):

    def setUp(self):

        for k in ('AWS_DEFAULT_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'):
            if k not in os.environ:
                return

        conn = dynamodb2.connect_to_region(
            os.environ['AWS_DEFAULT_REGION'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
        )

        # Create both dynamodb table and ObjectStore
        self.bag = MutexBag(conn, 'objectstore-test-table--delete-at-will')
        self.bag.create_table()
        self.bag._release('mutex-foobar')


    def test_acquire_multiple_times(self):

        if not hasattr(self, 'bag'):
            return

        # Acquire mutex
        m = self.bag.acquire('foobar')
        self.assertTrue(isinstance(m, Mutex))

        # Acquire it again: fail
        try:
            self.bag.acquire('foobar')
        except Exception as e:
            self.assertTrue(isinstance(e, MutexAlreadyAcquiredException))
        else:
            self.assertTrue(0, 'wanted a MutexAlreadyAcquiredException')

        # Release it
        m.release()

        # Acquire again: success
        m = self.bag.acquire('foobar')
        self.assertTrue(isinstance(m, Mutex))
