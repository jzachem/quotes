#!/usr/bin/env python

import os
import requests
import json 


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
         
        
    return(symbol_list)   



def get_end_of_year_price(symbol, encoded_apikey ):

    # startDate is milliseconds from epoch time (Jan 1, 1970). Value is 9:30 am EST Dec 29, 2017 - Last trading day of the year
    # endDate is milliseconds from epoch time (Jan 1, 1970). Value is 4:00 pm EST Dec 29, 2017 - Last trading day of the year

    eoy_quote_data = {}      #end_of_year_quote dictionary
    
    eoy_price = 1.00
    
    url = "https://api.tdameritrade.com/v1/marketdata/{}/pricehistory?apikey={}&periodType=month&period=1&frequencyType=daily&frequency=1&endDate=%201514880000000&startDate=1514534400000".format(symbol, encoded_apikey)
    
    reply = requests.get(url)
    
    eoy_quote_data = reply.json() 
 
    if eoy_quote_data["empty"] == False: 
        
        for candle in eoy_quote_data["candles"]:
                       
            eoy_price = candle["close"]
            
            return(eoy_price)
        
        print(" Cound not find end of day closing price timedate")

    else: 

        print ("No candles returned")
        
        eoy_price = 1.00
    
    return (eoy_price) 


def get_price(symbol,encoded_apikey):    
    
    quote_data = {} 
       
    url = "https://api.tdameritrade.com/v1/marketdata/{}/quotes?apikey={}".format(symbol, encoded_apikey)
    
    reply = requests.get(url)
    
    quote_data = reply.json() 
    
    current_price = quote_data[item]["lastPrice"]
    
    return (current_price)

 
def calc_YTD_return(current, prev_year):
    
    delta = float(current) - float(prev_year)
    
    decimal = float(delta) / float(prev_year)
    
    return decimal


def get_ytd_return(ticker,key) :
    
    current_price_float = get_price(ticker, key)
    
    current_price_round = round(current_price_float,2)
    
    prev_year_closing_price_float = get_end_of_year_price(ticker, key)
    
    prev_year_closing_price_round =  round(prev_year_closing_price_float,2)
    
    YTD_price_change = (float(current_price_round) - float(prev_year_closing_price_round)) 
    
    YTD_return_float = calc_YTD_return(current_price_float, prev_year_closing_price_float)
    
    YTD_percent = float(YTD_return_float * 100)
  
    YTD_return = round(YTD_percent, 2)
  
    # print "The current price of %s is: %s  EOY price was: %s  Change for the year is %s  YTD return is %s"  % (ticker, current_price_round, prev_year_closing_price_round, YTD_price_change, YTD_return)
    print "%s  %7.2f" % (ticker.ljust(5), YTD_return) 
    

''' main '''

api_key = get_user_specific_api_key()

if api_key == "None": 
    print("Could not get api key. Required file 'tdinfo.json not found")
    exit() 

symbol_list = make_symbols_list() 
if not(symbol_list):
    print("Could not get positions. Required file 'positions.json' not found.") 
    exit()

print "Getting quotes..."
print 
print "Symbol  YTD Return"

for item in symbol_list: 
    get_ytd_return(item, api_key)
  
