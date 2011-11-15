"""
Methods to work with XML.
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import datetime
from utils import str_to_datetime, str_to_boolean

def xml_to_dict(root_or_str):
    """
    Converts `root_or_str` which can be parsed xml or a xml string to dict.
    """
    root = root_or_str
    if isinstance(root, str):
        import xml.etree.cElementTree as ElementTree
        root = ElementTree.XML(root_or_str)
    return {root.tag: from_xml(root)}

def dict_to_xml(dict_xml):
    """
    Converts `dict_xml` which is a python dict to corresponding xml.

    >>> dict_xml = {'transaction': {'amount': '100.00','currency_code': 'USD'}}

    >>> expected = '<transaction><amount>100.00</amount><currency_code>USD</currency_code></transaction>'
    >>> expected == dict_to_xml(dict_xml)
    True
    """
    return xml_from_dict(dict_xml)

# Functions below this line are implementation details.
# Unless you are changing code, don't bother reading.
# The functions above constitute the user interface.

def to_xml(tag, content):
    if isinstance(content, dict):
        val = '<%(tag)s>%(content)s</%(tag)s>' % dict(tag=tag,
                                                      content=xml_from_dict(content))
    else:
        val = '<%(tag)s>%(content)s</%(tag)s>' % dict(tag=tag, content=content)
    return val

def xml_from_dict(dict_xml):
    """
    Converts `dict_xml` which is a python dict to corresponding xml.
    """
    tags = []
    for tag, content in dict_xml.iteritems():
        tags.append(to_xml(tag, content))
    return ''.join(tags)

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

    >>> expected = {'payment_method': {'address_1': {'nil': 'true'},
    ...   'address_2': {'nil': 'true'},
    ...   'card_type': 'visa',
    ...   'city': {'nil': 'true'},
    ...   'country': {'nil': 'true'},
    ...   'created_at': datetime.datetime(2011, 2, 12, 20, 20, 46),
    ...   'custom': 'Any value you want us to save with this payment method.',
    ...   'expiry_month': 1,
    ...   'expiry_year': 2020,
    ...   'first_name': 'Bob',
    ...   'is_redacted': False,
    ...   'is_retained': True,
    ...   'is_sensitive_data_valid': False,
    ...   'last_four_digits': '1111',
    ...   'last_name': 'Smith',
    ...   'messages': {'message': [{'class': 'error',
    ...      'context': 'input.cvv',
    ...      'key': 'too_long'},
    ...     {'class': 'error',
    ...      'context': 'input.card_number',
    ...      'key': 'failed_checksum'}]},
    ...   'payment_method_token': 'QhLaMNNpvHwfnFbHbUYhNxadx4C',
    ...   'state': {'nil': 'true'},
    ...   'updated_at': datetime.datetime(2011, 4, 22, 17, 57, 30),
    ...   'zip': {'nil': 'true'}}}
    >>> expected == xml_to_dict(test)
    True
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
    tag = els[0].tag
    for el in els:
        res.append(from_xml(el))
    return {tag: res}

def dict_from_xml(els):
    """
    Converts xml doc with root `root` to a python dict.
    """
    # An element with subelements.
    res = {}
    for el in els:
        res[el.tag] = from_xml(el)
    return res
