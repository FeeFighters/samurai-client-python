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
        # Check high level errors.
        if parsed_res.get('error'):
            error = True
            if parsed_res['error'].get('messages'):
                self.errors = parsed_res['error']['messages'].get
        # Check request specific error.
        elif parsed_res.get(self.message_block) and parsed_res[self.message_block].get('message'):
            error = any(True for m in parsed_res[self.message_block]['message']
                        if m['class'] == 'error')
            if error:
                self.errors = parsed_res[self.message_block]
        return error

    def update_fields(self, xml_res):
        """
        Updates field with the returned `xml_res`.
        """
        parsed_res = xml_to_dict(xml_res)
        if not self.check_for_error(parsed_res) and parsed_res.get(self.top_xml_key):
            self.__dict__.update(**parsed_res[self.top_xml_key])

