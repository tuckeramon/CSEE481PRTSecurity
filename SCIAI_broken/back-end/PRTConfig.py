
TAG_TO_READ = 'SORTER_1_REQUEST'

STATUS_BIT = '.END'

TAG_TO_WRITE = 'SORTER_1_RESPONSE'



CAR_DEST_MAP = {
   
}
"""
READING
DATA_TYPE:
96 Bytes long
First member string - double int - 4 Bytes -- length of string (don't need to really worry about)
82 Bytes after are ASCII characters 
Int with scanner number - 2 Bytes
Int with transaction ID - 2 Bytes
End bit -- double integer - 4 Bytes

WRITING BACK
DESTINATION: 'SORTER_1_RESPONSE'
Send back transaction ID to ensure correct communication -- + the destination -- written into data type:
4 Bytes wide
3 members: 
1: transaction id 
2: destination (single int) 
3: end (single int, 1)

AFTER SORTING:
'SORTED_1_REPORT'
96 Bytes
Barcode -- same as sorted car
Tracking flags: Active, Lost, Good, Diverted: Inner data type w/ 4 Booleans (1 byte wide each)
End bit - double integer - 4 Bytes
Do with data what I want
This bardcode went to X destination and Y is the reason
Start logging like: packages lost, not diverted because motor is working or dest not available etc
"""

BARCODE_DESTINATION_MAP = {
    #Barcode: {SorterNum: Destination},
    #PRT
    "0001": 1,
    "0002": 2,
    "0003": 3,
    "0004": 4,
    "0005": 1,
    "0006": 2,
    "0007": 3,
    "0008": 4,
    "0009": 1,
    "0010": 4,
    #Smart manufacturing
    "1001": 3,
    "1002": 3,
    "1003": 3,
    "1004": 3,
    "1005": 3,
    "1006": 3,
    "1007": 2,
    "1008": 2,
    "1009": 1,
    "1010": 1,
}

def prt_get_dest_route(physical_dest: int) -> dict:
    if physical_dest < 1 or physical_dest > 4:
        return None
    if physical_dest == 1:
        return {1: 3, 2: 2}  # { SorterNum: DestNum }
    elif physical_dest == 2:
        return {1: 3, 2: 1}
    elif physical_dest == 3:
        return {1: 1, 2: 3}
    elif physical_dest == 4:
        return {1: 2, 2: 3}



