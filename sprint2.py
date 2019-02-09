import requests
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import time
import datetime
#import plotly.plotly as py
#import plotly.graph_objs as go
import numpy as np
#from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

def zeroPad(month,day):
    if month < 10:
        m = str(0) + str(month)
    else:
        m = str(month)
    if day < 10:
        d = str(0) + str(day)
    else:
        d = str(day)
    date = m + d
    return date

class optionSeries:
    def __init__(self):
        self.data = []        
        self.commonStrikes = []
        
    def push(self,option):
        if len(self.data) == 0:
            self.commonStrikes = option.strikes
        else:
            for s in self.commonStrikes:
                if s not in option.strikes:
                    self.commonStrikes.remove(s)    
        self.data.append(option)
        
    def getPutSeries(self,i):
        series = []
        s = self.commonStrikes[i]
        for option in self.data:
            i2 = option.strikes.index(s)
            series.append(option.putPrices[i2])
        return series
    
    def getCallSeries(self,i):
        series = []
        s = self.commonStrikes[i]
        for option in self.data:
            i2 = option.strikes.index(s)
            series.append(option.callPrices[i2])
        return series
    
    def getDiscountRates(self,i):
        series = []
        s = self.commonStrikes[i]
        for option in self.data:
            i2 = option.strikes.index(s)
            series.append((option.callPrices[i2] - option.putPrices[i2])/(option.futurePrices - s))
        return series
    
    def getPutSeries2(self,i):
        series = []
        s = self.commonStrikes[i]
        for option in self.data:
            i2 = option.strikes.index(s)
            series.append(s - option.putPrices[i2])
        return series
    
    def getPremiumTimesSpread(self,i):
        series = []
        s = self.commonStrikes[i]
        for option in self.data:
            i2 = option.strikes.index(s)
            series.append(option.putPrices[i2]**0.5*(option.futurePrices - s + option.putPrices[i2]))
        return series
    
    def getFutures(self):
        series = []
        for option in self.data:
            series.append(option.futurePrices)
        return series
        
    
class optionDateSummary:
    def __init__(self, datum):
        self.datum = datum
        self.strikes = []
        self.putPrices = []
        self.callPrices = []
        self.futurePrices = 0
        
    def returnOnAssets(self,calls,puts,futures,s):
        money = 0
        for index, alpha in enumerate(calls):
            money = money + alpha*((-self.callPrices[index]) + max(0, s - self.strikes[index]))
        for index, alpha in enumerate(puts):
            money = money + alpha *((-self.putPrices[index]) + max(0, self.strikes[index] - s))
        money = money + futures*(s - self.futurePrices)
        return money
    
    def randomStrategy(self,sigma):
        puts = np.asarray(self.putPrices)
        calls = np.asarray(self.callPrices)
        l = len(self.strikes)
        v1 = -abs(np.random.normal(0,sigma,l))
        v2 = -abs(np.random.normal(0,sigma,l))
        sum = np.inner(puts, v1) + np.inner(calls, v2)
        v = np.append(v1,v2)/sum*100
        return np.append(v, np.random.normal(0,sigma,1))
        
            
        
    def setFuture(self,f):
        self.futurePrices = f
    
    def addStrike(self,k):
        self.strikes.append(k)
        
    def addPutPrice(self,price):
        self.putPrices.append(price)
        
    def addCallPrice(self,price):
        self.callPrices.append(price)
        
    def getPutPriceAt(self,strike):
        i = self.strikes.index(strike)
        return self.putPrices[i]
    
    def getCallPriceAt(self,strike):
        i = self.strikes.index(strike)
        return self.callPrices[i]
    
    def getFuture(self):
        return self.futurePrices
        
        
    def weerGave(self):
        print('future price: ' + str(self.futurePrices))
        for i,j,k in zip(self.strikes,self.putPrices, self.callPrices):
            print('strike: ' + str(i) + ';putprice: ' + str(j) + '; callprice: ' + str(k))

def collectOptionsSummaries(d1, d2, m1, m2, contractName1, contractName2, vervalDag):
    base = '/home/driesnaert/Downloads/optionsData/'
    summaries = []
    for day in range(d1, d2 + 1):
        for month in range(m1, m2 + 1):
            address = base + zeroPad(month, day)
            try:
                df = pd.read_excel(address, sheet_name = 'Series', header = 3)
            except:
                continue
            puts = df[(df['Contract Name'] == contractName1)& (df['Contract\nType'] == 'P') & (df['Expiry\nMonth'] == vervalDag)][['Exercise\nPrice', 'Settlement\nPrice']]
            calls = df[(df['Contract Name'] == contractName1)& (df['Contract\nType'] == 'C') & (df['Expiry\nMonth'] == vervalDag)][['Exercise\nPrice', 'Settlement\nPrice']]
            futures = df[(df['Contract Name'] == contractName2)& (df['Generic\nContract\nType'] == 'Futures') & (df['Expiry\nMonth'] == vervalDag)]['Settlement\nPrice']
            print(futures)
            obj = optionDateSummary(address)
            try:
                f =futures.iloc[0]
                obj.setFuture(f)
                for price in puts['Settlement\nPrice']:
                    obj.addPutPrice(price)
                for strikePrice in puts['Exercise\nPrice']:
                    obj.addStrike(strikePrice)
                for price in calls['Settlement\nPrice']:
                    obj.addCallPrice(price)
                summaries.append(obj)
            except:
                continue
    return summaries

def collectOptionsSummaries(d1, d2, m1, m2, contractName1, contractName2, vervalDag):
    base = '/home/driesnaert/Downloads/optionsData/'
    summaries = []
    for day in range(d1, d2 + 1):
        for month in range(m1, m2 + 1):
            address = base + zeroPad(month, day)
            try:
                df = pd.read_excel(address, sheet_name = 'Series', header = 3)
            except:
                continue
            puts = df[(df['Contract Name'] == contractName1)& (df['Contract\nType'] == 'P') & (df['Expiry\nMonth'] == vervalDag)][['Exercise\nPrice', 'Settlement\nPrice']]
            calls = df[(df['Contract Name'] == contractName1)& (df['Contract\nType'] == 'C') & (df['Expiry\nMonth'] == vervalDag)][['Exercise\nPrice', 'Settlement\nPrice']]
            futures = df[(df['Contract Name'] == contractName2)& (df['Generic\nContract\nType'] == 'Futures') & (df['Expiry\nMonth'] == vervalDag)]['Settlement\nPrice']
            print(futures)
            obj = optionDateSummary(address)
            try:
                f =futures.iloc[0]
                obj.setFuture(f)
                for price in puts['Settlement\nPrice']:
                    obj.addPutPrice(price)
                for strikePrice in puts['Exercise\nPrice']:
                    obj.addStrike(strikePrice)
                for price in calls['Settlement\nPrice']:
                    obj.addCallPrice(price)
                summaries.append(obj)
            except:
                continue
    return summaries









test = collectOptionsSummaries(6,6,2,2,'bpost NV - Standard Option', 'bpost NV/SA - Stock Future', 'Mar19')

mymax = 0
testobject = test[0]
for i in range(1000):
    mymin = 999999
    strategy = testobject.randomStrategy(1).tolist()
    array1 = strategy[0:22]
    array2 = strategy[22:44]
    array3 = -strategy[44]
    for s in range(6,10):
        myreturn = 0
        for j in range(10000):
            myreturn = myreturn + testobject.returnOnAssets(array1,array2,array3,np.random.gumbel(s,5))
        myreturn = myreturn/10000
        if myreturn < mymin :
            mymin = myreturn
    if mymin > mymax:
        mymax = mymin
        print('strategy: ' + str(strategy) + '\nreturn: ' + str(mymax))
