import six
import numbers
from decimal import Decimal
from dateutil.tz import tzlocal, tzutc
from datetime import date, datetime, timedelta

from typing import Union
from aiolotus.utils.logs import logger

__all__ = [
    'is_naive',
    'total_seconds',
    'guess_timezone',
    'remove_trailing_slash',
    'clean',
    'require',
    'stringify_id',
]

def is_naive(dt: datetime):
    """Determines if a given datetime.datetime is naive."""
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def total_seconds(delta: timedelta):
    """Determines total seconds with python < 2.7 compat."""
    # http://stackoverflow.com/questions/3694835/python-2-6-5-divide-timedelta-with-timedelta
    return (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 1e6) / 1e6


def guess_timezone(dt: datetime):
    """Attempts to convert a naive datetime to an aware datetime."""
    if is_naive(dt):
        # attempts to guess the datetime.datetime.now() local timezone
        # case, and then defaults to utc
        delta = datetime.now() - dt
        if total_seconds(delta) < 5:
            # this was created using datetime.datetime.now()
            # so we are in the local timezone
            return dt.replace(tzinfo=tzlocal())
        else:
            # at this point, the best we can do is guess UTC
            return dt.replace(tzinfo=tzutc())

    return dt


def remove_trailing_slash(host: str):
    return host[:-1] if host.endswith("/") else host

def _clean_list(list_):
    return [clean(item) for item in list_]

def _clean_dict(dict_):
    data = {}
    for k, v in six.iteritems(dict_):
        try:
            data[k] = clean(v)
        except TypeError:
            logger.warning(
                f'Dictionary values must be serializeable to JSON "{k}" value {v} of type {type(v)} is unsupported.',
            )
    return data

def _coerce_unicode(cmplx: Union[bytes, str]):
    try:
        item = cmplx.decode("utf-8", "strict")
    except AttributeError as exception:
        item = ":".join(exception)
        item.decode("utf-8", "strict")
        logger.warning("Error decoding: %s", item)
        return None
    return item

def clean(item):
    if isinstance(item, Decimal):
        return float(item)
    elif isinstance(
        item, (six.string_types, bool, numbers.Number, datetime, date, type(None))
    ):
        return item
    elif isinstance(item, (set, list, tuple)):
        return _clean_list(item)
    elif isinstance(item, dict):
        return _clean_dict(item)
    else:
        return _coerce_unicode(item)


def require(name, field, data_type):
    """Require that the named `field` has the right `data_type`"""
    if not isinstance(field, data_type):
        msg = f"{name} must have {data_type}, got: {field}"
        raise AssertionError(msg)


def stringify_id(val):
    if val is None:
        return None
    return val if isinstance(val, six.string_types) else str(val)

