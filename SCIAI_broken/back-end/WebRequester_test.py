from Communication.WebRequester import SorterReportHandler, SorterRequestResponseHandler
from Communication.WebRequesterConfig import PRT_URL_FRONTEND_LOCALTEST


def main():
    req_res_handler = SorterRequestResponseHandler(PRT_URL_FRONTEND_LOCALTEST)
    #report_handler = SorterReportHandler(PRT_URL_FRONTEND_LOCALTEST)
    req_res_handler.send_sorter_request_and_response(1, 1, 1, "23", 3)
    #report_handler.send_report(1, 1, True, True, False, False)

if __name__ == "__main__":
    main()