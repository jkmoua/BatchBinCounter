# AUTHOR: Jim K Moua
# LAST UPDATED 19/05/23

# This program reads PLC tag data every n seconds and makes respective API calls when conditions are met

import json
import time
import requests
import os
from pylogix import PLC

_batchInfo = {
    "batchID" : 1,
    "currentBinCount" : None
}

def getBatchID():
    """
    Make GET API call to localhost and store batch ID into variable
    """
    global _batchInfo
    
    headers = { 'accept' : 'application/json' } 
    getBatchInfo = requests.get('http://localhost:88/api/v1/batches/activebatches', headers=headers)
    activeBatch = getBatchInfo.json()
    _batchInfo['batchID'] = activeBatch[0]['id']



def postBatchBin():
    """
    Make POST API call to localhost
    """
    global _batchInfo
    
    url = 'http://localhost:88/api/v1/batchbins'
    payload = { 'batchID' : _batchInfo['batchID'] }
    headers = { 'accept' : 'application/json', 'Content-Type' : 'application/json-patch+json'}
    requests.post(url, data=json.dumps(payload), headers=headers)



def readPLC_BinCount():
    """
    Read PLC tag and post API calls if conditions are met
    """
    global _batchInfo
    
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        ret = comm.Read('BinCount_CurrentBatch')
        if _batchInfo['currentBinCount'] != ret.Value and ret.Value != 0:
            _batchInfo['currentBinCount'] = ret.Value
            getBatchID()
            postBatchBin()
            return True
        
    return False



def writePLC_BatchChange():
    """
    Changes PLC 'TAG_BatchChange' boolean to True then back to false
    Handles the accumulated bin logic from PLC and makes necessary post calls
    """
    global _batchInfo

    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        ret = comm.Read('Acc_Bins')
        accumulatedBins = ret.Value
        for x in range(0, accumulatedBins):
            postBatchBin()
        comm.Write('TAG_BatchChange', 1)
        time.sleep(1)
        comm.Write('TAG_BatchChange', 0)
        time.sleep(30)
        _batchInfo['currentBinCount'] = comm.Read('BinCount_CurrentBatch').Value



def compareBatchID():
    """
    Compare and update stored batch ID to current batch ID from GET call
    """
    global _batchInfo

    headers = { 'accept' : 'application/json' }
    getBatchInfo = requests.get('http://localhost:88/api/v1/batches/activebatches', headers=headers)
    activeBatch = getBatchInfo.json()
    if _batchInfo['batchID'] != activeBatch[0]['id']:
        _batchInfo['batchID'] = activeBatch[0]['id']
        writePLC_BatchChange()
        return True

    return False



def loadJSONdata():
    """
    Load stored values from 'currentBinCount.json' file into local dictionary
    """
    global _batchInfo

    current_directory = os.getcwd()

    file_path = os.path.join(current_directory, 'currentBinCount.json')

    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            _batchInfo = json.load(json_file)
    else:
        with open(file_path, 'w') as json_file:
            json.dump(_batchInfo, json_file)
    
    return file_path



def main():
    json_file = loadJSONdata()

    while True:
        if readPLC_BinCount():
            with open(file_path, 'w') as json_file:
                json.dump(_batchInfo, json_file)
        if compareBatchID():
            with open(file_path, 'w') as json_file:
                json.dump(_batchInfo, json_file)
        time.sleep(0.5)



if __name__ == "__main__":
    main()
