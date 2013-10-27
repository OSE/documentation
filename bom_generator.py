import logging
import re
import requests
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import unescape


def main(argv):
    if '-d' in argv:
        logging.basicConfig(level=logging.DEBUG)
    parts = {} # see add_part() for structure
    URLS = [ # dozuki guides as xml
        'https://opensourceecology.dozuki.com/api/2.0/guides/85?type=xml', # bottom frame
        'https://opensourceecology.dozuki.com/api/2.0/guides/86?type=xml', # top frame
        'https://opensourceecology.dozuki.com/api/2.0/guides/84?type=xml', # overall machine
    ]
    for url in URLS:
        process_url(parts, url)
    output_bom(parts)


def process_url(parts, url):
    xml_str = requests.get(url).text

    logging.debug(xml_str)
    logging.debug('----------------')

    # Strip namespace to make the xml tree easier to work with
    xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)

    extract_parts(parts, url, xml_str)


def extract_parts(parts, url, xml_str):
    root = ET.fromstring(xml_str)

    parts_level = None
    lines = root.findall('./steps/step/lines/line')
    for line in lines:
        line_level = int(line.get('level'))
        if parts_level is not None:
            if line_level == parts_level:
                process_part_line(parts, url, line.text)
            else:
                parts_level = None
        elif line.text.startswith('Parts'):
            parts_level = line_level + 1


# Part lines must start with a number, then have a space, then have the part
# name. If you want to include more info, put it in parenthases after the
# part name.
def process_part_line(parts, url, line_text):
    clean = unescape(line_text, {'&quot;': '"'})
    logging.debug("Cleaned line: %s" % clean)
    match = re.match('([0-9]+) ([^(]+)', clean, re.MULTILINE) # match checks only beginning of line
    if not match:
        logging.error("Can't understand part line from %s: '%s'" % (url, line_text))
        logging.error("Cleaned it looks like: '%s'" % clean)
        return
    count = int(match.group(1).strip())
    name = match.group(2).strip()
    logging.debug("%s %s" % (count, name))
    add_part(parts, url, name, count)


def add_part(parts, used_by, name, count):
    if name not in parts:
        parts[name] = {'count': 0, 'used_by': set()}
    parts[name]['count'] += count
    parts[name]['used_by'].add(used_by)



def output_bom(parts):
    for part in parts:
        print("Count: %s, Part: %s" % (parts[part]['count'], part))
        for used_by in parts[part]['used_by']:
            print("    Used by: %s" % used_by)


main(sys.argv)
