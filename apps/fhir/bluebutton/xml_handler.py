#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: xml_handler.py
Created: 3/28/17 3:00 PM

File created by: ''
"""
import logging
# import xml.etree.ElementTree as ET
# Replacing xml.etree.ElementTree to avoid xml exploits
import defusedxml.ElementTree as ET


from apps.fhir.bluebutton.utils import get_resource_names, get_resourcerouter
from apps.fhir.fhir_core.utils import valid_interaction

FHIR_NAMESPACE = {'fhir': 'http://hl7.org/fhir'}
XML_NAMESPACE = {'xml': 'http://www.w3.org/1999/xhtml'}
# ns_string will get value from first key in above dict
# ns_string can receive a dict to allow the default to be overridden

logger = logging.getLogger('hhs_server.%s' % __name__)


def xml_to_dom(xml_string):
    """
    convert an text string to an xml document we can manipulate
    using ElementTree.

    Import ElementTree as ET to allow changing the underlying library
    without impacting code.
    :param: xml_string
    :return dom
    """

    # Take the xml text and convert to a DOM
    dom = string_to_dom(xml_string)

    return dom


def dom_conformance_filter(dom, rr=None, ns=FHIR_NAMESPACE):
    """
    filter conformance statement to remove unsupported resources and
    interactions
    :param dom:
    :param ns:
    :return:
    """

    if rr is None:
        rr = get_resourcerouter()
    # Now we need to filter the Dom Conformance Statement
    dom = filter_dom(dom, rr, ns)

    # Then convert back to text to allow publishng
    back_to_xml = ET.tostring(dom).decode("utf-8")

    # logger.debug("New XML:\n%s" % back_to_xml)
    # logger.debug("XML is type:%s" % type(back_to_xml))

    return back_to_xml
    # return xml_to_dict


def string_to_dom(content, ns=FHIR_NAMESPACE):
    """
    Use ElementTree to parse content

    :param content:
    :return:
    """
    # ns = FHIR_NAMESPACE
    # print("Content:\n%s\n=================" % content)
    root = ET.fromstring(content)

    return root


def filter_dom(root, rr=None, ns=FHIR_NAMESPACE):
    """
    remove unwanted elements from dom
    :param dom:
    :param ns:
    :return:
    """

    if rr is None:
        rr = get_resourcerouter()
    # Get the published fhir resources as a list
    pub_resources = get_resource_names(rr)

    element_rest = root.findall('{%s}rest' % ns_string(ns), ns)
    for rest in element_rest:
        # logger.debug("REST:%s" % rest.tag)
        # We want the resource elements
        child_list = get_named_child(rest,
                                     '{%s}resource' % ns_string(ns))
        # logger.debug("Rest KIDS:%s" % child_list)
        for resource in child_list:
            # logger.debug("Resource:%s" % resource.tag)

            # Now we need to find the type element in resource
            element_type = resource.findall('{%s}type' % ns_string(ns))
            element_interaction = resource.findall('{%s}'
                                                   'interaction' % ns_string(ns))
            for t in element_type:
                # logger.debug("R:%s" % no_ns_name(t.attrib))
                if no_ns_name(t.attrib) in pub_resources:
                    # logger.debug("Publishing:%s" % no_ns_name(t.attrib))

                    # this resource is to be published
                    # We need to remove unsupported interactions
                    # get all interactions in resource
                    # check interaction code against supported resource type
                    # actions
                    # remove disabled actions
                    pub_interactions = valid_interaction(no_ns_name(t.attrib),
                                                         rr)
                    # logger.debug("Interactions:%s" % pub_interactions)

                    for e in element_interaction:
                        for c in e.findall('{%s}code' % ns_string(ns)):
                            e_action = c.attrib['value']
                            # print("What is element:%s" % e_action)
                            if e_action in pub_interactions:
                                pass
                                # logger.debug("Interaction "
                                #              "Enabled:%s" % e_action)
                                # No change - valid interaction
                            else:
                                # logger.debug("Interaction "
                                #              "Removed:%s" % e_action)
                                # Remove interaction from the resource
                                resource.remove(e)

                else:
                    # remove this node from child_list
                    # logger.debug("Removing:%s" % no_ns_name(t.attrib))
                    # logger.debug("Resource:%s" % resource)
                    rest.remove(resource)
                    # logger.debug("Child_list:%s" % child_list)

        # logger.debug("Root:%s" % root)

    return root


def get_named_child(root, named=None, x_field='tag'):
    """
    Traverse the Document segment
    :param root:
    :param named=None
    :param x_field='tag|value'
    :return: kids
    """
    kids = []
    # logger.debug(root)
    for child in root:
        # logger.debug("Evaluating:%s" % child)
        # logger.debug("%s:%s" % (named, child.get(x_field)))
        if named:
            if child.tag == named:
                # logger.debug("%s child:%s" % (named, no_ns_name(child.tag)))
                kids.append(child)

            else:
                pass

    return kids


def no_ns_name(name_string, ns=FHIR_NAMESPACE):
    """
    Strip the name space from the element name
    :param name:
    :param ns:
    :return: short_name
    """

    nspace = ns[next(iter(ns))]
    # logger.debug("Name:%s in %s" % (nspace, name_string))
    # Remove name space prefix
    if type(name_string) is dict:
        new_name_string = name_string[next(iter(name_string))]
        # logger.debug("From:%s to %s" % (name_string, new_name_string))
    else:
        new_name_string = name_string
    short_name = new_name_string.replace("{%s}" % nspace, "")

    return short_name


def ns_string(ns=FHIR_NAMESPACE):
    """
    get the namespace string from the global variable: FHIR_NAMESPACE
    """
    nss = ns

    return nss[next(iter(nss))]


def get_div_from_xml(xml_text, ns=FHIR_NAMESPACE):
    """
    Get the div from a xml resource
    :param xml_text:
    :return: div_text
    """

    if xml_text == '':
        # nothing to process
        return xml_text
    dom = string_to_dom(xml_text)

    dom_text = dom.findall('{%s}text' % ns_string(ns))
    # print("DOM Text:%s" % dom_text)
    aggregated_divs = []

    for divot in dom_text:
        child_list = get_named_child(divot,
                                     '{%s}div' % ns_string(XML_NAMESPACE))
        # print("Child list of div elements:%s" % child_list)
        aggregated_divs.append(child_list)

    # print("Divs to publish:%s" % aggregated_divs)
    div_text = ""
    for aggregated_div in aggregated_divs:
        # print("AD:%s" % aggregated_div)
        # print("AD[0]:%s" % aggregated_div[0])
        div_text += ET.tostring(aggregated_div[0], method="html").decode('utf-8')
        div_text += "\n"
    # div_text = aggregated_divs.tostring()
    # print("DV:%s" % div_text)
    # Replace html: in output
    # <html:div xmlns:html="http://www.w3.org/1999/xhtml">
    #      <html:div class="hapiHeaderText"> William Yung
    #         <html:b>CHEN </html:b>

    div_text = div_text.replace("html:", "")

    # Becomes this. This avoids strange results in the css when displayed
    # <div xmlns:html="http://www.w3.org/1999/xhtml">
    #      <div class="hapiHeaderText"> William Yung
    #         <b>CHEN </b>
    #      </div>
    # print("filtered DV:%s" % div_text)
    return div_text
