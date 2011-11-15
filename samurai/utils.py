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
    return datetime.datetime.strptime(date_str,  "%Y-%m-%dT%H:%M:%SZ")

def str_to_boolean(bool_str):
    if bool_str.lower() != 'false' and bool(bool_str):
        return True
    return False

def is_xml_el_dict(el):
    """
    Returns true if `el` is supposed to be a dict.
    This function makes sense only in the context of making dicts out of xml.
    """
    if len(el) == 1  or el[0].tag != el[1].tag:
        return True
    return False

def is_xml_el_list(el):
    """
    Returns true if `el` is supposed to be a list.
    This function makes sense only in the context of making lists out of xml.
    """
    if len(el) > 1 and el[0].tag == el[1].tag:
        return True
    return False

def process_xml_el(el):
    """
    Extracts value of xml element element `el`.
    """
    val = None
    # Parent node?
    if el:
        if is_xml_el_dict(el):
            val = dict_from_xml(el)
        elif is_xml_el_list(el):
            val = list_from_xml(el)
    else:
        attribs = el.items()
        # An element with no subelements but text.
        if el.text:
            val = val_and_maybe_convert(el)
        # An element with attributes.
        elif attribs:
            val = dict(attribs)
    return val

def val_and_maybe_convert(el):
    """
    Converts `el.text` if `el` has attribute `type` with valid value.
    """
    text = el.text.strip()
    data_type = el.get('type')
    convertor = val_and_maybe_convert.convertors.get(data_type)
    if convertor:
        return convertor(text)
    else:
        return text
val_and_maybe_convert.convertors = {
    'boolean': str_to_boolean,
    'datetime': str_to_datetime,
    'integer': int
}

def list_from_xml(el_list):
    """
    Converts xml elements list `el_list` to a python list.
    """
    res = []
    append = res.append
    for el in el_list:
        pipe(el, process_xml_el, append)
    return res

def dict_from_xml(root):
    """
    Converts xml doc with root `root` to a python dict.
    """
    # An element with subelements.
    res = {}
    if root:
        for el in root:
            res[el.tag] = process_xml_el(el)
    else:
        res = process_xml_el(root)
    return {root.tag: res}
