# --*-- coding: utf-8 --*--
from datetime import datetime
from operator import itemgetter
from dublabs import api, util

import json
import StringIO
import string
import vobject
import pytz
import sys
import re


DEBUG = False
BREAKFAST_LABEL = "Open hours"
LUNCH_LABEL = "Open hours"
DINNER_LABEL = "Open hours"

def getVcardSerialization(attrib, meal_desc):
    """Returns a vcard object ready to be serialized

    vcard object is populated with needed parameters from attrib data
    """
    entry = util.getVcard(attrib)

    if (DEBUG):
        print "dining location: " + attrib["name"]
        print attrib

    if "openHours" in attrib and attrib["openHours"] and attrib["type"] == "dining":
        # addFood(entry, "breakfast")
        # addFood(entry, "lunch")
        # addFood(entry, "dinner")
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

        openHourSuffix = ";;"

        if (DEBUG):
            print "【timeLookup.items】", timeLookup.items()
            print "【orderedTimeLookup:】", orderedTimeLookup

        br_option, lunch_option, dinner_option = 1, 1, 1
        for i, (openHour, _) in enumerate(orderedTimeLookup):
            time = getStartTime(openHour)
            value = getMealDayTime(orderedTimeLookup, i) + openHourSuffix
            if time < 1030:
                addFood(entry, "breakfast", meal_desc, value, str(br_option))
                br_option += 1
            elif time >= 1530:
                addFood(entry, "dinner", meal_desc, value, str(dinner_option))
                dinner_option += 1
            else:
                addFood(entry, "lunch", meal_desc, value, str(lunch_option))
                lunch_option += 1

        addBuildingID(attrib, entry)

    return entry


def getStartTime(openHour):
    """
    Return the starting time of the open hour
    :type: String, e.g.'100000Z-220000Z'
    :rtype: Int, e.g.1000
    """
    match = re.search(r'(?P<start>\d*)Z-\d*Z', openHour)
    return int(match.group('start')) / 100


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
        'Austin Hall': 'AUST',
        'Dixon Recreation Center': 'DXRC',
        'International Living-Learning Center': 'ILLC',
        'Kelley Engineering Center': 'KEC',
        'Linus Pauling Science Center': 'LPSC',
        'Marketplace West': 'WSDN',
        'McNary Dining': 'MCNY',
        'Memorial Union': 'MU',
        'Southside Station @ Arnold': 'ARND',
        'The Learning Innovation Center': 'LINC',
        'Valley Library': 'VLIB',
        'Weatherford Hall': 'WFD',
    }
    entry.x_d_bldg_id.value = parent_building_map[zone]


def addFood(entry, mealTime, meal_desc, value="", option_param="1"):
    """
    Adds label, option_param for breakfast/lunch/dinner
    :type mealTime: String
    :type option_param: Int
    """
    if mealTime == "breakfast":
        tmp = entry.add("X-DH-BREAKFAST-" + option_param)
        tmp.option_param = option_param
        tmp.value = value
        label = entry.add("X-DH-BREAKFAST-%s-LABEL" % option_param)
        label.value = BREAKFAST_LABEL
        summary = entry.add("X-DH-BREAKFAST-SUMMARY")
        summary.value = meal_desc["breakfast_description"]

    elif mealTime == "lunch":
        tmp = entry.add("X-DH-LUNCH-" + option_param)
        tmp.option_param = option_param
        tmp.value = value
        label = entry.add("X-DH-LUNCH-%s-LABEL" % option_param)
        label.value = LUNCH_LABEL
        summary = entry.add("X-DH-LUNCH-SUMMARY")
        summary.value = meal_desc["lunch_description"]

    elif mealTime == "dinner":
        tmp = entry.add("X-DH-DINNER-" + option_param)
        tmp.option_param = option_param
        tmp.value = value
        label = entry.add("X-DH-DINNER-%s-LABEL" % option_param)
        label.value = DINNER_LABEL
        summary = entry.add("X-DH-DINNER-SUMMARY")
        summary.value = meal_desc["dinner_description"]

def getMealTime(datevalue):
    """Gets the UTC date value from a string and returns the time in local format
    """
    dateObject = datetime.strptime(datevalue, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)

    tz = pytz.timezone('America/Los_Angeles')
    localTime = tz.normalize(dateObject.astimezone(tz))

    return localTime.strftime('%H%M%SZ')


def writeVcardFile(filename, response):
    vcfFile = open(filename,'w')
    meal_descs_json = open('osu-corvallis-food-locations.json')
    meal_descs = json.load(meal_descs_json)

    for x in response["data"]:
        # Skip on campus delivery
        if "Food 2 You" in x["attributes"]['name']:
            continue

        try:
            meal_desc = meal_descs[x["id"]]
        except KeyError:
            meal_desc = meal_descs["default_descriptions"]

        entry = getVcardSerialization(x["attributes"], meal_desc)

        try:
            vcard = entry.serialize()
        except:
            vcard = entry.serialize()

        vcard = util.fixVcardEscaping(vcard)
        vcard = re.sub(r"(BREAKFAST|LUNCH|DINNER)(-\d)", r"\1", vcard)
        vcfFile.write(vcard)

    vcfFile.close()


try:
    # Read configuration file in JSON format
    config_data_file = open(sys.argv[1])
    config_data  = json.load(config_data_file)
    params = {"type": "dining", "page[size]": 200}
    # Process Dining Data
    response = api.getLocationsData(config_data, params)
    writeVcardFile('dininglocations.vcf', response)
except:
    raise
    print "Please make sure placing the configuration file in the same directory and pass it as an argument!"
