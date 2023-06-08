# AUTHOR: Jim K Moua
# LAST UPDATED 23/05/23

# This program reads PLC tag data every n seconds and makes respective API calls when conditions are met

import json
import time
import os
import requests
from pylogix import PLC

def getBatchID():
    """
    Make GET API call to localhost and return batch ID
    """
    url = 'http://localhost:88/api/v1/batches/activebatches'
    headers = { 'accept' : 'application/json' }
    try:
        getBatchInfo = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        # Log to file
        with open('error_log.txt', 'a+') as file:
            file.write(f'{time.strftime("%H:%M:%S")} {time.strftime("%d/%m/%Y")} - Failed to reach API server for GET.\n')
        return None
    else:
        activeBatch = getBatchInfo.json()

    return activeBatch[0]['id']



def postBatchBin(batchID):
    """
    Make POST API call to localhost
    """
    url = 'http://localhost:88/api/v1/batchbins'
    payload = { 'batchID' : batchID }
    headers = { 'accept' : 'application/json', 'Content-Type' : 'application/json-patch+json'}
    try:
        requests.post(url, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError:
        with open('error_log.txt', 'a+') as file:
            file.write(f'{time.strftime("%H:%M:%S")} {time.strftime("%d/%m/%Y")} - Failed to reach API server for POST.\n')
        return None



def getPLC_BinCount():
    """
    Returns 'BinCount_CurrentBatch' value from PLC
    """ 
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        ret = comm.Read('BinCount_CurrentBatch')
        return ret.Value



def getAccumulatedBins():
    """
    Returns 'Acc_Bins' value from PLC
    """
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        ret = comm.Read('Acc_Bins')
        return ret.Value



def writePLC_BatchChange(value):
    """
    Writes boolean to 'TAG_BatchChange' value in PLC
    """
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        comm.Write('TAG_BatchChange', value)



def batchIDisSame(batchID):
    """
    Returns true if batchID is equal to getBatchID()
    """
    if getBatchID() == batchID:
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



def checkBatchChangeInput():
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        ret = comm.Read('BatchChange_Latch')
        if ret.Value == 1:
            return True
        
    return False



def main():
    _batchInfo = {
        "batchID" : getBatchID(),
        "currentBinCount" : getPLC_BinCount()
    }

    batchChangeLogged = False
    while True:
        if (checkBatchChangeInput()) and (batchChangeLogged == False):
            with open('batchChangePushbuttonLog.txt', 'a+') as file:
                file.write(f'{time.strftime("%H:%M:%S")} {time.strftime("%d/%m/%Y")} - PLC received batch change input\n')
                batchChangeLogged = True

        TSbatchID = getBatchID()
        if TSbatchID != _batchInfo['batchID']:
            _batchInfo['batchID'] = TSbatchID
            buffer = getAccumulatedBins()
            with open('batchChangePushbuttonLog.txt', 'a+') as file:
                file.write(f'{time.strftime("%H:%M:%S")} {time.strftime("%d/%m/%Y")} - Accumulated Bins added: {buffer}\n')
            for x in range(buffer):
                postBatchBin(TSbatchID)
            writePLC_BatchChange(1)
            time.sleep(1)
            writePLC_BatchChange(0)
            time.sleep(10)
            _batchInfo['currentBinCount'] = getPLC_BinCount()
            batchChangeLogged = False

        PLC_BinCount = getPLC_BinCount()
        if PLC_BinCount != _batchInfo['currentBinCount'] and PLC_BinCount != 0:
            postBatchBin(TSbatchID)
            _batchInfo['currentBinCount'] = PLC_BinCount

        time.sleep(0.5)



if __name__ == "__main__":
    main()
