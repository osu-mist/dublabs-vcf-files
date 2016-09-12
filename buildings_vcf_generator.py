from dublabs import api, util

import json
import StringIO
import string
import vobject
import sys

def getVcardSerialization(attrib):
    """Returns a vcard object ready to be serialized

    vcard object is populated with needed parameters from attrib data
    """
    entry = util.getVcard(attrib)

    entry.add('role')
    entry.role.value = "BUILDING"

    if "latitude" in attrib and "longitude" in attrib:
        if attrib["latitude"] is not None and attrib["longitude"] is not None:
            entry.add('geo')
            entry.geo.value = attrib["latitude"]+';'+attrib["longitude"]

    if attrib["images"] and attrib["images"][0] is not None:
        entry.add("PHOTO")
        entry.photo.value_param = 'uri'
        entry.photo.value = attrib["images"][0]

    return entry

def writeVcardFile(filename, response):
    vcfFile = open(filename,'w')
    
    entry = util.addCampus()
    try:
        vcard = entry.serialize()
    except:
        vcard = entry.serialize()

    vcfFile.write(vcard)

    for x in response["data"]:
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
    config_data = json.load(config_data_file)
    params = {"type": "building", "page[size]": 200, "campus": "corvallis"}
    response = api.getLocationsData(config_data, params)
    writeVcardFile('buildings.vcf', response)
except:
    print "Please make sure placing the configuration file in the same directory and pass it as an argument!"
