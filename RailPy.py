#Importing default python modules
import csv
import json
import os
import tkinter as tk
from tkinter import font

#Importing custom Pip modules
import requests
from bidict import bidict

#--------------------------------------------------------------------------------------------------------------------------------

#Importing the API Key(s) from an external file (~/assets/apiKeys.json)
apiKeyFilePath="assets/apiKeys.json"

if not os.path.exists(apiKeyFilePath):

    #Asking the user for their API keys.
    print("No API credentials were found at the default path. Please enter your information.")
    print("These details can be found by logging in at https://api.rtt.io")
    apiUsername = input("Enter your API username (i.e. rttapi_username):  ")
    apiAuthKey = input("Enter your API password (NOT your login password):  ")
    apiKey = apiUsername,apiAuthKey

    #Creating a dictionary with the API credentials.
    apiCredentials = {
        "apiUsername": apiUsername,
        "apiAuthKey": apiAuthKey,
    }

    #Dumping the dictionary to the json file
    with open(apiKeyFilePath, "w") as file:
        json.dump(apiCredentials, file)

else:
    with open(apiKeyFilePath, "r") as file:
        apiCredentials = json.load(file)

    #Retrieving the API key from the credentials
    apiKey = (apiCredentials.get("apiUsername"), apiCredentials.get("apiAuthKey"))

    if not apiKey:
        print("Error: API key not found in the JSON file.")
        print("Try deleting the file and re-running this program.")

#--------------------------------------------------------------------------------------------------------------------------------

#Defining variables with null values
nextStop = ''
stopCounter = 0

#--------------------------------------------------------------------------------------------------------------------------------

#Tkinter Sub-Program for the Dot-Matrix Style Window
def dotMatrixWindow(finalAnnouncement,stopsAnnouncement):

    #Setting up the Window Params
    window = tk.Tk()
    window.title("RailPy")
    window.geometry("1500x500")
    window.configure(bg="black")

    #Creating the Main Label
    dotMatrixFont = font.Font(family="DotMatrix", size=42)
    announcementLabel = tk.Label(window, text=finalAnnouncement, font=dotMatrixFont, fg="orange", bg="black", wraplength=1375)
    announcementLabel.pack(pady=50)

    #Creating the Secondary Label
    stopsAnnouncementLabel = tk.Label(window, text=stopsAnnouncement, font=dotMatrixFont, fg="orange", bg="black", wraplength=1375)
    stopsAnnouncementLabel.pack()

    window.mainloop()

#--------------------------------------------------------------------------------------------------------------------------------

#Creating a Bidirectional HashMap from CSV using BiDict
with open("assets/ukCrsCodes.csv") as file:
    crsStationDict = bidict(dict(csv.reader(file, skipinitialspace=True)))

#--------------------------------------------------------------------------------------------------------------------------------

#Getting a station input from the user
stationInput=input("Enter a Station Name or its CRS code:  ")
    
#Establishing the CRS code for entered station by interpretting the input
try:
    stationCode = crsStationDict.inverse[stationInput.upper()]
except:
    stationCode = stationInput.upper()

#Establishing the name of the entered station by comparing the CRS Code to a dictionary
stationName=crsStationDict[stationCode].title()

#--------------------------------------------------------------------------------------------------------------------------------

#Retrieving the JSON data from the API using 'requests.get' and parsing the data so it can be used as a dictionary.
rttStationData = json.loads(requests.get(f'http://api.rtt.io/api/v1/json/search/{stationCode}', auth=apiKey).text)

#Printing and Displaying an error message if no services are found.
if rttStationData['services'] == None:
    print(f"\nThere are no services departing from {stationName} for a while... Check back later!\n")
    dotMatrixWindow(f"\nThere are no services departing from {stationName} for a while..."," Check back later!")
    quit()

#Using the retrieved data, the first service's basic info is established. (UID, Run Date & Destination, etc.)
serviceUid = rttStationData['services'][0]['serviceUid'] 
serviceDate = rttStationData['services'][0]['runDate']
serviceType = rttStationData['services'][0]['serviceType']
railOperator = rttStationData['services'][0]['atocName']
destinationName = rttStationData['services'][0]['locationDetail']['destination'][0]['description']
arrivalTime = rttStationData['services'][0]['locationDetail']['destination'][0]['publicTime']

#Establishes departure platform (if applicable)
try:
    platformNo = rttStationData['services'][0]['locationDetail']['platform']
except:
    platformNo = False

#Fixes an error with CalMac ferries appearing as ScotRail services
if railOperator == 'ScotRail' and serviceType == 'ship':
    railOperator = 'Caledonian MacBrayne'

#Find the adjective from of the service type
serviceTypeConversion={'train':'rail',"bus":"rail replacement bus","ship":"ferry"}
serviceTypeAdjective = serviceTypeConversion[serviceType]

#--------------------------------------------------------------------------------------------------------------------------------

#Using the basic info, the service-specific JSON data is retrieved from the API using 'requests.get' and parsed to be used as a dictionary
rttServiceData = json.loads(requests.get(f'http://api.rtt.io/api/v1/json/service/{serviceUid}/{serviceDate.replace("-","/")}', auth=apiKey).text)

#--------------------------------------------------------------------------------------------------------------------------------

#Finds the entered location within the service's route and stores it as the var stationStopNumber
while nextStop != stationName:
    nextStop = rttServiceData['locations'][stopCounter]['description']
    stopCounter+=1

stationStopNumber = stopCounter-1

#--------------------------------------------------------------------------------------------------------------------------------

#Finds the scheduled and expected (if available) departure time for the service from the entered station
departureTime = rttServiceData['locations'][stationStopNumber]['gbttBookedDeparture']
try:
    expectedDeparture = rttServiceData['locations'][stationStopNumber]['realtimeDeparture']
except:
    expectedDeparture = departureTime

#Establishes if the services is delayed, and alters the time announcement to include the delay if applicable
if expectedDeparture != departureTime:
    departureTimeAnnouncement = f", delayed, {departureTime[0:2]}:{departureTime[2:4]} (expected {expectedDeparture[0:2]}:{expectedDeparture[2:4]})"
else:
    departureTimeAnnouncement = f" {departureTime[0:2]}:{departureTime[2:4]}"

#--------------------------------------------------------------------------------------------------------------------------------

#Defines the initial announcement based on whether a Platform Number is findable or not.
if platformNo == False:
    finalAnnouncement = (f"\nThe next {serviceTypeAdjective} service to depart {stationName} ({stationCode}) is the{departureTimeAnnouncement}, {railOperator} service to {destinationName}")
    print(finalAnnouncement)
else:
    finalAnnouncement = (f"\nThe next {serviceTypeAdjective} service to depart {stationName} ({stationCode}) from Platform {platformNo} is the{departureTimeAnnouncement}, {railOperator} service to {destinationName}")
    print(finalAnnouncement)

#--------------------------------------------------------------------------------------------------------------------------------

#Creates the initial part of the 'calling at...' announcment
stopsAnnouncement = (f"This {serviceType} will be calling at ")
print(f"This {serviceType} will be calling at ",end='')

nextStop = rttServiceData['locations'][stopCounter-1]['description']
if nextStop == rttServiceData['destination'][0]['description']:
    nextStop = rttServiceData['locations'][stopCounter+1]['description']
while nextStop != destinationName:
    try:
        nextStop = rttServiceData['locations'][stopCounter]['description']
        try:
            nextStopTime = rttServiceData['locations'][stopCounter]['realtimeArrival']
        except:
            nextStopTime = rttServiceData['locations'][stopCounter]['gbttBookedArrival']
        
        if nextStop == destinationName and stopCounter > stationStopNumber+1:
            print(f"and {nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]})\n")
            stopsAnnouncement += (f"and {nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]})\n")
        elif nextStop == destinationName and stopCounter == stationStopNumber+1:
            print(f"{nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]}) only\n")
            stopsAnnouncement += (f"{nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]}) only\n")
        else:
            print(f"{nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]}), ",end='')
            stopsAnnouncement += (f"{nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]}), ")
        stopCounter+=1
    #Finds the related UID in situations when the services changes UID before the terminus (e.g. Poole -> Waterloo merges at Bournemouth)
    except:
        serviceChangeStop = rttServiceData['locations'][stopCounter-1]['description']
        print(serviceChangeStop)
        associatedUid = rttServiceData['locations'][stopCounter-1]['associations'][0]['associatedUid']
        associatedDate = rttServiceData['locations'][stopCounter-1]['associations'][0]['associatedRunDate']
        rttServiceData = json.loads(requests.get(f'http://api.rtt.io/api/v1/json/service/{associatedUid}/{serviceDate.replace("-","/")}', auth=apiKey).text)
        nextStop = rttServiceData['locations'][stopCounter]['description']
        oldStopCounter = stopCounter
        while nextStop != serviceChangeStop:
            nextStop = rttServiceData['locations'][stopCounter]['description']
            stopCounter+=1
            if nextStop == destinationName:
                stopCounter = oldStopCounter

#Runs the Tkinter Sub-Program to display the announcements in the DotMatrix style
dotMatrixWindow(finalAnnouncement,stopsAnnouncement)

'''
NOTES
-----

RTTServiceData:

{
    'serviceUid': 'Y40572',
    'runDate': '2023-05-18',
    'serviceType': 'train',
    'isPassenger': True,
    'trainIdentity': '2V57',
    'powerType': 'EMU',
    'trainClass': 'S',
    'atocCode': 'NT',
    'atocName': 'Northern',
    'performanceMonitored': True,
    'origin': [{'tiploc': 'ILKLEY', 'description': 'Ilkley', 'workingTime': '184000', 'publicTime': '1840'}],
    'destination': [{'tiploc': 'LEEDS', 'description': 'Leeds', 'workingTime': '191100', 'publicTime': '1912'}],
    'locations': [{
        'realtimeActivated': True, 'tiploc': 'ILKLEY', 'crs': 'ILK', 'description': 'Ilkley', 'gbttBookedDeparture': '1840', 'origin': [{
            'tiploc': 'ILKLEY', 'description': 'Ilkley', 'workingTime': '184000', 'publicTime': '1840'}],
            'destination': [{'tiploc': 'LEEDS', 'description': 'Leeds', 'workingTime': '191100', 'publicTime': '1912'}],
            'isCall': True,
            'isPublicCall': True,
            'realtimeDeparture':'1840',
            'realtimeDepartureActual': False,
            'platform': '2',
            'platformConfirmed': False,
            'platformChanged': False,
            'displayAs': 'ORIGIN',
            'associations': [{'type': 'next', 'associatedUid': 'Y40570', 'associatedRunDate': '2023-05-18'}]},
        {'realtimeActivated': True, 'tiploc': 'BNRHYDN', 'crs': 'BEY', 'description': 'Ben Rhydding', 'gbttBookedArrival': '1842', 'gbttBookedDeparture': '1842', 'origin': [{
            'tiploc': 'ILKLEY',
            'description': 'Ilkley',
            'workingTime': '184000',
            'publicTime': '1840'}],
            'destination': [{'tiploc': 'LEEDS',
            'description': 'Leeds', 'workingTime':
            '191100', 'publicTime': '1912'}],'
            'isCall': True,
            'isPublicCall': True,
            'realtimeArrival': '1842',
            'realtimeArrivalActual': False,
            'realtimeDeparture': '1842',
            'realtimeDepartureActual': False,
            'platform': '2',
            'platformConfirmed': False,
            'platformChanged': False,
            'displayAs': 'CALL'}, 
        {'realtimeActivated': True, 'tiploc': 'BURLYIW', 'crs': 'BUW', 'description': 'Burley-in-Wharfedale', 'gbttBookedArrival': '1847', 'gbttBookedDeparture': '1847', 'origin': [{'tiploc': 'ILKLEY', 'description': 'Ilkley', 'workingTime': '184000', 'publicTime': '1840'}], 'destination': [{'tiploc': 'LEEDS', 'description': 'Leeds', 'workingTime': '191100', 'publicTime': '1912'}], 'isCall': True, 'isPublicCall': True, 'realtimeArrival': '1846', 'realtimeArrivalActual': False, 'realtimeDeparture': '1847', 'realtimeDepartureActual': False, 'platform': '2', 'platformConfirmed': False, 'platformChanged': False, 'displayAs': 'CALL'}, {'realtimeActivated': True, 'tiploc': 'MENSTON', 'crs': 'MNN', 'description': 'Menston', 'gbttBookedArrival': '1850', 'gbttBookedDeparture': '1851', 'origin': [{'tiploc': 'ILKLEY', 'description': 'Ilkley', 'workingTime': '184000', 'publicTime': '1840'}], 'destination': [{'tiploc': 'LEEDS', 'description': 'Leeds', 'workingTime': '191100', 'publicTime': '1912'}], 'isCall': True, 'isPublicCall': True, 'realtimeArrival': '1850', 'realtimeArrivalActual': False, 'realtimeDeparture': '1851', 'realtimeDepartureActual': False, 'platform': '2', 'platformConfirmed': False, 'platformChanged': False, 'displayAs': 'CALL'}, {'realtimeActivated': True, 'tiploc': 'GUISELY', 'crs': 'GSY', 'description': 'Guiseley', 'gbttBookedArrival': '1854', 'gbttBookedDeparture': '1854', 'origin': [{'tiploc': 'ILKLEY', 'description': 'Ilkley', 'workingTime': '184000', 'publicTime': '1840'}], 'destination': [{'tiploc': 'LEEDS', 'description': 'Leeds', 'workingTime': '191100', 'publicTime': '1912'}], 'isCall': True, 'isPublicCall': True, 'realtimeArrival': '1853', 'realtimeArrivalActual': False, 'realtimeDeparture': '1854', 'realtimeDepartureActual': False, 'platform': '2', 'platformConfirmed': False, 'platformChanged': False, 'displayAs': 'CALL'}, {'realtimeActivated': True, 'tiploc': 'LEEDS', 'crs': 'LDS', 'description': 'Leeds', 'gbttBookedArrival': '1912', 'origin': [{'tiploc': 'ILKLEY', 'description': 'Ilkley', 'workingTime': '184000', 'publicTime': '1840'}], 'destination': [{'tiploc': 'LEEDS', 'description': 'Leeds', 'workingTime': '191100', 'publicTime': '1912'}], 'isCall': True, 'isPublicCall': True, 'realtimeArrival': '1911', 'realtimeArrivalActual': False, 'platform': '5C', 'platformConfirmed': False, 'platformChanged': False, 'displayAs': 'DESTINATION'}], 'realtimeActivated': True, 'runningIdentity': '2V57'}
        {'realtimeActivated': True, 'tiploc': 'BOMO', 'crs': 'BMH', 'description': 'Bournemouth', 'gbttBookedArrival': '1913', 'origin': [{'tiploc': 'POOLE', 'description': 'Poole', 'workingTime': '190000', 'publicTime': '1900'}], 'destination': [{'tiploc': 'WATRLMN', 'description': 'London Waterloo', 'workingTime': '212830', 'publicTime': '2129'}], 'isCall': True, 'isPublicCall': True, 'realtimeArrival': '1913', 'realtimeArrivalActual': False, 'platform': '2', 'platformConfirmed': False, 'platformChanged': False, 'displayAs': 'DESTINATION', 'associations': [{'type': 'join', 'associatedUid': 'L22366', 'associatedRunDate': '2023-05-18'}]}], 'realtimeActivated': True, 'runningIdentity': '2W72'}

        
Example of JSON Output from RTTStationData:

{
    "location":{"name":"Oban","crs":"OBN","tiploc":"OBAN","country":"gb","system":"nr"},
    "filter":null,
    "services":[
        {"locationDetail":{
                "tiploc":"OBAN",
                "crs":"OBN",
                "description":"Oban",
                "gbttBookedDeparture":"1715",
                "origin":[{"tiploc":"OBAN","description":"Oban","workingTime":"171500","publicTime":"1715"}],
                "destination":[{"tiploc":"LISMORE","description":"Lismore","workingTime":"181000","publicTime":"1810"}],
                "isCall":true,
                "isPublicCall":true,"displayAs":"ORIGIN"},
            "serviceUid":"C08242",
            "runDate":"2023-05-18",
            "trainIdentity":"0S00",
            "atocCode":"SR",
            "atocName":"ScotRail",
            "serviceType":"ship",
            "isPassenger":true},
        {"locationDetail":{
                "realtimeActivated":true,
                "tiploc":"OBAN",
                "crs":"OBN",
                "description":"Oban",
                "gbttBookedDeparture":"1811",
                "origin":[{"tiploc":"OBAN","description":"Oban","workingTime":"181100","publicTime":"1811"}],
                "destination":[{"tiploc":"GLGQHL","description":"Glasgow Queen Street","workingTime":"212500","publicTime":"2125"}],
                "isCall":true,
                "isPublicCall":true,
                "realtimeDeparture":"1811",
                "realtimeDepartureActual":false,
                "platform":"3",
                "platformConfirmed":false,
                "platformChanged":false,
                "displayAs":"ORIGIN"},
            "serviceUid":"G11073",
            "runDate":"2023-05-18",
            "trainIdentity":"1Y28",
            "runningIdentity":"1Y28",
            "atocCode":"SR",
            "atocName":"ScotRail",
            "serviceType":"train",
            "isPassenger":true},
        {"locationDetail":{
                "tiploc":"OBAN",
                "crs":"OBN",
                "description":"Oban",
                "gbttBookedDeparture":"2000",
                "origin":[{"tiploc":"OBAN","description":"Oban","workingTime":"200000","publicTime":"2000"}],
                "destination":[{"tiploc":"CRGURE","description":"Craignure","workingTime":"210000","publicTime":"2100"}],
                "isCall":true,
                "isPublicCall":true,
                "displayAs":"ORIGIN"},
            "serviceUid":"C19972",
            "runDate":"2023-05-18",
            "trainIdentity":"0S00",
            "atocCode":"SR",
            "atocName":"ScotRail",
            "serviceType":"ship",
            "isPassenger":true},
        {"locationDetail":{
                "realtimeActivated":true,
                "tiploc":"OBAN",
                "crs":"OBN",
                "description":"Oban",
                "gbttBookedDeparture":"2039",
                "origin":[{"tiploc":"OBAN","description":"Oban","workingTime":"203900","publicTime":"2039"}],
                "destination":[{"tiploc":"GLGQHL","description":"Glasgow Queen Street","workingTime":"233200","publicTime":"2332"}],
                "isCall":true,
                "isPublicCall":true,
                "realtimeDeparture":"2039",
                "realtimeDepartureActual":false,
                "platform":"3",
                "platformConfirmed":false,
                "platformChanged":false,
                "displayAs":"ORIGIN"},
            "serviceUid":"C53464",
            "runDate":"2023-05-18",
            "trainIdentity":"1Y32",
            "runningIdentity":"1Y32",
            "atocCode":"SR",
            "atocName":"ScotRail",
            "serviceType":"train",
            "isPassenger":true}]}

Maybe useful for generating announcements: https://github.com/davwheat/rail-announcements

To generate requirements.txt for sharing, use >>>pipreqs /path/to/project

'''