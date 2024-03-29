#Importing default python modules
import csv
import json
import os
import tkinter as tk
from tkinter import font, ttk
from datetime import datetime, timedelta

#Importing custom Pip modules
import requests
from bidict import bidict

serviceIterationNumber=0

#--------------------------------------------------------------------------------------------------------------------------------
def getStationInput():

    global homeSetTrue
    homeSetTrue = False

    def updateListbox(event):
        searchText = searchEntry.get().lower()
        listBox.delete(0, tk.END)
        for item in items:
            combinedString = f"{item[1].lower()} [{item[0].lower()}]"
            if searchText in combinedString:
                listBox.insert(tk.END, f"{item[0]} [{item[1]}]")

    def setHomeStation():
        selectedItem = listBox.get(listBox.curselection())
        with open("assets/homeStation.txt", "w") as home_file:
            home_file.write(selectedItem)

    def setStationInput(event=None):
        selectedItem = listBox.get(listBox.curselection())
        global stationInput 
        stationInput = selectedItem[:-6]
        if homeSetTrue == True:
            setHomeStation()
        root.destroy()

    def homeSetTrue():
        global homeSetTrue
        homeSetTrue = True

    # Create the main application window
    root = tk.Tk()
    root.title("RailPy Stations")
    root.geometry("+%d+%d" % (750, 450))
    root.geometry("300x400")

    # Create a label and an entry widget for searching
    searchLabel = tk.Label(root, text="Search:", font=('SFPro-Bold', 16))
    searchLabel.pack()

    searchEntry = tk.Entry(root)
    searchEntry.pack()

    # Read the CSV file and extract values from the first and second column
    csvFile = "assets/ukCrsCodes.csv"
    items = []

    try:
        with open(csvFile, "r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    items.append((row[1].title(), row[0]))
    except FileNotFoundError:
        print(f"The station CRS Code CSV file cannot be found at the default path ({csvFile}).\nPlease try reinstalling the application, or checking the file path.")

    # Check if there is a value in the homeStation.txt file
    homeStationFile = "assets/homeStation.txt"
    try:
        with open(homeStationFile, "r") as home_file:
            homeStation = home_file.read().strip()
            if homeStation:
                # Move the home station to the top of the list
                items.insert(0, (f"{homeStation} (Home)", ""))
    except FileNotFoundError:
        pass  # No need to handle the error if the file doesn't exist

    # Create a listbox and a scrollbar
    listBox = tk.Listbox(root, selectmode=tk.SINGLE, height=10, font=('SFPro-Light', 16))
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=listBox.yview)
    listBox.config(yscrollcommand=scrollbar.set)

    # Populate the listbox with items
    for item in items:
        listBox.insert(tk.END, f"{item[0]} [{item[1]}]")

    # Center the listbox in the window
    listBox.pack(side="top", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Bind the search entry to the updateListbox function when text changes
    searchEntry.bind("<KeyRelease>", updateListbox)

    # Create a variable to store the selected station
    stationInput = ""

    # Create a frame to hold the "Set as Home" checkbox
    frame = tk.Frame(root)
    frame.pack()

    # Create a "Set as Home" checkbox
    setHomeCheckbox = tk.Checkbutton(frame, text="Set as Home", font=('SFPro-Heavy', 12), command=homeSetTrue)
    setHomeCheckbox.pack(side="left")

    # Create a "Confirm Selection" button
    confirmButton = tk.Button(frame, text="Confirm Selection", font=('SFPro-Heavy', 14), command=setStationInput)
    confirmButton.pack(side="left")
    listBox.bind("<Double-1>", setStationInput)

    # Start the Tkinter main loop
    root.mainloop()
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
    window.geometry("1500x600")
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
stationCode = 'null'
while stationCode not in crsStationDict:

    # Create a Tkinter input dialog to get the station input
    getStationInput()
    
    #Establishing the CRS code for entered station by interpretting the input
    try:
        stationCode = crsStationDict.inverse[stationInput.upper()]
    except:
        stationCode = stationInput.upper()

#Establishing the name of the entered station by comparing the CRS Code to a dictionary
stationName=crsStationDict[stationCode].title()

#--------------------------------------------------------------------------------------------------------------------------------

#Retrieving the JSON data from the API using 'requests.get' and parsing the data so it can be used as a dictionary.
def getStationData(stationCode, searchTime):
    return json.loads(requests.get(f'http://api.rtt.io/api/v1/json/search/{stationCode}/{searchTime}', auth=apiKey).text)
searchTime = datetime.now().strftime("%Y/%m/%d/%H%M")
rttStationData = getStationData(stationCode, searchTime)

#rttStationData = json.loads(requests.get(f'http://api.rtt.io/api/v1/json/search/{stationCode}', auth=apiKey).text)

def searchStationServices(stationCode,searchTime):
    rttStationData = getStationData(stationCode, searchTime)

    global serviceUidList,serviceDateList,serviceTypeList,railOperatorList,destinationNameList,arrivalTimeList,platformNoList,scheduledDepartureList,realTimeDepartureList,serviceTypeConversion
    #Using the retrieved data, the first service's basic info is established. (UID, Run Date & Destination, etc.)
    serviceUidList=[]; serviceDateList=[]; serviceTypeList=[]; railOperatorList=[]; destinationNameList=[]; arrivalTimeList=[]; platformNoList=[]; scheduledDepartureList=[]; realTimeDepartureList=[]
    tempDepartureTime = (int(searchTime[-4:-2]) * 3599 + int(searchTime[-2:]) * 60)
    j=0
    while tempDepartureTime < (int(searchTime[-4:-2]) * 3600 + int(searchTime[-2:]) * 60):
        try:
            tempDepartureTime = (rttStationData['services'][j]['locationDetail']['gbttBookedDeparture'])
            tempDepartureTime = int(tempDepartureTime[:2]) * 3600 + int(tempDepartureTime[2:]) * 60
            j+=1
        except:
            #Printing and Displaying an error message if no services are found.
            #To Do - implement a feature to keep searching an hour later until a service is found or the day ends.
                #Keep searching for services i hours ahead until midnight is hit or a service is found.
            for i in range(1,(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1) - datetime.now()).seconds // 3600):
                itterativeSearchTime = (datetime.now()+timedelta(hours=i)).strftime("%Y/%m/%d/%H%M")
                rttStationData = getStationData(stationCode, itterativeSearchTime)
                print(i)
            print(f"\nThere are no services calling at {stationName} ({stationCode}) for a while... Check back later!\n")
            dotMatrixWindow(f"\nThere are no services calling at {stationName} ({stationCode}) for a while..."," Check back later!")
            quit()

    serviceCountStart = j-1; serviceCountStop = j+6
    serviceTypeConversion=bidict({'train':'rail',"bus":"rail replacement bus","ship":"ferry"})

    for i in range(serviceCountStart,serviceCountStop):
        try:
            serviceUidList.append(rttStationData['services'][i]['serviceUid'])
            serviceDateList.append(rttStationData['services'][i]['runDate'])
            serviceTypeList.append(serviceTypeConversion[rttStationData['services'][i]['serviceType']])
            destinationNameList.append(rttStationData['services'][i]['locationDetail']['destination'][0]['description'])
            railOperatorList.append(rttStationData['services'][i]['atocName'])
            if railOperatorList[-1] == 'ScotRail' and serviceTypeList[-1] == 'ship':
                railOperatorList[-1] = 'Caledonian MacBrayne'
            if railOperatorList[-1] == 'CrossCountry' and destinationNameList[-1] == 'Leeds Bradford Airport' or railOperatorList[-1] == 'CrossCountry' and stationName == 'Leeds Bradford Airport':
                railOperatorList[-1] = 'FLYER A1' 
            arrivalTimeList.append(rttStationData['services'][i]['locationDetail']['destination'][0]['publicTime'])
            try:
                platformNoList.append(rttStationData['services'][i]['locationDetail']['platform'])
            except:
                platformNoList.append(False)
            scheduledDepartureList.append(rttStationData['services'][i]['locationDetail']['gbttBookedDeparture'])
            try:
                realTimeDepartureList.append(rttStationData['services'][i]['locationDetail']['realtimeDeparture'])
            except:
                realTimeDepartureList.append(False)
        except:
            break
    #print(serviceUidList, serviceDateList, serviceTypeList, destinationNameList, railOperatorList, arrivalTimeList, platformNoList, scheduledDepartureList, realTimeDepartureList)

searchStationServices(stationCode,datetime.now().strftime("%Y/%m/%d/%H%M"))

#--------------------------------------------------------------------------------------------------------------------------------

def box_clicked(i):
    global serviceIterationNumber
    serviceIterationNumber = i
    infoWindow.destroy()

def nextPageSearch(firstTime=False):
    global infoWindow  # Declare infoWindow as a global variable
    infoWindow.destroy()  # Destroy the existing window

    if firstTime is False:
        if datetime.now().strftime("%H%M") > realTimeDepartureList[-1]:
            searchStationServices(stationCode, (datetime.now() + timedelta(days=1)).strftime(f"%Y/%m/%d/{realTimeDepartureList[-1]}"))
        else:
            searchStationServices(stationCode, datetime.now().strftime(f"%Y/%m/%d/{realTimeDepartureList[-1]}"))

    # Create a new Tkinter window
    infoWindow = tk.Tk()
    infoWindow.title("Service Information")
    infoWindow.configure(bg='black')
    infoWindow.geometry("+%d+%d" % (675, 400))

    for i in range(len(serviceUidList)):
        scheduledDeparture = scheduledDepartureList[i]
        realTimeDeparture = realTimeDepartureList[i]

        try:
            scheduledMinutes = int(scheduledDeparture[:2]) * 60 + int(scheduledDeparture[2:])
            realTimeMinutes = int(realTimeDeparture[:2]) * 60 + int(realTimeDeparture[2:])

            if realTimeMinutes == scheduledMinutes or realTimeMinutes == scheduledMinutes - 1 or realTimeMinutes == scheduledMinutes + 1439:
                delayInfo = "On Time"
            else:
                delayInfo = f"Expected {realTimeDeparture[:2]}:{realTimeDeparture[2:]}"
        except:
            delayInfo = "On Time"

        frame = tk.Frame(infoWindow, bg='black')
        frame.pack(pady=5, padx=10, fill=tk.X)

        label1 = tk.Label(frame, text=f"{scheduledDeparture[:2]}:{scheduledDeparture[2:]} to {destinationNameList[i]}", font='DotMatrix 22 bold', fg='orange', bg='black', anchor='w')
        label1.pack(fill=tk.X)

        # Add the new line to display platformNoList[i] unless it equals False
        if platformNoList[i] is not False:
            platform_label = tk.Label(frame, text=f"Platform {platformNoList[i]}", font='DotMatrix 18', fg='orange', bg='black', anchor='w')
            platform_label.pack(fill=tk.X)

        info_frame = tk.Frame(frame, bg='black')
        info_frame.pack(fill=tk.X)

        label2 = tk.Label(info_frame, text=delayInfo, font='DotMatrix 16', fg='orange', bg='black', anchor='w')
        label2.pack(side=tk.LEFT)

        box = tk.Button(info_frame, text="Select", command=lambda i=i: box_clicked(i), bg='black', fg='black')
        box.pack(side=tk.RIGHT)

        if i == 0:
            last_service_button = tk.Button(infoWindow, text="Next services...", command=nextPageSearch, bg='black', fg='black')
            last_service_button.pack(side=tk.BOTTOM)

    infoWindow.mainloop()

# Initialize the Tkinter window
infoWindow = tk.Tk()
infoWindow.title("Service Information")
infoWindow.configure(bg='black')
infoWindow.geometry("+%d+%d" % (675, 400))

# Call nextPageSearch to populate the initial window
nextPageSearch(True)

# Start the Tkinter main loop
infoWindow.mainloop()

#--------------------------------------------------------------------------------------------------------------------------------
#Using the basic info, the service-specific JSON data is retrieved from the API using 'requests.get' and parsed to be used as a dictionary
rttServiceData = json.loads(requests.get(f'http://api.rtt.io/api/v1/json/service/{serviceUidList[serviceIterationNumber]}/{serviceDateList[serviceIterationNumber].replace("-","/")}', auth=apiKey).text)
print(rttServiceData)
#--------------------------------------------------------------------------------------------------------------------------------

#Finds the entered location within the service's route and stores it as the var stationStopNumber
while nextStop != stationName:
    nextStop = rttServiceData['locations'][stopCounter]['description'].title()
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

try:
    scheduledMinutes = int(departureTime[:2]) * 60 + int(departureTime[2:])
    realTimeMinutes = int(expectedDeparture[:2]) * 60 + int(expectedDeparture[2:])

    if departureTime == False:
        departureTimeAnnouncement = f"{expectedDeparture[:2]}:{expectedDeparture[2:]}"

    if realTimeMinutes == scheduledMinutes or realTimeMinutes == scheduledMinutes - 1 or realTimeMinutes == scheduledMinutes + 1439:
        departureTimeAnnouncement = f" {departureTime[:2]}:{departureTime[2:]}"
    else:
        departureTimeAnnouncement = f", delayed {departureTime[:2]}:{departureTime[2:]} (expected {expectedDeparture[:2]}:{expectedDeparture[2:]})"
except:
    departureTimeAnnouncement = f"{expectedDeparture[:2]}:{expectedDeparture[2:]}"
#--------------------------------------------------------------------------------------------------------------------------------

if serviceIterationNumber == 0:
    serviceOrder = "next"
elif serviceIterationNumber == 1:
    serviceOrder = "2nd"
elif serviceIterationNumber == 2:
    serviceOrder = "3rd"
else:
    serviceOrder = str(serviceIterationNumber+1)+'th'

#--------------------------------------------------------------------------------------------------------------------------------

#Defines the initial announcement based on whether a Platform Number is findable or not.
if platformNoList[serviceIterationNumber] == False:
    finalAnnouncement = (f"\nThe {serviceOrder} {serviceTypeList[serviceIterationNumber]} service to depart {stationName} ({stationCode}) is the{departureTimeAnnouncement}, {railOperatorList[serviceIterationNumber]} service to {destinationNameList[serviceIterationNumber]}")
    print(finalAnnouncement)
else:
    finalAnnouncement = (f"\nThe {serviceOrder} {serviceTypeList[serviceIterationNumber]} service to depart {stationName} ({stationCode}) from Platform {platformNoList[serviceIterationNumber]} is the{departureTimeAnnouncement}, {railOperatorList[serviceIterationNumber]} service to {destinationNameList[serviceIterationNumber]}")
    print(finalAnnouncement)

#--------------------------------------------------------------------------------------------------------------------------------

#Creates the initial part of the 'calling at...' announcment
stopsAnnouncement = (f"This {serviceTypeConversion.inverse[serviceTypeList[serviceIterationNumber]]} will be calling at ")
print(f"This {serviceTypeConversion.inverse[serviceTypeList[serviceIterationNumber]]} will be calling at ",end='')

nextStop = rttServiceData['locations'][stopCounter-1]['description']
if nextStop == rttServiceData['destination'][0]['description']:
    nextStop = rttServiceData['locations'][stopCounter+1]['description']
while nextStop != destinationNameList[serviceIterationNumber]:
    try:
        nextStop = rttServiceData['locations'][stopCounter]['description']
        try:
            nextStopTime = rttServiceData['locations'][stopCounter]['realtimeArrival']
        except:
            nextStopTime = rttServiceData['locations'][stopCounter]['gbttBookedArrival']
        
        if nextStop == destinationNameList[serviceIterationNumber] and stopCounter > stationStopNumber+1:
            print(f"and {nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]})\n")
            stopsAnnouncement += (f"and {nextStop} ({nextStopTime[0:2]}:{nextStopTime[2:4]})\n")
        elif nextStop == destinationNameList[serviceIterationNumber] and stopCounter == stationStopNumber+1:
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
        rttServiceData = json.loads(requests.get(f'http://api.rtt.io/api/v1/json/service/{associatedUid}/{serviceDateList[serviceIterationNumber].replace("-","/")}', auth=apiKey).text)
        nextStop = rttServiceData['locations'][stopCounter]['description']
        oldStopCounter = stopCounter
        while nextStop != serviceChangeStop:
            nextStop = rttServiceData['locations'][stopCounter]['description']
            stopCounter+=1
            if nextStop == destinationNameList[serviceIterationNumber]:
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