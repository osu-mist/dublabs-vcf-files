from datetime import datetime
from operator import itemgetter
from dublabs import api, util

import json
import StringIO
import string
import vobject
import pytz


DEBUG = False

def getVcardSerialization(attrib):
    """Returns a vcard object ready to be serialized

    vcard object is populated with needed parameters from attrib data
    """
    entry = util.getVcard(attrib)

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

def getMealTime(datevalue):
    """Gets the UTC date value from a string and returns the time in local format
    """
    dateObject = datetime.strptime(datevalue, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)

    tz = pytz.timezone('America/Los_Angeles') 
    localTime = tz.normalize(dateObject.astimezone(tz))

    return localTime.strftime('%H%M%S%Z')

def writeVcardFile(filename, response):
    vcfFile = open(filename,'w')
    
    entry = util.addCampus()
    try:
        vcard = entry.serialize()
    except:
        vcard = entry.serialize()

    vcfFile.write(vcard)

    for x in response["data"]:
        # Skip on campus delivery
        if "Food 2 You" in x["attributes"]['name']:
            continue

        entry = getVcardSerialization(x["attributes"])

        try:
            vcard = entry.serialize()
        except:
            vcard = entry.serialize()

        vcard = util.fixVcardEscaping(vcard)
        vcfFile.write(vcard)

    vcfFile.close()

# Read configuration file in JSON format
config_data_file = open('configuration.json')
config_data  = json.load(config_data_file)

params = {"type": "dining", "page[size]":200}

# Process Dining Data
response = api.getLocationsData(config_data, params)
writeVcardFile('dininglocations.vcf', response)
