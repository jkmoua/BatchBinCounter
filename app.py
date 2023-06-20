import requests
import time
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

headings = ('Batch Name', 'Bins Expected', 'Bins Tipped', 'Start Time', 'Status')
data = (
    ('Batch 1', 100, 99, '4:51 AM'),
    ('Batch 2', 10, 10, '6:47 AM'),
    ('Batch 3', 204, 205, '7:22 AM'),
    ('Batch 4', 190, 190, '10:22 AM'),
    ('Batch 5', 19, 5, '11:22 AM')
)

def getBatches():
    """Make API call and return response in JSON form."""
    url = 'http://localhost:88/api/v1/batches/gui?limit=20&offset=0'
    headers = { 'accept' : 'application/json' }

    try:
        getBatches = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        # Log to file
        with open('error_log.txt', 'a+') as file:
            file.write(f'{time.strftime("%H:%M:%S")} {time.strftime("%d/%m/%Y")} - WebApp unable to reach TrueSort API.\n')
        return None
    else:
        return getBatches.json()



def appendData(list, iter, batchResponse, batchTime):
    """
    Append dict to argument list. iter is the batch element in batchResponse which is the 
    return value of the getBatches() method. batchTime is formatted time returned from formatDate().
    """
    list.append({
                "name" : batchResponse[iter]["name"],
                "expectedBinCount" : batchResponse[iter]["expectedBinCount"],
                "tippedBinCount" : batchResponse[iter]["tippedBinCount"],
                "startDateUtc" : batchTime,
                "status" : batchResponse[iter]["status"]
        })



def formatDate(batchTime):
    """Format the 'startDateUtc' values of the form ISO 8601 from getBatches()."""
    #formattedDate = batchTime.split('.')[0]
    #formattedDate = formattedDate.split('Z')[0]
    return str(datetime.strptime(batchTime, '%Y-%m-%dT%H:%M:%S.%fZ') - timedelta(hours=7)).split('.')[0]



def format_to_datetime(time):
    return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')



def buildData(batchResponse, hour_filter):
    """Filters out batches with start date older than the hour_filter."""
    if batchResponse == None:
        return None

    batchList = []

    for batch in range(len(batchResponse)):
        if batchResponse[batch]["status"] == 'StandBy':
            appendData(batchList, batch, batchResponse, batchResponse[batch]['startDateUtc'])
        elif batchResponse[batch]["status"] == 'Active' or batchResponse[batch]["status"] == 'Paused':
            batchTime = formatDate(batchResponse[batch]['startDateUtc'])
            appendData(batchList, batch, batchResponse, batchTime)
        elif batchResponse[batch]["status"] == 'Done':
            batchTime = formatDate(batchResponse[batch]['startDateUtc'])
            if hour_filter == 600:
                if datetime.now().time() > time(6, 0, 0):
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date(), time(6, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime)
                else:
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date() - timedelta(days=1), time(6, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime)
            elif hour_filter == 1800:
                if datetime.now().time() > time(18, 0, 0):
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date(), time(18, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime)
                else:
                    if format_to_datetime(batchTime) > datetime.combine(datetime.now().date() - timedelta(days=1), time(18, 0, 0)):
                        appendData(batchList, batch, batchResponse, batchTime)
            elif abs(format_to_datetime(batchTime) - datetime.now()) < timedelta(hours=hour_filter):
                appendData(batchList, batch, batchResponse, batchTime)
            
    return batchList



@app.route("/batches", methods=['GET', 'POST'])
def table():
    """Calls buildData() and renders the list to a table in a flask app."""
    selected_option = request.form.get('dropdown')
    if selected_option == None:
        selected_option = 12
    if request.method == 'POST':
        selected_option = int(request.form.get('dropdown'))
        data = buildData(getBatches(), selected_option)
        if data == None:
            return 'API unreachable. Refresh the web page once the API is running again.'
        #return render_template("table.html", headings=headings, data=data, selected_option=selected_option)
        return redirect(url_for('table'))

    data = buildData(getBatches(), selected_option)
    if data == None:
        return 'API unreachable. Refresh the web page once the API is running again.'
    return render_template("table.html", headings=headings, data=data, selected_option=selected_option)



if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=7000)
