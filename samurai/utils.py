"""
    General utilities
    ~~~~~~~~~~~~~~~~~~
"""
import datetime

def pipe(cur_val, *fns):
    """
    Pipes `cur_val` through `fns`.
    ::
        def sqr(x): return x * x

        def negate(x): return -x

        `pipe(5, sqr, negate)`

    is the same as
    ::
        negate(sqr(5))
    """
    for fn in fns:
        cur_val = fn(cur_val)
    return cur_val

def str_to_datetime(date_str):
    try:
        val = datetime.datetime.strptime(date_str,  "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        val = date_str
    return val

def str_to_boolean(bool_str):
    if bool_str.lower() != 'false' and bool(bool_str):
        return True
    return False

def is_error(dict_data):
    """
    Returns true if returned Samurai result `dict_data` erred.
    """
    # Top level error.
    if dict_data.get('error'):
        return True
    # Error in a response block.
    if dict_data.get('messages') and dict_data['messages'].get('message') and \
        any(True for m in dict_data['messages']['message'] if m['class'] == 'error'):
        return True
    # No errors.
    return False
