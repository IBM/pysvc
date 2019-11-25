##############################################################################
# Copyright 2019 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

import xml.etree.ElementTree as et
import xml.etree.cElementTree as cet
from contextlib import contextmanager
from xml.parsers.expat import ExpatError
from pysvc.unified.helpers.xml_util import XMLSyntaxError, \
    ElementNotFoundException


# et.Element.tostring = et.tostring
# cet.Element.tostring = cet.tostring

Element = cet.Element


@contextmanager
def _translateExceptions(original):
    try:
        yield None
    except ExpatError as e:
        raise XMLSyntaxError(original, e.args[0], e.lineno)
    except (cet.ParseError, et.ParseError) as e:
        raise XMLSyntaxError(original, e.args[0], e.lineno)


def fromstring(text):
    with _translateExceptions(None):
        return cet.fromstring(text)


tostring = cet.tostring


def parse(obj):
    with _translateExceptions(None):
        return cet.parse(obj)


def xml_find(elem, path, attrib=None):
    elem2 = elem.find(path)
    if elem2 is None:
        raise ElementNotFoundException(elem, path)
    if attrib is None:
        return elem2
    else:
        if attrib not in elem2.attrib:
            raise ElementNotFoundException(elem, "%s/@%s" % (path, attrib))
        return elem2.attrib[attrib]

# =========================================================================
# TerminationDetectingXMLParser
# =========================================================================


class _TerminationDetectingTreeBuilder(et.TreeBuilder):

    def __init__(self):
        et.TreeBuilder.__init__(self)
        self.root_element = None
        self.root_element_closed = False

    def start(self, tag, attrs):
        element = et.TreeBuilder.start(self, tag, attrs)
        if self.root_element is None:
            self.root_element = element
        return element

    def end(self, tag):
        element = et.TreeBuilder.end(self, tag)
        if self.root_element is element:
            self.root_element_closed = True
        return element


class TerminationDetectingXMLParser(object):

    """An XML parser which you can feed from a stream; knows automatically
    when the first tag was closed"

    >>> td = TerminationDetectingXMLParser()
    >>> td.feed('<a>')
    >>> td.root_element_closed
    False
    >>> td.feed('</a>')
    >>> td.root_element_closed
    True
    >>> td.close().tostring()
    '<a/>'

    >>> td = TerminationDetectingXMLParser()
    >>> td.feed('<a><b></b></a>')
    >>> td.root_element_closed
    True
    >>> td.close().tostring()
    '<a><b/></a>'

    >>> td = TerminationDetectingXMLParser()
    >>> td.feed('<a<a') #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    ParseError: not well-formed (invalid token): line 1, column 2
    >>>
    """

    def __init__(self):
        self.tree_builder = _TerminationDetectingTreeBuilder()
        self.xml_tree_builder = et.XMLTreeBuilder(target=self.tree_builder)

    def feed(self, chunk):
        with _translateExceptions(chunk):
            self.xml_tree_builder.feed(chunk)

    def close(self):
        with _translateExceptions(None):
            tree = self.xml_tree_builder.close()
            return fromstring(tostring(tree))

    @property
    def root_element_closed(self):
        return self.tree_builder.root_element_closed
