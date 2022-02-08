from sqlalchemy import create_engine
import yfinance as yf
import pandas as pd
from datetime import timedelta,datetime
import datetime as dt
from pandas_datareader import data as pdr

#modules in local directories
import database_config as config


def run():
	#quick few lines of code to ensure that certain securities aren't repeated & whole db
	#doesn't need to be deleted every time
	ticker_search = pd.read_sql_query('SELECT DISTINCT ticker FROM daily_trade_data',config.validationengine)
	ticker_search=ticker_search.values.tolist()
	ticker_search = [val for sublist in ticker_search for val in sublist]
	print(ticker_search)
	print(len(ticker_search))

	for ticker in config.tickers:
		if ticker == 'CXO' or ticker == 'FLIR' or ticker == 'TIF' or ticker =='VAR' or ticker in ticker_search: #cxo appears to have been delisted but causes an error with a foreign security
			pass
		else:
			print(ticker)
			#need to ensure that begin_date and end_date reflect the range that you would like to pull into the db
			begin_date = dt.datetime(1999,1,1)
			end_date = dt.datetime(2010,12,31)
			df=pull_data(begin_date,end_date,ticker)
			print(df)
			if len(df)==0:
				pass
			else:
				write_data(df,config.validationengine)

def pull_data(begin_date,end_date,ticker):
#pulling in df to set baseline for outstanding shares
	try:
		yf.pdr_override() #got data to pull. Caused crazy errors. need to check back later
		#https://github.com/pydata/pandas-datareader/issues/170

		#pulling in most recent market cap to calculate outstanding shares
		#required to calculate historical market cap
		df3=pdr.get_data_yahoo(ticker,start=dt.datetime(2021,7,1),end=dt.datetime(2021,7,2))
		mkt_cap = pdr.get_quote_yahoo(ticker)['marketCap']
		outstanding_shares = mkt_cap/df3['Adj Close'][0] #ran into an issue with 'A' where 7/2 was NaN so I had to switch to 7/1 to get correct data
		
		#pulling in rest of data	
		df=pdr.get_data_yahoo(ticker,begin_date,end_date)
		config.df_columns(df,outstanding_shares)
		
		#adjusting df before importing to db
		df.insert(0,'ticker',ticker) #putting ticket at beginning
		df = df.reset_index() #date as index (to rename it)
		df = config.rename_df_columns(df) #renaming columns so they are query-able in sql
		df = df.set_index("date") #adding date back in as index
		return df
	
	except IndexError:
		print(f'{ticker} does not have enough data for backtest')
		df = []		
		return df

#ensures that data for different technical indicators appear on different tables. Helps with scalability and data leagage if a new technical indicator
#is added you can comment out some code and not need to rewrite whole db.
def write_data(data,engine):
	func = ['daily','ma','macd','rsi']

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

config.pull_SP_tickers()
run()
