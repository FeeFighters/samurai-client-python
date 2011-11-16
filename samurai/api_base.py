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

    def __init__(self):
        self.errors = None

    def check_for_error(self, parsed_res):
        """
        Checks `parsed_res` for error blocks.
        If it contains error blocks, it return True and sets errors.
        Returns false otherwise.
        """
        error = False
        if parsed_res.get('error'):
            error = True
            if parsed_res['error'].get('messages'):
                self.errors = parsed_res['error']['messages']
        return error

    def update_fields(self, xml_res):
        """
        Updates field with the returned `xml_res`.
        """
        parsed_res = xml_to_dict(xml_res)
        if not self.check_for_error(parsed_res) and parsed_res[self.top_xml_key]:
            self.__dict__.update(**parsed_res[self.top_xml_key])

