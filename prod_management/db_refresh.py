
import csv
import psycopg2
from sqlalchemy import create_engine
import yfinance as yf
import pandas as pd
from datetime import timedelta,datetime
import datetime as dt
from pandas_datareader import data as pdr
from bs4 import BeautifulSoup
import requests

ticker_SP500path = '/Users/timothygould/Desktop/Python/Projects/Quant Trading/S&P500List.csv'
ticker_NASDAQpath ='/Users/timothygould/Desktop/Python/Projects/Quant Trading/NASDAQ.csv'


localpwd = 'pwd'
localengine = create_engine(f'postgresql://postgres:{localpwd}@localhost/dbg_research')
serverengine = create_engine(f'postgresql://dbg_devtest:dbg_password@database-2.c9zekcxdkpeh.us-east-2.rds.amazonaws.com:5375/database_test')
testengine = create_engine(f'postgresql://postgres:{localpwd}@localhost/dbg_staging')
validationengine = create_engine(f'postgresql://postgres:pwd@localhost/dbg_validation')

def pull_SP_tickers():
	with open (ticker_SP500path) as csv_file:
		reader = csv.reader(csv_file)
		for row in reader:
			tickers.append(row[0])

def scrape_SP_tickers(engine,write=False):
	url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
	table = pd.read_html(url)
	current_tickers = table[0].copy()
	changed_tickers = table[1].copy()
	current_tickers['status'] = 'active'
	current_tickers.rename(columns={'Symbol':'ticker'},inplace=True)
	current_tickers.drop(columns=['Security','SEC filings','GICS Sector','GICS Sub-Industry','Headquarters Location'
	,'Date first added','CIK','Founded'],inplace=True,axis=1)
	
	changes_dict = {'ticker':[],'status':[]}

	still_use_tickers = changed_tickers.loc[changed_tickers['Reason']['Reason'].str.contains("spun off|market", case=False)]
	for i in still_use_tickers['Removed']['Ticker']:

		if str(i) == 'nan' or str(i) in current_tickers['ticker'].values or str(i) in changes_dict['ticker']:
			pass
		else:
			changes_dict['ticker'].append(i)
			changes_dict['status'].append('legacy')
	
	decomissioned_tickers = changed_tickers.loc[~changed_tickers['Reason']['Reason'].str.contains("spun off|market", case=False)]
	for i in decomissioned_tickers['Removed']['Ticker']:
		if str(i) == 'nan' or str(i) in current_tickers['ticker'].values or str(i) in changes_dict['ticker']:
			pass
		else:
			changes_dict['ticker'].append(i)
			changes_dict['status'].append('inactive')

	changes_df = pd.DataFrame.from_dict(changes_dict)
	tickerlist = pd.concat([current_tickers,changes_df])
	tickerlist.set_index('ticker',inplace=True)

	if write:
		tickerlist.to_sql(f'ticker_list',engine,if_exists='append',index=True)
		return tickerlist
	else:
		return tickerlist

def rename_df_columns(df):
	df.rename(columns = 
	{'Date':'date',
	'High':'high',
	'Low':'low',
	'Open':'open',
	'Close':'close',
	'Volume':'volume',
	'Adj Close':'adj_close'},
	inplace=True)
	return df

def df_columns(df,outstanding_shares):
	#Moving Averages
	df['ma200'] = df['Adj Close'].rolling(window=200).mean()#6
	df['ma150'] = df['Adj Close'].rolling(window=150).mean()#7
	df['ma100'] = df['Adj Close'].rolling(window=100).mean()#8
	df['ma75'] = df['Adj Close'].rolling(window=75).mean()#9
	df['ma50'] = df['Adj Close'].rolling(window=50).mean()#10
	df['ma35'] = df['Adj Close'].rolling(window=35).mean()#11
	df['ma25'] = df['Adj Close'].rolling(window=25).mean()#12
	df['ma15'] = df['Adj Close'].rolling(window=15).mean()#13
	df['ma10'] = df['Adj Close'].rolling(window=10).mean()#14

	#MACD
	df['short_ema'] = df['Adj Close'].ewm(span=12,adjust=False).mean()#15
	df['long_ema'] = df['Adj Close'].ewm(span=26,adjust=False).mean()#16
	df['macd'] = df['short_ema']-df['long_ema']#17
	df['signal'] = df['macd'].ewm(span=9,adjust=False).mean()#18
	df['macd_diff'] = round(df['macd']-df['signal'],5)#19
	df['macd_5d'] = df['macd'].shift(5)#20
	df['signal_5d'] = df['signal'].shift(5)#21
	df['macd_5diff'] = round(df['macd_5d']-df['signal_5d'],5)#22
	df['macd_10d'] = df['macd'].shift(10)#23
	df['signal_10d'] = df['signal'].shift(10)#24
	df['macd_10diff'] = round(df['macd_10d']-df['signal_10d'],5)#25

	#RSI
	delta = df['Adj Close'].diff(1)
	up = delta.copy()
	down = delta.copy()
	up[up<0] = 0
	down[down>0] = 0
	df['avg_gain50'] = up.rolling(window = 50).mean()
	df['avg_loss50'] = abs(down.rolling(window = 50).mean())
	RS = df['avg_gain50']/df['avg_loss50']
	RSI = 100 - (100/(1+RS))
	df['rsi50'] = 100 - (100/(1+(df['avg_gain50']/df['avg_loss50'])))

	df['avg_gain40'] = up.rolling(window = 40).mean()
	df['avg_loss40'] = abs(down.rolling(window = 40).mean())
	RS = df.iloc[:,29]/df.iloc[:,30]
	RSI = 100 - (100/(1+RS))
	df['rsi40'] = 100 - (100/(1+(df.iloc[:,29]/df.iloc[:,30])))

	df['avg_gain30'] = up.rolling(window = 30).mean()
	df['avg_loss30'] = abs(down.rolling(window = 30).mean())
	RS = df.iloc[:,32]/df.iloc[:,33]
	RSI = 100 - (100/(1+RS))
	df['rsi30'] = 100 - (100/(1+(df.iloc[:,32]/df.iloc[:,33])))

	df['avg_gain20'] = up.rolling(window = 20).mean()
	df['avg_loss20'] = abs(down.rolling(window = 20).mean())
	RS = df.iloc[:,35]/df.iloc[:,36]
	RSI = 100 - (100/(1+RS))
	df['rsi20'] = 100 - (100/(1+(df.iloc[:,35]/df.iloc[:,36])))

	df['mkt_cap'] = df['Adj Close']*int(outstanding_shares)
	df['vol_as_pct'] = (df['Volume']*df['Adj Close'])/df['mkt_cap']

	return df



def pull_data(begin_date,end_date,ticker):
#pulling in df to set baseline for outstanding shares
	try:
		yf.pdr_override() #got data to pull. Caused crazy errors. need to check back later
		#https://github.com/pydata/pandas-datareader/issues/170

		#pulling in most recent market cap to calculate outstanding shares
		#required to calculate historical market cap
		df3=pdr.get_data_yahoo(ticker,start=dt.datetime(2021,7,1),end=dt.datetime(2021,7,2))
		mkt_cap = pdr.get_quote_yahoo(ticker)['marketCap']
		print(df3,mkt_cap)
		outstanding_shares = mkt_cap/df3['Adj Close'][0] #ran into an issue with 'A' where 7/2 was NaN so I had to switch to 7/1 to get correct data
		#pulling in rest of data	
		df=pdr.get_data_yahoo(ticker,begin_date,end_date)
		df_columns(df,outstanding_shares)
		
		#adjusting df before importing to db
		df.insert(0,'ticker',ticker) #putting ticket at beginning
		df = df.reset_index() #date as index (to rename it)
		df = rename_df_columns(df) #renaming columns so they are query-able in sql
		df = df.set_index("date") #adding date back in as index
		return df
	
	except KeyError:
		#prevents error from raising when trying to adjust columns on blank dataset
		print(f'{ticker} does not have enough data for backtest')
		df = []
		return df

	except IndexError:
		#prevents another error from raising when trying to pull most recent market cap
		print(f'{ticker} does not have enough data for backtest')
		df = []
		return df

def write_data(data,engine,refresh = False):

	if len(data) > 0:
		func = ['daily','ma','macd','rsi']

		if refresh:
			data = data.tail(1).copy()
		else:
			pass

		for x in func:

			if x == 'daily':
				df = data[['ticker','high','low','open','close','volume','vol_as_pct','mkt_cap','adj_close']]
				df.to_sql(f'daily_trade_data',engine,if_exists='append',index=True)

			
			if x == 'ma':
				df = data[['ticker','ma200','ma150','ma100','ma75','ma50','ma35',
				'ma25','ma15','ma10']]
				df.to_sql(f'moving_averages',engine,if_exists='append',index=True)

			if x == 'macd':
				df = data[['ticker','macd','signal','macd_diff','macd_5d','signal_5d',
				'macd_5diff','macd_10d','signal_10d','macd_10diff']]
				df.to_sql(f'macd',engine,if_exists='append',index=True)

			if x == 'rsi':
				df = data[['ticker','rsi50','rsi40','rsi30','rsi20']]
				df.to_sql(f'rsi',engine,if_exists='append',index=True)

			else:
				pass
	else:
		pass

def update_norm_metrics(engine):
	df = pd.read_csv('/Users/timothygould/Desktop/norm_metrics.csv')
	df.to_sql('norm_metrics',engine,if_exists='replace',index=True)

	df = pd.read_csv('/Users/timothygould/Desktop/alg_performance_metrics.csv')
	df.to_sql('alg_performance_metrics',engine,if_exists='replace',index=True)

	df = pd.read_csv('/Users/timothygould/Desktop/trade_table_docs.csv')
	df.to_sql('trade_table_docs',engine,if_exists='replace',index=True)

	df = pd.read_csv('/Users/timothygould/Desktop/metrics_table_docs.csv')
	df.to_sql('metrics_table_docs',engine,if_exists='replace',index=True)

