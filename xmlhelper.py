from xml.dom.minidom import parse as parse_xml
from xml.dom.minidom import parseString as parse_string

def indent(depth):
    return ''.join([' ' for x in xrange(depth)])

def dump(n, depth = 0):
    "Dump a minodom DOM"

    if n.nodeType == n.ELEMENT_NODE:
        print '%s+ %s'%(indent(depth), n.nodeName)
        for (k, v) in n.attributes.items():
            print '%s - %s = %s'%(indent(depth), k, v)
    elif n.nodeType == n.TEXT_NODE:
        s = n.wholeText.rstrip('\t\r\n ')
        if len(s):
            print '%so %s'%(indent(depth), s)

    for x in n.childNodes:
        dump(x, depth + 1)

def dump2(n, depth = 0):
    "Dump a XMLNode DOM"

    print '%s+ %s'%(indent(depth), n.name)
    for (k, v) in n.attrib.items():
        print '%s - %s = %s'%(indent(depth), k, v)
    if n.text is not None:
        print '%so %s'%(indent(depth), n.text)
    for x in n.children:
        dump2(x, depth + 1)

def children(node):
    return filter(lambda x:x.nodeType == x.ELEMENT_NODE, node.childNodes)
def text(node):
    return filter(lambda x:x.nodeType == x.TEXT_NODE, node.childNodes)

class XMLNode:
    "Simple XML DOM structure"

    def __str__(self):
        return 'XMLNode(%s)'%self.name
    def __repr__(self):
        return 'XMLNode(%s)'%self.name

    def __init__(self, n):
        self.name = n.nodeName
        self.child = {}
        self.children = []
        self.attrib = dict(n.attributes.items())
        for x in children(n):
            c = XMLNode(x)
            self.child.setdefault(c.name, [])
            self.child[c.name].append(c)
            self.children.append(c)

        ss = ''
        for x in text(n):
            s = x.wholeText.rstrip('\t\r\n ')
            ss += s
        if len(ss):
            self.text = ss
        else:
            self.text = None

    def __getitem__(self, key):
        return self.attrib[key]
    def has_attrib(self, key):
        return self.attrib.has_key(key)

def parse_xml_file(fn, verbose = False):
    if verbose:
        print fn
    doc = parse_xml(fn)
    ret = XMLNode(doc.childNodes[0])
    if verbose:
        dump2(ret)
        print
    return ret

def parse_xml_string(s, verbose = False):
    doc = parse_string(s)
    ret = XMLNode(doc.childNodes[0])
    if verbose:
        dump2(ret)
        print
    return ret
