import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template

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
    url = 'http://localhost:88/api/v1/batches'
    headers = { 'accept' : 'application/json' }

    try:
        getBatches = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        # Log to file
        with open('error_log.txt', 'a+') as file:
            file.write(f'{time.strftime("%H:%M:%S")} {time.strftime("%d/%m/%Y")} - Failed to reach API server for GET.\n')
        return None
    else:
        return getBatches.json()
    
def get_last_12_hours_batches(batchResponse):
    batchList = []

    for x in range(len(batchResponse)):
        if batchResponse[x]["status"] == 'StandBy':
            batchList.append({
                "name" : batchResponse[x]["name"],
                "expectedBinCount" : batchResponse[x]["expectedBinCount"],
                "tippedBinCount" : batchResponse[x]["tippedBinCount"],
                "startDateUtc" : batchTime,
                "status" : batchResponse[x]["status"]
                })
        
        if batchResponse[x]['startDateUtc'] == None:
            continue
        formattedDate = batchResponse[x]['startDateUtc'].split('.')[0]
        formattedDate = formattedDate.split('Z')[0]
        batchTime = datetime.strptime(formattedDate, '%Y-%m-%dT%H:%M:%S')
        if abs(batchTime - datetime.now()) < timedelta(hours=12):
            batchList.append({
                "name" : batchResponse[x]["name"],
                "expectedBinCount" : batchResponse[x]["expectedBinCount"],
                "tippedBinCount" : batchResponse[x]["tippedBinCount"],
                "startDateUtc" : batchTime,
                "status" : batchResponse[x]["status"]
                })
            
    return batchList

def main():
    batchList = get_last_12_hours_batches(getBatches())

@app.route("/batches")
def table():
    return render_template("table.html", headings=headings, data=get_last_12_hours_batches(getBatches()))

if __name__ == "__main__":
    app.run(debug=True, port=7000)
