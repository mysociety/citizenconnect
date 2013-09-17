"""convert json to csv
Author: Stephen Emslie
"""

USAGE = """
    django-admin.py dumpdata myapp.mymodel > /path/to/in.json
    python %prog /path/to/in.json /path/to/out.csv

    or in one command:

    django-admin.py dumpdata myapp.mymodel | python %prog - /tmp/out.csv
"""

import csv
import sys
import json
from optparse import OptionParser

if __name__ == '__main__':
    parser = OptionParser(usage=USAGE)
    options, args = parser.parse_args()
    path, outpath = args[0], args[1]
    if path == '-':
        source = sys.stdin
    else:
        source = open(path)
    s = source.read()
    objects = [dict({'id': object['pk']}.items() + object['fields'].items()) for object in json.loads(s)]
    writer = csv.DictWriter(open(outpath, 'w'), objects[0].keys())
    headings = {'id': 'id'}
    headings.update(dict(zip(objects[0].keys(), objects[0].keys())))
    objects.insert(0, headings)
    for d in objects:
        for key, value in d.items():
            if isinstance(value, basestring):
                d[key] = value.encode('utf8')
    writer.writerows(objects)
