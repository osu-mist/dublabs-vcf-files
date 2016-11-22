# --*-- coding: utf-8 --*--
from datetime import datetime
from operator import itemgetter
from dublabs import api, util
from collections import defaultdict

import json
import StringIO
import string
import vobject
import pytz
import sys
import re


DEBUG = True

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
                openTimes[day_lookup[x]] += 1

        orderedTimeLookup = sorted(timeLookup.items(), key=lambda tup: tup[0])

        breakfast = ""
        lunch = ""
        dinner = ""
        openHourSuffix = ";;"

        if (DEBUG):
            print "【timeLookup.items】", timeLookup.items()
            print "【orderedTimeLookup:】", orderedTimeLookup

        # if len(orderedTimeLookup) > 0:
        #     breakfast = getMealDayTime(orderedTimeLookup, 0)
        #     print "【breakfast】", breakfast

        # if len(orderedTimeLookup) > 1:
        #     lunch = getMealDayTime(orderedTimeLookup, 1)
        #     print "【lunch】", lunch

        # if len(orderedTimeLookup) > 2:
        #     dinner = getMealDayTime(orderedTimeLookup, 2)
        #     print "【dinner】", dinner

        entry.x_dh_breakfast.value = breakfast + openHourSuffix
        entry.x_dh_lunch.value = lunch + openHourSuffix
        entry.x_dh_dinner.value = dinner + openHourSuffix

        # br_option, lunch_option, dinner_option = 1, 1, 1
        # for i, (openHour, _) in enumerate(orderedTimeLookup):
        #     if countHours(openHour) >= 7:
        #         if br_option > 1:
        #             entry.add("X-DH-BREAKFAST")
        #             entry.x_dh_breakfast.option_param = str(br_option)
        #         breakfast = getMealDayTime(orderedTimeLookup, i)
        #         entry.x_dh_breakfast.value = breakfast + openHourSuffix # overwrites previous one
        #         entry.x_dh_breakfast_label.value = "Open Hours"
        #         br_option += 1
        #     else:
        #         pass

        addBuildingID(attrib, entry)

    return entry

def countHours(openHour):
    """
    Calculate hours for openHours in the format of '100000Z-220000Z'
    """
    match = re.search(r'(?P<start>\d*)Z-(?P<end>\d*)Z', openHour)
    return abs(int(match.group('end')) - int(match.group('start'))) / 10000

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


def addFood(entry):
    """Adds label, summary and url for breakfast, lunch and dinner

    The entry passed in is modified. The values added are blank.
    """
    entry.add("X-DH-BREAKFAST")
    entry.x_dh_breakfast.option_param = '1'
    entry.add("X-DH-BREAKFAST-LABEL")
    entry.x_dh_breakfast_label.value = "Breakfast"

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

    return localTime.strftime('%H%M%SZ')

def writeVcardFile(filename, response):
    vcfFile = open(filename,'w')

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
