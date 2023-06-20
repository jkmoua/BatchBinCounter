import requests
import time
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

headings = ('Batch Name', 'Bins Expected', 'Bins Tipped', 'Total Bins Tipped', 'Start Time', 'Status')

def getBatches(test=False):
    """Make API call and return response in JSON form."""
    if test == True:
        with open('response.json') as file:
            return sorted(json.load(file), key=lambda x: x['name'])
        
    url = 'http://localhost:88/api/v1/batches/gui?limit=20&offset=0'
    headers = { 'accept' : 'application/json' }

    try:
        getBatches = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        # Log to file
        with open('error_log.txt', 'a+') as file:
            file.write(f'{tm.strftime("%H:%M:%S")} {tm.strftime("%d/%m/%Y")} - WebApp unable to reach TrueSort API.\n')
        return None
    else:
        return sorted(getBatches.json(), key=lambda x: x['name'])



def appendData(list, batch, batchResponse, batchTime, total_bins):
    """
    Append dict to argument list. batch is the batch element in batchResponse which is the 
    return value of the getBatches() method. batchTime is formatted time returned from formatDate().
    """
    if batchResponse[batch]["status"] == "StandBy":
        list.append({
                "name" : batchResponse[batch]["name"],
                "expectedBinCount" : batchResponse[batch]["expectedBinCount"],
                "tippedBinCount" : batchResponse[batch]["tippedBinCount"],
                "total_bins" : total_bins,
                "startDateUtc" : batchTime,
                "status" : "Standby"
        })
    else:
        list.append({
                    "name" : batchResponse[batch]["name"],
                    "expectedBinCount" : batchResponse[batch]["expectedBinCount"],
                    "tippedBinCount" : batchResponse[batch]["tippedBinCount"],
                    "total_bins" : total_bins,
                    "startDateUtc" : batchTime,
                    "status" : batchResponse[batch]["status"]
            })



def formatDate(batchTime):
    """Format the 'startDateUtc' values of the form ISO 8601 from getBatches()."""
    return str(datetime.strptime(batchTime, '%Y-%m-%dT%H:%M:%S.%fZ') - timedelta(hours=7)).split('.')[0]



def format_to_datetime(time):
    """Return the string argument as datetime object"""
    return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')



def buildData(batchResponse, hour_filter):
    """Filters out batches with start date older than the hour_filter."""
    if batchResponse == None:
        return None

    batchList = []
    total_bins = 0

    for batch in range(len(batchResponse)):
        total_bins = total_bins + int(batchResponse[batch]['tippedBinCount'])
        if batchResponse[batch]["status"] == 'StandBy':
            appendData(batchList, batch, batchResponse, batchResponse[batch]['startDateUtc'], total_bins)
        elif batchResponse[batch]["status"] == 'Active' or batchResponse[batch]["status"] == 'Paused':
            batchTime = formatDate(batchResponse[batch]['startDateUtc'])
            appendData(batchList, batch, batchResponse, batchTime, total_bins)
        elif batchResponse[batch]["status"] == 'Done':
            if batchResponse[batch]['startDateUtc'] == None:
                continue
            batchTime = formatDate(batchResponse[batch]['startDateUtc'])
            if hour_filter == 600:
                if datetime.now().time() > time(6, 0, 0):
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date(), time(6, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime, total_bins)
                else:
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date() - timedelta(days=1), time(6, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime, total_bins)
            elif hour_filter == 1800:
                if datetime.now().time() > time(18, 0, 0):
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date(), time(18, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime, total_bins)
                else:
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date() - timedelta(days=1), time(18, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime, total_bins)
            elif abs(format_to_datetime(batchTime) - datetime.now()) < timedelta(hours=hour_filter):
                appendData(batchList, batch, batchResponse, batchTime, total_bins)
            
    return batchList



@app.route("/batches", methods=['GET', 'POST'])
def table():
    """Calls buildData() and renders the list to a table in a flask app."""
    if request.method == 'POST':
        time_filter = int(request.form.get('dropdown'))
        data = buildData(getBatches(), time_filter)
        if data == None:
            return 'API unreachable. Refresh the web page once the API is running again.'
        return redirect(url_for('table', time_filter=time_filter))

    time_filter = request.args.get('time_filter')
    if time_filter == None:
        time_filter = 12
    else:
        time_filter = int(time_filter)
    data = buildData(getBatches(), time_filter)
    if data == None:
        return 'API unreachable. Refresh the web page once the API is running again.'
    return render_template("table.html", headings=headings, data=data, time_filter=time_filter)



if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=7000)
