from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract as IBcontract
from threading import Thread
import queue
import datetime
import socket
import pickle
import sys

DEFAULT_HISTORIC_DATA_ID = 50
DEFAULT_GET_CONTRACT_ID = 43

FINISHED = object()
STARTED = object()
TIME_OUT = object()


class FinishableQueue(object):

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):

        contents_of_queue = []
        finished = False

        while not finished:
            try:
                current_element = self._queue.get(timeout = timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)

            except queue.Empty:
                finished = True
                self.status = TIME_OUT

        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT


class TestWrapper(EWrapper):

    def __init__(self):
        self._my_contract_details = {}
        self._my_historic_data_dict = {}

    def init_error(self):
        error_queue = queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if = not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        errormsg = 'IB error id %d error code %d string %s' % (id, errorCode, errorString)
        self._my_errors.put(errormsg)

    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue()

        return contract_details_queue

    def contractDetails(self, reqId, contractDetails):
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    def contractDetailsEnd(self, reqId):
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(FINISHED)

    def init_historicprices(self, tickerid):
        historic_data_queue = self._my_historic_data_dict[tickerid] = queue.Queue()

        return historic_data_queue

    def historicalData(self, tickerid, bar):

        bardata = (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
        historic_data_dict = self._my_historic_data_dict

        if tickerid not in historic_data_dict.keys():
            self.init_historicprices(tickerid)

        historic_data_dict[tickerid].put(bardata)

    def historicalDataEnd(self, tickerid, start:str, end:str):
        if tickerid not in self._my_historic_data_dict.keys():
            self.init_historicprices(tickerid)

        self._my_historic_data_dict[tickerid].put(FINISHED)

class TestClient(EClient):

    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def resolve_ib_contract(self, ibcontract, reqId=DEFAULT_GET_CONTRACT_ID):
        contract_details_queue = FinishableQueue(self.init_contractdetails(reqId))
        print("Getting full contract details from the server...")
        self.reqContractDetails(reqId, ibcontract)
        MAX_WAIT_SECONDS = 10
        new_contract_details = contract_details_queue.get(timeout=MAX_WAIT_SECONDS)
        while self.wrapper.is_error():
            print(self.get_error())

        if contract_details_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        if len(new_contract_details)== 0:
            print("Failed to get additional contract details: returning unresolved contract")
            return ibcontract

        if len(new_contract_details) > 1:
            print("got multiple contracts using first one")

        new_contract_details = new_contract_details[0]
        resolved_ibcontract = new_contract_details.contract
        return resolved_ibcontract

    def get_IB_historical_data(self, ibcontract, durationStr="7 Y", barSizeSetting="1 day", tickerid=DEFAULT_HISTORIC_DATA_ID):
        historic_data_queue = FinishableQueue(self.init_historicprices(tickerid))
        self.reqHistoricalData(tickerid, ibcontract, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"), durationStr, barSizeSetting, "TRADES", 1, 1, False, [])
        MAX_WAIT_SECONDS = 10
        print("Getting historical data from the server... could take %d seconds to complete" % MAX_WAIT_SECONDS)
        historic_data = historic_data_queue.get(timeout=MAX_WAIT_SECONDS)
        while self.wrapper.is_error():
            print(self.get_error())

        if historic_data_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behavior")

        self.cancelHistoricalData(tickerid)

        return historic_data


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipadress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipadress, portid, clientid)

        thread = Thread(target=self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()


app = TestApp('127.0.0.1', 7496, 1)

ibcontract = IBcontract()
ibcontract.secType = 'STK'
#ibcontract.lastTradeDateOrContractMonth = "201909"
ibcontract.symbol = "BEKB"
ibcontract.exchange = "BATEEN"

resolved_ibcontract = app.resolve_ib_contract(ibcontract)

historic_data = app.get_IB_historical_data(resolved_ibcontract)

print(historic_data)

app.disconnect



host = '192.168.0.103'
port = 50002
print(socket.getaddrinfo(host, port))
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mySocket.connect((host, port))

message = input(" -> ")

# while message != 'q':
#     mySocket.send(message.encode())
#     data = mySocket.recv(1024).decode()
#
#     print('Received from server: ' + data)
#
#     message = input(" -> ")

for item in historic_data:
    data = str(item) + '@'
    mySocket.send(data.encode())












