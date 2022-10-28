# assumption response from api looks like below:
#response template
'''
{
    response:
    {
        data:
        [
            {
                b0: []
                b1: []
                a9:"14324.70" // LTP  ##refering the link https://www.edelweiss.in/docs/streaming/
            }
        ]
    }
}
'''

#Dummy response
temp_response={
    "response":
    {
        "data":
        [
            {
                "a9":"14324.70",
                "b0":[
                    {
                    "z0":"0.00",
                    "z1":"0",
                    "z2":"0"
                    }
                ],
                "b1":[
                    {
                    "z0":"0.00",
                    "z1":"0",
                    "z2":"0"
                    }
                ],
                "z3":"-29"
            },
            {
                "a9":"9144.70",
                "b0":[
                    {
                    "z0":"0.00",
                    "z1":"0",
                    "z2":"0"
                    }
                ],
                "b1":[
                    {
                    "z0":"0.00",
                    "z1":"0",
                    "z2":"0"
                    }
                ],
                "z3":"-29"
            }
        ],
        "streaming_type":"quote3"
    }
}


from socket import *
import json
from time import sleep
import pandas as pd
import multiprocessing
from multiprocessing.managers import BaseManager
import warnings
warnings.filterwarnings("ignore")


#defining host and port
PORT = 9443
HOST = "tocstream.edelweiss.in"

#creating symbol from exchange token : {"symbol": //exchangetoken}
def create_token(exchange_token):
    return dict({"symbol": exchange_token})

#importing exchange tokens from instruments.csv using pandas and convert them into list of {"symbol": //exchangetoken} format
def get_token_set():
    file_data=pd.read_csv('instruments.csv')
    return list(map(create_token,file_data.exchangetoken))

#return first 1000 symbols from the file
def get_first_1000_token():
    return get_token_set()[:1000]

#creating request body from the list of symbols and the template given in the assignment and returning a dictionary
def request_body_creation(symbols):
    return dict(
        {
            "request":
                {
                    "streaming_type": "quote3",
                    "data":
                        {
                            "accType": "EQ",
                            "symbols": symbols
                        },
                    "formFactor": "M",
                    "appID": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHAiOjAsImZmIjoiVyIsImJkIjoid2ViLXBjIiwibmJmIjoxNjE2Mzk3MzMyLCJzcmMiOiJlbXRtdyIsImF2IjoiMS4wLjAiLCJhcHBpZCI6ImQ5MDM1NjFiZTFhYWUyYWY3M2RjZTJjOWJhODFiODViIiwiaXNzIjoiZW10IiwiZXhwIjoxNjE2NDM3ODAwLCJpYXQiOjE2MTYzOTc2MzJ9.iy2c_iialRdLSTLcHMHD0JM81DDUMHwGx9SrreVass8",
                    "response_format": "json",
                    "request_type": "subscribe"
                },
            "echo": {}
        }
    )

#creating a fully fledged request containing header and request body using the request dictionary returned by the above function
# type_of_request: get, put, post
# request: dictionary of request bodyformed using above function
def create_request(type_of_request,request):
    return f"""{str(type_of_request).upper()} / HTTP/1.1\r\nHost: {HOST}\r\nContent-type: application/json\r\nContent-length: {len(request)}\r\n\r\n{request}"""


# establishing socket connection and sending request to the server and return the response from the request
def send_request(request):
    response=""
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.connect((HOST,PORT))

        # sending encoded request
        sock.sendall(request.encode())

        # receiving response
        while True:
            recv = sock.recv(1024)
            #printing decoded response
            print(recv,recv.decode())
            if recv == b'':
                break
            response += recv.decode()

    return response


#this function is to intergrate all the steps from request creating to return response
def get_response(list_of_symbols):
    body=request_body_creation(list_of_symbols)
    body_json=json.dumps(body)
    request=create_request("post",body_json) #change type to get,put,post
    response=send_request(request)
    return response

# this define what process 1 should be doing according the assignment
def process1(shared_list):
    list_of_symbols=get_first_1000_token()

    #subscribing tokens using this request and getting response from the requst made to server
    ''' to get response from the servive un-comment the line below (1) and comment out the line (2)'''
    """ (1) """
    # response=get_response(list_of_symbols) # while using dummy response comment this line


    #### this is a dummy hard coded response according to the assumption made in the starting ####
    ''' to use this dummy response un-comment the line below (2) and comment the line (1) above '''
    """ (2) """
    response=json.loads(json.dumps(temp_response))
    

    #parsing the data and getting a list of token and LTPs and storing it in a shared_list which will be accessed by process 2
    for i,x in enumerate(response['response']['data']):
        temp={"Token":list_of_symbols[i]['symbol'],"LTP":float(x['a9'])}
        shared_list.append(temp)


# this define what process 1 should be doing according the assignment
def process2(shared_list):
    # waiting for 1 sec
    sleep(1)

    #printing all the tokens and their respective LTPs
    print(f"printing using process 2: {shared_list}")


if __name__ == "__main__":
    
    # defining the type of instance
    BaseManager.register('list', list)

    # create a new manager instance
    with BaseManager() as manager:

        #infinite loop for fetching and parsing the data using process 1 and printing using process 2 in every 1 second
        while 1:
            # create a shared set instance
            shared_list = manager.list()

            # creating 2 processes and calling functions process1 & process2
            p1 = multiprocessing.Process(target=process1,args=(shared_list,))
            p2 = multiprocessing.Process(target=process2,args=(shared_list,))

            # starting processes
            p1.start()
            p2.start()

            # waiting till processes are finished
            p1.join()
            p2.join()


