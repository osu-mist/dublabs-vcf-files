from HTMLParser import HTMLParser
from datetime import datetime

import json
import pycurl
import urllib
import StringIO
import string
import vobject
import pytz

CAMPUS = "Oregon State - Corvallis"
CAMPUS_LOC = "C"

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
    entry.note.value = "todo: put url or something else here??"
    if attrib["summary"] is not None:
        entry.note.value = strip_tags(attrib["summary"]).encode('utf-8')

    if "abbreviation" in attrib and attrib["abbreviation"] is not None:
        entry.add("X-D-BLDG-ID")
        entry.x_d_bldg_id.value = attrib["abbreviation"]

    if "latitude" in attrib and "longitude" in attrib:
        if attrib["latitude"] is not None and attrib["longitude"] is not None:
            entry.add('geo')
            entry.geo.value = attrib["latitude"]+';'+attrib["longitude"]

    print attrib
    print attrib["openHours"].get("1")
    if "openHours" in attrib and attrib["openHours"] and attrib["type"] == "dining":
        print "dining location: " + attrib["name"]
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

        day_lookup = { '1': "MO", '2': "TU", '3': "WE", '4': "TH", '5': "FR", '6': "SA", '7':"SU" }

        breakfast_days = ""
        lunch_days = ""
        dinner_days = ""

        # iterate over days 1-7 to add their available to breakfast, lunch and dinner
        for x in ['1', '2', '3', '4', '5', '6', '7']:
            if attrib["openHours"][x]:
                meals = len(attrib["openHours"][x])
                if meals == 1:
                    breakfast_days += day_lookup[x] + ","
                if meals > 1:
                    lunch_days += day_lookup[x] + ","
                if meals > 2:
                   dinner_days += day_lookup[x] + ","

        breakfast_days += ";"
        lunch_days     += ";"
        dinner_days    += ";"
        monday = attrib["openHours"]['1']
        
        # iterate over # time slots on Monday / first day of week
        if len(monday) >=1:
            breakfast_days += getMealTime(monday[0]['start']) + ";" + getMealTime(monday[0]['end']) + ";;"

        if len(monday) >=2:
            lunch_days += getMealTime(monday[1]['start']) + ";" + getMealTime(monday[1]['end']) + ";;"

        if len(monday) >=3:
            dinner_days += getMealTime(monday[2]['start']) + ";" + getMealTime(monday[2]['end']) + ";;"

        entry.x_dh_breakfast.value = breakfast_days
        entry.x_dh_lunch.value = lunch_days
        entry.x_dh_dinner.value = dinner_days
        #@todo: need to match dining location with building id

        entry.add("X-D-BLDG-ID")

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
            'The Learning Innovation Center': 'VLib', # @todo!!!!!
            'Valley Library': 'VLib',
            'Weatherford Hall': 'Wfd',
        }
        entry.x_d_bldg_id.value = parent_building_map[zone]


    return entry

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
