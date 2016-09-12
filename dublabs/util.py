from HTMLParser import HTMLParser

import vobject

CAMPUS = "Oregon State - Corvallis"
CAMPUS_LOC = "C"

# SO: http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def addCampus():
    entry = vobject.vCard()
    entry.add('n')
    entry.n.value = CAMPUS

    entry.add('fn')
    entry.fn.value = CAMPUS

    entry.add("X-D-LOC")
    entry.x_d_loc.value = CAMPUS_LOC

    entry.add('role')
    entry.role.value = "CAMPUS"

    return entry

def getVcard(attrib):
    """Returns a new vcard object with common attributes populated"""

    entry = vobject.vCard()

    entry.add('n')
    entry.n.value = attrib["name"]

    entry.add('fn')
    entry.fn.value = attrib["name"]

    entry.add('X-D-BLDG-LOC')
    entry.x_d_bldg_loc.value = CAMPUS_LOC

    entry.add('categories')
    entry.categories.value = ["Corvallis"]

    entry.add('note')
    entry.note.value = ""

    if attrib["summary"] is not None:
        entry.note.value = strip_tags(attrib["summary"]).encode('utf-8')

    if "abbreviation" in attrib and attrib["abbreviation"] is not None:
        entry.add("X-D-BLDG-ID")
        entry.x_d_bldg_id.value = attrib["abbreviation"].upper()

    return entry

def fixVcardEscaping(vcardText):
    """Fixes some escaping issues due to vobject library. 
    
    The ; and , shouldn't be escaped It modifies the vcard text.
    """
    vcardText = vcardText.replace('\;', ';')
    return vcardText.replace('\,', ',')

