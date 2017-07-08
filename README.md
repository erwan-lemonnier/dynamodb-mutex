# dynamodbmutex

A super-simple mutex implementation on top of DynamoDB.

Dynadbmutex uses
[dynadbobjectstore](https://github.com/erwan-lemonnier/dynamodbobjectstore) to
acquire/release an entry in a DynamoDB table. That entry is uniquely identified
by its name string. If no such entry exists, the acquiring process may create
it and thereby gets the mutex. Any other process trying to acquire the same
name afterwards gets an exception.

This mutex implementation does not implement any timeout/expiry mechanism: the
acquiring process is solely responsible for releasing the mutex when done.

This implementation relies on DynamoDB's support for [conditional
writes](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.Modifying.html#Expressions.Modifying.ConditionalWrites).

A good discussion on the pros and cons of using DynamoDB for locking can be
found at
[https://r.32k.io/locking-with-dynamodb](https://r.32k.io/locking-with-dynamodb).

## Installing

```
pip install dynadbmutex
```

## Synopsis

```
from boto import dynamodb2
from dynadbmutex import MutexBag, MutexAlreadyAcquiredException

aws_conn = dynamodb2.connect_to_region(...)

# Initialize a mutex bag in a DynamoDB table named 'some_table_name'
bag = MutexBag(
    aws_conn,
    'some_table_name'
)

# Create the table if needed
bag.create_table()

# Get a mutex
try:
    # If multiple processes want to acquire the same string 'name', only one
    # will succeed, and all others get a MutexAlreadyAcquiredException.
    mutex = bag.acquire(name)

except MutexAlreadyAcquiredException as e:
    # Too bad, someone else already acquired this mutex
    return

# Bingo! You got the mutex :-)

do_my_stuff()

# When done, release that mutex
mutex.release()
```

## Testing

```
# Set the following environment variables:
export AWS_DEFAULT_REGION='eu-west-1'
export AWS_ACCESS_KEY_ID='...'
export AWS_SECRET_ACCESS_KEY='...'

nosetests test.py
```