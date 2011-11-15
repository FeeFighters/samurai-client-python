def _dict_to_xml(in_data):
    doc_tagname = in_data.keys()[0]
    xml = parseStringToXML("<%s></%s>" % (doc_tagname, doc_tagname) )
    for tag_name, tag_value in in_data[doc_tagname].iteritems():
        newElement = xml.createElement(tag_name)
        newTextNode = xml.createTextNode( str(tag_value) )
        xml.documentElement.appendChild( newElement )
        newElement.appendChild( newTextNode )
    return xml.toxml()

def _xml_to_dict(xml_string):
    try:
        xml_data = parseStringToXML(xml_string)
    except: # parse error, or something
        return None # error code, perhaps

    return _xml_outer_node_to_dict(xml_data.documentElement)

