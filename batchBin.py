# AUTHOR: Jim K Moua
# LAST UPDATED 18/05/23

# This program reads PLC tag data every second and makes respective API calls when conditions are met

import json
import time
import requests
from pylogix import PLC

_batchID = None
_currentBinCount = 0

def getBatchID():
    """
    Make GET API call to localhost and store batch ID into variable
    """
    global _batchID
    
    headers = { 'accept' : 'application/json' } 
    getBatchInfo = requests.get('http://localhost:88/api/v1/batches/activebatches', headers=headers)
    activeBatch = getBatchInfo.json()
    _batchID = activeBatch[0]['id']



def postBatchBin():
    """
    Make POST API call to localhost
    """
    global _batchID
    
    url = 'http://localhost:88/api/v1/batchbins'
    payload = { 'batchID' : _batchID }
    headers = { 'accept' : 'application/json', 'Content-Type' : 'application/json-patch+json'}
    requests.post(url, data=json.dumps(payload), headers=headers)



def readPLC_BinCount():
    """
    Read PLC tag and post API calls if conditions are met
    """
    global _currentBinCount
    
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        ret = comm.Read('BinCount_CurrentBatch')
        if _currentBinCount != ret.Value and ret.Value != 0:
            _currentBinCount = ret.Value
            getBatchID()
            postBatchBin()



def writePLC_BatchChange():
    """
    Change PLC 'TAG_BatchChange' boolean to True then back to false
    """
    with PLC() as comm:
        comm.Micro800 = True
        comm.IPAddress = '192.168.99.95'
        comm.Write('TAG_BatchChange', 1)
        time.sleep(2)
        comm.Write('TAG_BatchChange', 0)



def compareBatchID():
    """
    Compare and update stored batch ID to current batch ID from GET call
    """
    global _batchID
    
    headers = { 'accept' : 'application/json' }
    getBatchInfo = requests.get('http://localhost:88/api/v1/batches/activebatches', headers=headers)
    activeBatch = getBatchInfo.json()
    if _batchID != activeBatch[0]['id']:
        writePLC_BatchChange()
        _batchID = activeBatch[0]['id']



while True:
    readPLC_BinCount()
    compareBatchID()
    time.sleep(1)
