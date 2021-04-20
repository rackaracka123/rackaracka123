import requests
import os
import json

with open("apiKeys.json") as f:
    apis = json.loads(f.read())
    api_key_hubSpot = apis["hubspot"]
    api_key_mapbox = apis["mapbox"]
    api_key_helium_vision = apis["helium_vision"]

def logFailedPerson(email):
    print("Log fail: " + email)
    f = open("unsuccessfullPeople.txt", "a")
    f.write(email + "\n")
    f.close()

def getHostingStage():
    url = "http://api.hubapi.com/contacts/v1/lists/all/contacts/recent?hapikey=" + api_key_hubSpot + "&count=500&property=email&property=hosting_stage&property=floor_number___house&property=firstname&property=lastname"
    return requests.request("GET", url).json()

def getSignupDetails(formId):
    resp = requests.get("https://api.hubapi.com/form-integrations/v1/submissions/forms/" + formId + "?hapikey=" + api_key_hubSpot)
    return resp.json()
        
def translateAddressToLongLat(address):
    resp = requests.get("https://api.mapbox.com/geocoding/v5/mapbox.places/" + address + ".json?limit=30&access_token=" + api_key_mapbox)
    j = resp.json()
    
    lat = lng = street = city = state = country = postal_code = None

    #assume first result is correct
    for x in j["features"]:
        try:
            street = str(x["text"]) + " " + str(j["features"][0]["address"])
            lat = x["center"][0]
            lng = x["center"][1]


            for y in x["context"]:
                if "postcode" in y["id"]:
                    postal_code = str(y["text"])
                if "place" in y["id"]:
                    city = str(y["text"])
                if "country" in y["id"]:
                    country = str(y["text"])
                if "region" in y["id"]:
                    state = str(y["text"])
            if street not in address:
                continue
            return lat, lng, street, city, state, country, postal_code
        except Exception as e:
            None

def postNewHotspot(name, lat, lng, notes, street, city, state, country, postal_code):
    payload = """{
    "name": "{0}",
    "lat": "{1}",
    "lng": "{2}",
    "radius": 300,
    "elevation": 0,
    "notes": "{3}",
    "physical_address": {
        "street": "{4}",
        "street_2": null,
        "city": "{5}",
        "state": "{6}",
        "country": "{7}",
        "post_code": "{8}",
        "lat": "{1}",
        "lng": "{2}"
    }
}
""".replace("{\n", "{{\n").replace("}\n", "}}").format(name, lat, lng, notes, street, city, state, country, postal_code)

    os.system("""curl --silent --location --request POST 'https://api.helium.vision/v1/placement' \
--header 'Accept: application/json' \
--header 'Authorization: Bearer {0}' \
--header 'Content-Type: application/json' \
--header 'Cookie: __cfduid=de192a8ed2567a748b4e7e464a92286461617952587' \
--data-raw '""".format(api_key_helium_vision) + payload + "'" + " > /dev/null")

hostingStages = getHostingStage()
def findContactHostingStage(email):
    return [x for x in hostingStages["contacts"] if x["properties"]["email"]["value"] == email][0]
def formatContact(contact):
    contact = contact["properties"]
    return (contact["firstname"]["value"][0] + contact["lastname"]["value"][0], "hosting_stage:" + contact["hosting_stage"]["value"] + "," + 
    "email," + contact["email"]["value"] + ","
    "floor_number," + contact["floor_number___house"]["value"])

signups = getSignupDetails("5838c04f-fb15-4350-b822-b40ac8a212d4") #id för registrations formet
with open("checkpoint.txt", "w+") as f:
    emailToStopAt = f.read()

firstEmail = ""
for x in signups["results"]:
    try:
        if firstEmail == "":
            firstEmail = x["values"][2]["value"]
        if x["values"][2]["value"] == emailToStopAt:
            break

        lat, lng, street, city, state, country, postal_code = translateAddressToLongLat(x["values"][5]["value"] + " " +  x["values"][8]["value"])
        contact = findContactHostingStage(x["values"][2]["value"])

        if contact["properties"]["floor_number___house"] >= 4:
            None ## exempel på filtrering
            
        (name, notes) = formatContact(contact)
        postNewHotspot(name, lat, lng, notes, street, city, state, country, postal_code)
    except Exception as e:
        logFailedPerson(x["values"][2]["value"])

with open("checkpoint.txt", "w+") as f:
    f.write(firstEmail)