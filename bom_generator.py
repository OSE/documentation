from datetime import datetime
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
        87, # shear table
        84, # assemble the pieces
    ]
    print "Processing %s guides..." % len(DOZUKI_GUIDE_IDS)
    BASE_URL = 'https://opensourceecology.dozuki.com/api/2.0/guides'
    for guide_id in DOZUKI_GUIDE_IDS:
        url = "%s/%s" % (BASE_URL, guide_id)
        process_url(parts, url)
    output_bom(parts)


def process_url(parts, url):
    try:
        json_str = urllib2.urlopen(url).read()
    except urllib2.HTTPError:
        logging.error("There was an error loading guide %s. Make sure it's public." % url)
        raise

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
    match = re.match('([0-9.]+) ([^(]+)', line_text, re.MULTILINE) # match checks only beginning of line
    if not match:
        logging.error("Can't understand part line from '%s', step %s: '%s'" % (guide['title'], step['orderby'], line_text))
        return
    count = float(match.group(1).strip())
    name = match.group(2).strip()
    logging.debug("%s %s" % (count, name))
    add_part(parts, "%s, step %s" % (guide['title'], step['orderby']), name, count)


def add_part(parts, used_by, name, count):
    if name[-1] != 's':
        name = name + 's'

    if name not in parts:
        parts[name] = {'count': 0, 'used_by': set()}
    parts[name]['count'] += count
    parts[name]['used_by'].add(used_by)


def plural(num, text):
    if text[-1:] == 's':
        text = text[:-1]
    suffix = 's'
    if num==1 or text[-6:]=='grease' :  #if it ends in the word grease or there is only one
        suffix = ''
    return "%s%s" % (text, suffix)


def make_parts_table(parts):
    rval = ''
    rval += "Count\t Part\n"
    rval += "-----\t ----\n"
    for part in sorted(parts.keys(), key=lambda x: x.split()[-1] + x):
        count = parts[part]['count']
        if float(round(count)) == count:
            count = int(count)
        part_name = plural(count,part)
        rval += "" + '%5s' % format(str(count)) + "\t " + part_name + "\n"
    return rval


def output_bom(parts):
    print("\n\n<!--START OF GENERATED BOM. Copy from here until the end into the wiki.-->")
    print("<pre>")
    print("This BOM was generated from the dozuki guides on %s\n" % datetime.now())
    print(
        "WARNING: If you hand-edit this list, your changes will be lost when "
        "the BOM is regenerated. If anything is wrong, you should update the "
        "parts entries in dozuki, fix bom_generator.py, or make a note in a "
        "section other than the generated list.\n")
    print('')
    print(make_parts_table(parts))
    print('')
    for part in sorted(parts.keys(), key=lambda x: x.split()[-1] + x):
        count = parts[part]['count']
        if float(round(count)) == count:
            count = int(count)
        part_name = plural(count,part)
        print("Count: %s, Part: %s" % (count, part_name))
        for used_by in parts[part]['used_by']:
            print("    Used by: %s" % used_by)
    print("</pre>")
    print("<!--END OF GENERATED BOM.-->")


main(sys.argv)

