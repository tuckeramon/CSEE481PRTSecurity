import requests
from Communication.WebRequesterConfig import PRT_URL_FRONTEND_LOCALTEST, PRT_URL_FRONTEND_WEBSERVER

class WebRequester:
    """
    Represents a connection to a web server
    """
    def __init__(self, server_url: str):
        """
        Create an instance of a WebRequester
        :param server_url: the base server URL to be used in all requests
        """
        self.server_url = server_url

    def post_data(self, endpoint: str, data: dict):
        """
        Posts data to a specific endpoint on the base server
        :param endpoint: sub-path for the request (e.g. 'prt', 'plc/update')
        :param data: data to be sent in the POST request
        :return: Response object from requests.post call
        """
        url = f"{self.server_url}/{endpoint}"
        response = requests.post(url, json=data)
        return response

class SorterRequestResponseHandler(WebRequester):
    """
    Handles 'Request' type data:
    Fields:
        Sorter: 1 or 2
        TransactionID: 1-?
        Barcode: "XXXX" where X is 0-9
        Time: DateTime
        Destination: 1, 2, 3, or 4 (Being sorted)
    """

    def send_sorter_request_and_response(self, sorter: int, transaction_id: int, barcode: str, timestamp: str, destination: int,):
        """
        Send a request indicating a barcode has entered the sorter system
        :param sorter: Sorter ID
        :param transaction_id: Unique transaction identifier
        :param barcode: Scanned barcode
        :param timestamp: Time the request was received by the OPC server
        """
        data = {
            'sorter': sorter,
            'transaction_id': transaction_id,
            'barcode': barcode,
            'destination': destination
        }
        return self.post_data('plc/update', data)

class SorterReportHandler(WebRequester):
    """
    Handles 'Report' type data
    Fields:
        Sorter: 1 or 2
        Barcode: "XXXX" where X is 0-9
        Status: "XXXX" where X is 0 or 1 and represents Active, Good, Lost, Diverted
    """

    def send_report(self, sorter: int, barcode: str, active: bool, good: bool, lost: bool, diverted: bool):
        status = "1" if active else "0" + "1" if good else "0" + "1" if lost else "0" + 1 if diverted else "0"
        data = {
            'sorter': sorter,
            'barcode': barcode,
            'status': status
        }
        return self.post_data('plc/report', data)



