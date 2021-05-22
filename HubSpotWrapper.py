import json
import requests


class HubSpotWrapper:
    def __init__(self):
        with open("apiKeys.json") as f:
            apis = json.loads(f.read())
            self.api_key_hubSpot = apis["hubspot"]

    def paramsToString(self, *params):
        csv = ""
        for x in params[0]:
            csv += "&property={p}".format(p=x)
        return csv

    def getAllContactsCSV(self, offset, *params):
        url = "http://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=500&hapikey=" + \
            self.api_key_hubSpot + "&vidOffset=" + \
            str(offset) + "&count=500" + self.paramsToString(params)
        json = requests.request("GET", url).json()
        if json["has-more"] == True:
            return self.contactToCSV(json) + self.getAllContactsCSV(json["vid-offset"], params)
        return self.contactToCSV(json)

    def contactToCSV(self, contact):
        csv = ""
        for c in contact["contacts"]:
            try:
                csv += "{id},".format(id=str(c["vid"]))
                for x in c["properties"]:
                    csv += "{p},".format(p=str(c["properties"][x]["value"]))
                csv = csv[:-1]
                csv += "\n"
            except Exception as e:
                None
        return csv

# EXAMPLE CODE

# hw = HubSpotWrapper()
# with open("contacts.csv", "w+") as f:
#    f.write(hw.getAllContactsCSV(0, "email", "firstname"))
