"""
Methods to work with XML.
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from utils import str_to_datetime, str_to_boolean

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

def from_xml(el):
    """
    Extracts value of xml element element `el`.
    """
    # Parent node.
    if el:
        if is_xml_el_dict(el):
            val = {el.tag: dict_from_xml(el)}
        elif is_xml_el_list(el):
            val = list_from_xml(el)
    # Simple node.
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

def list_from_xml(els):
    """
    Converts xml elements list `el_list` to a python list.
    """
    res = []
    for el in els:
        res.append(from_xml(el))
    return res

def dict_from_xml(els):
    """
    Converts xml doc with root `root` to a python dict.
    """
    # An element with subelements.
    res = {}
    for el in els:
        res[el.tag] = from_xml(el)
    return res
