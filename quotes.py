#!/usr/bin/env python

import os
import requests
import json
import redis

from flask import Flask 
from flask import request
from flask import jsonify

app = Flask(__name__, static_url_path = "")

@app.route('/hello')
def entry_point():
    return 'Hello World!'

@app.route('/')
def serve_main_page():
    return app.send_static_file('index.html')

# For development only 
@app.route('/shutdown')
def shutdown():
    print "Shutting down"
    shutdown_server()
    return "Shut down"

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    print "Server shut down."
    return

@app.route('/symbol/')
def handle_ytd_return_request():
    # api_key = get_user_specific_api_key()
    # if api_key == "None": 
        # print("Could not get api key. Required file 'tdinfo.json not found")
        # exit() 
    # YTD_return = get_ytd_return("AMZN", api_key)    
    # print YTD_return 
    return "Missing Symbol" 

@app.route('/symbol/<symbol>')
def handle_ytd_return_request_symbol(symbol):
    api_key = get_user_specific_api_key()
    if api_key == "None": 
        print("Could not get api key. Required file 'tdinfo.json not found")
        exit()    
    YTD_return = get_ytd_return(symbol.upper(), api_key)    
    # print symbol
    # print YTD_return 
    return str(YTD_return) 

@app.route('/positions')
def return_postions_as_json():
    positions_dict = make_positions_json()
    json_response = jsonify(positions_dict)
    return json_response

# get the position information from positions file, load a json object and return the object 
def make_positions_json(): 
    # symbol_list = []
    positions_file = "positions.json"

    if os.path.isfile(positions_file):         
        with open(positions_file,'r') as p:            
            positions = json.load(p)       
            # print positions       
            # for item in positions:       
                # symbol_list.append(positions[item]["symbol"])              
                # if use_redis_cache: 
                    #put_position_in_cache(item,positions[item])

    return (positions)   

def connect_to_redis():
    global r 
    r = redis.Redis(host='localhost')

def put_position_in_cache(position_key, position_dict):  
    r.hmset(position_key, position_dict)

    
# get the api key from the the required tdinfo.json file. 
def get_user_specific_api_key():
    filename = "tdinfo.json"
    encoded_apikey = "None"
    if os.path.isfile(filename): 
        with open(filename,'r') as f:
            tdinfo = json.load(f)            
            encoded_apikey = tdinfo["encoded_apikey"]

    return(encoded_apikey)

# get the position information from positions file 
def make_symbols_list(): 
    symbol_list = []
    positions_file = "positions.json"

    if os.path.isfile(positions_file):         
        with open(positions_file,'r') as p:            
            positions = json.load(p)             
            for item in positions:       
                symbol_list.append(positions[item]["symbol"])              
                if use_redis_cache: 
                    put_position_in_cache(item,positions[item])

    return(symbol_list)   



def get_end_of_year_price(symbol, encoded_apikey ):
    # startDate is milliseconds from epoch time (Jan 1, 1970). Value is 3:00 am EST Dec 29, 2017 -  1514534400000
    # endDate is milliseconds from epoch time (Jan 1, 1970). Value is 3:00 am EST Jan 2, 2017 -  1514880000000
    

      # startDate is milliseconds from epoch time (Jan 1, 1970). Value is 3:00 am EST Dec 29, 2018 -  1546070400000
      # endDate is milliseconds from epoch time (Jan 1, 1970). Value is 3:00 am EST Jan 2, 2019 -  1546416000000
    
    eoy_quote_data = {}      #end_of_year_quote dictionary    
    eoy_price = 1.00    

    # url = "https://api.tdameritrade.com/v1/marketdata/{}/pricehistory?apikey={}&periodType=month&period=1&frequencyType=daily&frequency=1&endDate=%201514880000000&startDate=1514534400000".format(symbol, encoded_apikey)    
    url = "https://api.tdameritrade.com/v1/marketdata/{}/pricehistory?apikey={}&periodType=month&period=1&frequencyType=daily&frequency=1&endDate=%201546416000000&startDate=1546070400000".format(symbol, encoded_apikey)    
   

    reply = requests.get(url)
    if reply.status_code != 200: 
        print "TD API failure. Error code {}. Error Message {}".format(reply.status_code, reply.text)
        exit()
    eoy_quote_data = reply.json() 
    # print eoy_quote_data
    
    if eoy_quote_data["empty"] == False: 
        # should only have one candle now that period only covers Dec 29, 2017
        # commenting out previous loop. Leaving for reference for now.
        # for candle in eoy_quote_data["candles"]:                   
            #eoy_price = candle["close"]            
            #return(eoy_price)
        eoy_price = eoy_quote_data["candles"][0]["close"]
        # print eoy_price                 
    else: 
        print ("No candles returned. YTD return for this position will not be accurate.")        
        eoy_price = 1.00   
    print eoy_price 
    return (eoy_price) 

def get_price(symbol,encoded_apikey):        
    quote_data = {} 
    current_price = 100.00
    
    url = "https://api.tdameritrade.com/v1/marketdata/{}/quotes?apikey={}".format(symbol, encoded_apikey)
    # print url 
    reply = requests.get(url) 
    # print reply
    # print reply.status_code    
    # print reply.text 
    if reply.status_code != 200: 
        print "TD API failure. Error code {}. Error Message {}".format(reply.status_code, reply.text)
        exit()
    if reply.text == "": 
        # print "TD API issue"
        exit() 

    quote_data = reply.json() 
    # print quote_data   
    current_price = quote_data[symbol]["lastPrice"]    
    print current_price
    return (current_price)
 
def calc_YTD_return(current, prev_year):    
    delta = float(current) - float(prev_year)    
    decimal = float(delta) / float(prev_year)
    
    return decimal


def get_ytd_return(ticker,apikey) :    
    global r # The Redis connection established earlier

    current_price_float = get_price(ticker, apikey)    
    current_price_round = round(current_price_float,2)
    
    prev_year_closing_price_float = get_end_of_year_price(ticker, apikey)    
    prev_year_closing_price_round =  round(prev_year_closing_price_float,2)
    
    YTD_price_change = (float(current_price_round) - float(prev_year_closing_price_round)) 

    YTD_return_float = calc_YTD_return(current_price_float, prev_year_closing_price_float)    
    YTD_percent = float(YTD_return_float * 100)  
    YTD_return = round(YTD_percent, 2)
    
    if use_redis_cache:         
        r.hmset(ticker, {"ytd_return": YTD_return}) # add the return to the position data cache (Redis)

    # print "The current price of %s is: %s  EOY price was: %s  Change for the year is %s  YTD return is %s"  % (ticker, current_price_round, prev_year_closing_price_round, YTD_price_change, YTD_return)
    print "%s  %7.2f" % (ticker.ljust(5), YTD_return) 

    return YTD_return
     
''' main '''
api_key = get_user_specific_api_key()
if api_key == "None": 
    print("Could not get api key. Required file 'tdinfo.json not found")
    exit() 

use_redis_cache = False # Redis much be installed and operational if this is set to True.  
if use_redis_cache: 
    connect_to_redis()

symbol_list = make_symbols_list() 
if not(symbol_list):    
    print("Could not get positions. Required file 'positions.json' not found.")     
    exit()

# print "Getting quotes..."
# print 
# print "Symbol  YTD Return"
'''for item in symbol_list: 
    get_ytd_return(item, api_key)
'''    
# get_ytd_return("AMZN", api_key)

if __name__ == "__main__":
    app.run(debug = True, port = 5005)
