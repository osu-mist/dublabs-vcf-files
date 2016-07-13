from HTMLParser import HTMLParser
from datetime import datetime
from operator import itemgetter

import json
import pycurl
import urllib
import StringIO
import string
import vobject
import pytz

CAMPUS = "Oregon State - Corvallis"
CAMPUS_LOC = "C"

DEBUG = False

def getAccessToken(url, client_id, client_secret):
    post_data = "client_id=" + client_id + "&client_secret=" + client_secret + "&grant_type=client_credentials"

    storage = StringIO.StringIO()
    curl    = pycurl.Curl()

    # Set options
    curl.setopt(pycurl.URL, url)                     # CURLOPT_URL in PHP
    curl.setopt(pycurl.POST, 1)                      # CURLOPT_POST in PHP
    curl.setopt(pycurl.POSTFIELDS, post_data)        # CURLOPT_POSTFIELDS in PHP
    curl.setopt(pycurl.WRITEFUNCTION, storage.write) # CURLOPT_RETURNTRANSFER in PHP

    # Send the request and save response
    curl.perform()

    # Close request to clear up some resources
    curl.close()

    response = storage.getvalue()
    return json.loads(response)


def getLocations(url, access_token, params):
    query_params = urllib.urlencode(params)
    api_call_url = url + "?" + query_params;
    headers      = ['Authorization: Bearer '+ access_token]

    storage = StringIO.StringIO()
    curl    = pycurl.Curl()

    # Set options
    curl.setopt(pycurl.URL, api_call_url)
    curl.setopt(pycurl.HTTPHEADER, headers) # CURLOPT_HTTPHEADER in PHP
    curl.setopt(pycurl.WRITEFUNCTION, storage.write)

    curl.perform()
    curl.close()

    response = storage.getvalue()
    return json.loads(response)

def getCampus():
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

def getDiningSerialization(attrib):
    entry = vobject.vCard()
    entry.add('n')
    entry.n.value = attrib["name"]

    entry.add('fn')
    entry.fn.value = attrib["name"]

    entry.add('X-D-BLDG-LOC')
    entry.x_d_bldg_loc.value = "C"

    entry.add('categories')
    entry.categories.value = ["Corvallis"]

    entry.add('note')
    entry.note.value = ""
    if attrib["summary"] is not None:
        entry.note.value = strip_tags(attrib["summary"]).encode('utf-8')

    if "abbreviation" in attrib and attrib["abbreviation"] is not None:
        entry.add("X-D-BLDG-ID")
        entry.x_d_bldg_id.value = attrib["abbreviation"]

    if (DEBUG):
        print "dining location: " + attrib["name"]
        print attrib

    if "openHours" in attrib and attrib["openHours"] and attrib["type"] == "dining":
        addFood(entry)
        day_lookup = { '1': "MO", '2': "TU", '3': "WE", '4': "TH", '5': "FR", '6': "SA", '7':"SU" }

        timeLookup = { }

        # build data structure to hold hours data for vcf
        for x in ['1', '2', '3', '4', '5', '6', '7']:
            dayOpenHours = attrib["openHours"][x]
            for v in dayOpenHours:
                openTime = getMealTime(v['start']) + "-" + getMealTime(v['end'])
                if openTime not in timeLookup:
                    timeLookup[openTime] = ''

                timeLookup[openTime] += day_lookup[x] + ","

        orderedTimeLookup = sorted(timeLookup.items(), key=lambda tup: tup[0])

        if (DEBUG):
            print timeLookup.items()
            print orderedTimeLookup

        if len(orderedTimeLookup) > 0:
            entry.x_dh_breakfast.value = getMealDayTime(orderedTimeLookup, 0)

        if len(orderedTimeLookup) > 1:
            entry.x_dh_lunch.value = getMealDayTime(orderedTimeLookup, 1)

        if len(orderedTimeLookup) > 2:
            entry.x_dh_dinner.value = getMealDayTime(orderedTimeLookup, 2)

        entry.x_dh_breakfast.value += ";;"
        entry.x_dh_lunch.value += ";;"
        entry.x_dh_dinner.value += ";;"

        addBuildingID(attrib, entry)

    return entry


def getMealDayTime(orderedTimeLookup, mealType):
    return orderedTimeLookup[mealType][1] + ";" + orderedTimeLookup[mealType][0].replace('-', ';')


def addBuildingID(attrib, entry):
    """Adds X-D-BLDG-ID to vcard entry

    Args:
        attrib (object): attribute dictionary from locations api
        entry (object): vcard object
    """
    entry.add("X-D-BLDG-ID")

    # @todo: the names from uhds don't exactly map to a location due to spelling
    zone = attrib["summary"].encode('utf-8').replace('Zone: ', '')
    parent_building_map = {
        'Austin Hall': 'Aust',
        'Dixon Recreation Center': 'DxLg',
        'International Living-Learning Center': 'ILLC',
        'Kelley Engineering Center': 'KEC',
        'Linus Pauling Science Center': 'LPSC',
        'Marketplace West': 'WsDn',
        'McNary Dining': 'McNy',
        'Memorial Union': 'MU',
        'Southside Station @ Arnold': 'ArnD',
        'The Learning Innovation Center': 'LInC',
        'Valley Library': 'VLib',
        'Weatherford Hall': 'Wfd',
    }
    entry.x_d_bldg_id.value = parent_building_map[zone]


def addFood(entry):
    """Adds label, summary and url for breakfast, lunch and dinner

    The entry passed in is modified. The values added are blank.
    """
    entry.add("X-DH-BREAKFAST-LABEL")
    entry.x_dh_breakfast_label.value = ""
    entry.add("X-DH-BREAKFAST-SUMMARY")
    entry.x_dh_breakfast_summary.value = ""
    entry.add("X-DH-BREAKFAST-URL")
    entry.x_dh_breakfast_url.value = ""

    entry.add("X-DH-LUNCH-LABEL")
    entry.x_dh_lunch_label.value = ""
    entry.add("X-DH-LUNCH-SUMMARY")
    entry.x_dh_lunch_summary.value = ""
    entry.add("X-DH-LUNCH-URL")
    entry.x_dh_lunch_url.value = ""

    entry.add("X-DH-DINNER-LABEL")
    entry.x_dh_dinner_label.value = ""
    entry.add("X-DH-DINNER-SUMMARY")
    entry.x_dh_dinner_summary.value = ""
    entry.add("X-DH-DINNER-URL")
    entry.x_dh_dinner_url.value = ""

    entry.add("X-DH-BREAKFAST")
    entry.x_dh_breakfast.option_param = '1'

    entry.add("X-DH-LUNCH")
    entry.x_dh_lunch.option_param = '1'

    entry.add("X-DH-DINNER")
    entry.x_dh_dinner.option_param = '1'


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

def getMealTime(datevalue):
    """Gets the UTC date value from a string and returns the time in local format
    """
    dateObject = datetime.strptime(datevalue, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)

    tz = pytz.timezone('America/Los_Angeles') 
    localTime = tz.normalize(dateObject.astimezone(tz))

    return localTime.strftime('%H%M%S%Z')

def writeVcardFile(filename, response):
    vcfFile = open(filename,'w')
    
    entry = getCampus()
    try:
        vcard = entry.serialize()
    except:
        vcard = entry.serialize()

    vcfFile.write(vcard)

    for x in response["data"]:
        # Skip on campus delivery
        if "Food 2 You" in x["attributes"]['name']:
            continue

        entry = getDiningSerialization(x["attributes"])

        try:
            vcard = entry.serialize()
        except:
            vcard = entry.serialize()

        vcard = fixVcardEscaping(vcard)
        vcfFile.write(vcard)

    vcfFile.close()

def fixVcardEscaping(vcardText):
    vcardText = vcardText.replace('\;', ';')
    return vcardText.replace('\,', ',')

# Read configuration file in JSON format
config_data_file = open('configuration.json')
config_data      = json.load(config_data_file)

base_url         = config_data["hostname"] + config_data["version"] + config_data["api"]
access_token_url = base_url + config_data["token_endpoint"]

access_token_response = getAccessToken(access_token_url, config_data["client_id"], config_data["client_secret"]);

access_token  = access_token_response["access_token"]
locations_url = base_url + config_data["locations_endpoint"]
params        = {"type": "dining", "page[size]":200}

# Process Dining Data
response = getLocations(locations_url, access_token, params)
writeVcardFile('dininglocations.vcf', response)

#@todo: sed -i='' 's/\\;/;/g' dininglocations.vcf && sed -i='' 's/\\,/,/g' dininglocations.vcf
#python dining_vcf_generator.py && sed -i='' 's/\\;/;/g' dininglocations.vcf && sed -i='' 's/\\,/,/g' dininglocations.vcf
