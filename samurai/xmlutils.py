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

def xml_to_dict(root_or_str):
    """
    Converts `root_or_str` which can be parsed xml or a xml string to dict.
    """
    root = root_or_str
    if isinstance(root, str):
        import xml.etree.cElementTree as ElementTree
        root = ElementTree.XML(root_or_str)
    return {root.tag: from_xml(root)}

def from_xml(el):
    """
    Extracts value of xml element element `el`.

    >>> test = '''
    ... <payment_method>
    ...   <payment_method_token>QhLaMNNpvHwfnFbHbUYhNxadx4C</payment_method_token>
    ...   <created_at type="datetime">2011-02-12T20:20:46Z</created_at>
    ...   <updated_at type="datetime">2011-04-22T17:57:30Z</updated_at>
    ...   <custom>Any value you want us to save with this payment method.</custom>
    ...   <is_retained type="boolean">true</is_retained>
    ...   <is_redacted type="boolean">false</is_redacted>
    ...   <is_sensitive_data_valid type="boolean">false</is_sensitive_data_valid>
    ...   <messages>
    ...     <message class="error" context="input.cvv" key="too_long" />
    ...     <message class="error" context="input.card_number" key="failed_checksum" />
    ...   </messages>
    ...   <last_four_digits>1111</last_four_digits>
    ...   <card_type>visa</card_type>
    ...   <first_name>Bob</first_name>
    ...   <last_name>Smith</last_name>
    ...   <expiry_month type="integer">1</expiry_month>
    ...   <expiry_year type="integer">2020</expiry_year>
    ...   <address_1 nil="true"></address_1>
    ...   <address_2 nil="true"></address_2>
    ...   <city nil="true"></city>
    ...   <state nil="true"></state>
    ...   <zip nil="true"></zip>
    ...   <country nil="true"></country>
    ... </payment_method>
    ... '''

    >>> xml_to_dict(test)
    {'payment_method': {'payment_method_token': 'QhLaMNNpvHwfnFbHbUYhNxadx4C', 'card_type': 'visa', 'first_name': 'Bob', 'last_name': 'Smith', 'zip': {'nil': 'true'}, 'city': {'nil': 'true'}, 'messages': [{'context': 'input.cvv', 'class': 'error', 'key': 'too_long'}, {'context': 'input.card_number', 'class': 'error', 'key': 'failed_checksum'}], 'created_at': datetime.datetime(2011, 2, 12, 20, 20, 46), 'is_sensitive_data_valid': False, 'updated_at': datetime.datetime(2011, 4, 22, 17, 57, 30), 'custom': 'Any value you want us to save with this payment method.', 'last_four_digits': '1111', 'state': {'nil': 'true'}, 'is_retained': True, 'address_1': {'nil': 'true'}, 'address_2': {'nil': 'true'}, 'country': {'nil': 'true'}, 'is_redacted': False, 'expiry_year': 2020, 'expiry_month': 1}}

    """
    # Parent node.
    if el:
        if is_xml_el_dict(el):
            val = dict_from_xml(el)
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
