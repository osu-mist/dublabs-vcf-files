import json
import pycurl
import urllib
import StringIO
import vobject

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

def getDiningSerialization(attrib):
    entry = vobject.vCard()
    entry.add('n')
    entry.n.value = str(attrib["name"])

    entry.add('fn')
    entry.fn.value = str(attrib["name"])

    entry.add('X-D-BLDG-LOC')
    entry.x_d_bldg_loc.value = "C"

    entry.add('role')
    entry.role.value = "BUILDING"

    entry.add('note')
    entry.note.value = str(attrib["summary"])

    if "abbreviation" in attrib and attrib["abbreviation"] is not None:
        entry.add("X-D-BLD-ID")
        entry.x_d_bld_id.value = str(attrib["abbreviation"])

    if "latitude" in attrib and "longitude" in attrib:
        if attrib["latitude"] is not None and attrib["longitude"] is not None:
            entry.add('geo')
            entry.geo.value = attrib["latitude"]+','+attrib["longitude"]
    
    entry.prettyPrint()
    return entry

def writeVcardFile(filename, response):
    vcfFile = open(filename,'w')
    
    for x in response["data"]:
        entry = getDiningSerialization(x["attributes"])

        try:
            vcard = entry.serialize()
        except:
            vcard = entry.serialize()

        #print vcard
        vcfFile.write(vcard)
    
        #print entry.serialize()
        print "\n\n"
    
    vcfFile.close()

# Read configuration file in JSON format
config_data_file = open('configuration.json')
config_data      = json.load(config_data_file)

base_url         = config_data["hostname"] + config_data["version"] + config_data["api"]
access_token_url = base_url + config_data["token_endpoint"]

access_token_response = getAccessToken(access_token_url, config_data["client_id"], config_data["client_secret"]);

access_token  = access_token_response["access_token"]
locations_url = base_url + config_data["locations_endpoint"]
params        = {"type": "dining"}

# Process Dining Data
response = getLocations(locations_url, access_token, params)
writeVcardFile('dininglocations.vcf', response)

# Process Building Data
params["type"] = "building"
params["campus"] = "corvallis"
response = getLocations(locations_url, access_token, params)
writeVcardFile('buildings.vcf', response)
