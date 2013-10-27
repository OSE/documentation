import json
import logging
import re
import sys
import urllib2


def main(argv):
    if '-d' in argv:
        logging.basicConfig(level=logging.DEBUG)
    parts = {} # see add_part() for structure
    DOZUKI_GUIDE_IDS = [
        85, # bottom frame
        86, # top frame
        84, # overall machine
    ]
    BASE_URL = 'https://opensourceecology.dozuki.com/api/2.0/guides'
    for guide_id in DOZUKI_GUIDE_IDS:
        url = "%s/%s" % (BASE_URL, guide_id)
        process_url(parts, url)
    output_bom(parts)


def process_url(parts, url):
    json_str = urllib2.urlopen(url).read()
    guide = json.loads(json_str)

    logging.debug(json.dumps(guide, sort_keys=True, indent=4, separators=(',', ': ')))
    logging.debug('----------------')

    extract_parts(parts, guide)


def extract_parts(parts, guide):
    parts_level = None
    for step in guide['steps']:
        for line in step['lines']:
            if parts_level is not None:
                if line['level'] == parts_level:
                    process_part_line(parts, guide, step, line['text_raw'])
                else:
                    parts_level = None
            elif line['text_raw'].startswith('Parts'):
                parts_level = line['level'] + 1


# Part lines must start with a number, then have a space, then have the part
# name. If you want to include more info, put it in parenthases after the
# part name.
def process_part_line(parts, guide, step, line_text):
    match = re.match('([0-9]+) ([^(]+)', line_text, re.MULTILINE) # match checks only beginning of line
    if not match:
        logging.error("Can't understand part line from '%s', step %s: '%s'" % (guide['title'], step['orderby'], line_text))
        return
    count = int(match.group(1).strip())
    name = match.group(2).strip()
    logging.debug("%s %s" % (count, name))
    add_part(parts, guide['title'], name, count)


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
