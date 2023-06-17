import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request

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
    list.append({
                "name" : batchResponse[iter]["name"],
                "expectedBinCount" : batchResponse[iter]["expectedBinCount"],
                "tippedBinCount" : batchResponse[iter]["tippedBinCount"],
                "startDateUtc" : batchTime,
                "status" : batchResponse[iter]["status"]
        })



def formatDate(batchTime):
    formattedDate = batchTime.split('.')[0]
    formattedDate = formattedDate.split('Z')[0]
    return datetime.strptime(formattedDate, '%Y-%m-%dT%H:%M:%S') - timedelta(hours=7)



def buildData(batchResponse, hour_filter):
    if batchResponse == None:
        return None

    batchList = []

    for x in range(len(batchResponse)):
        if batchResponse[x]["status"] == 'StandBy':
            appendData(batchList, x, batchResponse, batchResponse[x]['startDateUtc'])
        elif batchResponse[x]["status"] == 'Active' or batchResponse[x]["status"] == 'Paused':
            batchTime = formatDate(batchResponse[x]['startDateUtc'])
            appendData(batchList, x, batchResponse, batchTime)
        elif batchResponse[x]["status"] == 'Done':
            batchTime = formatDate(batchResponse[x]['startDateUtc'])
            if abs(batchTime - datetime.now()) < timedelta(hours=hour_filter):
                appendData(batchList, x, batchResponse, batchTime)
            
    return batchList



@app.route("/batches", methods=['GET', 'POST'])
def table():
    selected_option = request.form.get('dropdown')
    if selected_option == None:
        selected_option = 12
    if request.method == 'POST':
        selected_option = int(request.form.get('dropdown'))
        data = buildData(getBatches(), selected_option)
        if data == None:
            return 'API unreachable. Refresh the web page once the API is running again.'
        return render_template("table.html", headings=headings, data=data, selected_option=selected_option)

    data = buildData(getBatches(), selected_option)
    if data == None:
        return 'API unreachable. Refresh the web page once the API is running again.'
    return render_template("table.html", headings=headings, data=data, selected_option=selected_option)



if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=7000)
