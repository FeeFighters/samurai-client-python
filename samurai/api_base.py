"""
    api_base
    ~~~~~~~~~~~~

    Abstraction for behavior common to other api objects.
"""
from xmlutils import xml_to_dict

class ApiBase(object):
    """
    This object implements behavior common to non-abstract api objects.

    It's basically a mix-in which adds methods to subclasses.
    Most of the methods here are template methods http://en.wikipedia.org/wiki/Template_method_pattern
    """
    def update_fields(self, xml_res):
        """
        Updates field with the returned `xml_res`.
        """
        parsed_data = xml_to_dict(xml_res)
        if parsed_data[self.top_xml_key]:
            self.__dict__.update(**parsed_data[self.top_xml_key])

