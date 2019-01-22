import requests
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import time
import datetime

part1 = 'https://www.euronext.com/sites/www.euronext.com/files/statistics/derivatives/daily/2017/Euronext-DailyDerivativesStatistics%202019'
part2 = '.xlsx'
for month in range(datetime.datetime.now().month , datetime.datetime.now().month):
    for day in range(datetime.datetime.now().day - 1, datetime.datetime.now().day):
        while True:
            try:
                if month < 10:
                    m = str(0) + str(month)
                else:
                    m = str(month)
                if day < 10:
                    d = str(0) + str(day)
                else:
                    d = str(day)
                date = m + d
                print(date)
                url = part1 + date + part2
                r = requests.get(url)
                if r.status_code == 200:
                    path = '/home/driesnaert/Downloads/optionsData/' + date
                    with open(path, 'wb') as f:
                        f.write(r.content)
                    time.sleep(5)
            except:
                continue
            break

df = pd.read_excel('/home/driesnaert/Downloads/optionsData/0121', sheet_name = 'Series', header = 3)

puts = df[(df['Contract Name'] == 'Anheuser- Busch InBev NV')& (df['Contract\nType'] == 'P') & (df['Expiry\nMonth'] == 'Dec19')][['Exercise\nPrice', 'Settlement\nPrice']]
calls = df[(df['Contract Name'] == 'Anheuser- Busch InBev NV')& (df['Contract\nType'] == 'C') & (df['Expiry\nMonth'] == 'Dec19')][['Exercise\nPrice', 'Settlement\nPrice']]
futures = df[(df['Contract Name'] == 'Anheuser-Busch Inbev NV - Stock Future')& (df['Generic\nContract\nType'] == 'Futures') & (df['Expiry\nMonth'] == 'Dec19')]['Settlement\nPrice']
stocks = pd.read_csv("/home/driesnaert/Downloads/optionsData/ABI.BR.csv")

# s = stocks['Close'][0]  --> ToDo: geautomatiseerd stock prijs inlezen van het aandeel op die dag
s = 65
k = calls[calls['Exercise\nPrice'] <= s].sort_values(by=['Exercise\nPrice'], inplace = False, ascending = False)['Exercise\nPrice'].iloc[0]
c = calls[calls['Exercise\nPrice'] <= s].sort_values(by=['Exercise\nPrice'], inplace = False, ascending = False)['Settlement\nPrice'].iloc[0]
p = puts[puts['Exercise\nPrice'] <= s].sort_values(by=['Exercise\nPrice'], inplace = False, ascending = False)['Settlement\nPrice'].iloc[0]
f =futures.iloc[0]

class Call:
    def __init__(self, strike, premium, a):
        self.strike = strike
        self.premium = premium
        self.a = a
        
    def ret(self,s):
        if (self.a == 'long'):
            return max(0, s-self.strike) - self.premium
        if (self.a == 'short'):
            return self.premium - max(0, s-self.strike)
        
class Put:
    def __init__(self,strike, premium, a):
        self.strike = strike
        self.premium = premium
        self.a = a
        
    def ret(self,s):
        if (self.a == 'long'):
            return max(0,self.strike - s) - self.premium
        if (self.a == 'short'):
            return self.premium - max(0, self.strike - s)
        
class Future:
    def __init__(self, price, a):
        self.price = price
        self.a = a
            
    def ret(self,s):
        if self.a == 'long':
            return s - self.price
        if self.a == 'short':
            return self.price - s

call = Call(k,c,'short')
put = Put(k,p,'long')
future = Future(f, 'long')
x = range(0,100)
for i in x:
    print(call.ret(i)+put.ret(i)+future.ret(i))

