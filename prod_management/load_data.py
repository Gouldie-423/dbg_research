from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import torch
import datetime
from datetime import timedelta

localengine = create_engine(f'postgresql://postgres:pwd@localhost/dbg_research')
validationengine = create_engine(f'postgresql://postgres:pwd@localhost/dbg_validation')

def grab_data(ticker,engine,start_date,end_date):
	df = pd.read_sql_query(f'''
				SELECT 
				daily_trade_data.date,
				daily_trade_data.ticker,
				daily_trade_data.adj_close,
				daily_trade_data.vol_as_pct,
				macd.macd,
				macd.signal,
				macd.macd_diff,
				macd.macd_5d,
				macd.signal_5d,
				macd.macd_5diff,
				macd.macd_10d,
				macd.signal_10d,
				macd.macd_10diff,
				moving_averages.ma200,
				moving_averages.ma150,
				moving_averages.ma100,
				moving_averages.ma75,
				moving_averages.ma50,
				moving_averages.ma35,
				moving_averages.ma25,
				moving_averages.ma15,
				moving_averages.ma10,
				rsi.rsi50,
				rsi.rsi40,
				rsi.rsi30,
				rsi.rsi20
				FROM
				daily_trade_data
				JOIN macd
				ON daily_trade_data.date=macd.date
				AND daily_trade_data.ticker=macd.ticker
				JOIN moving_averages
				ON daily_trade_data.date=moving_averages.date
				AND daily_trade_data.ticker=moving_averages.ticker
				JOIN rsi
				ON daily_trade_data.date=rsi.date
				AND daily_trade_data.ticker=rsi.ticker
				WHERE daily_trade_data.ticker = '{ticker}'
				AND daily_trade_data.date >= '{start_date}'
				AND daily_trade_data.date <= '{end_date}'
				ORDER BY daily_trade_data.date ASC''',engine)
	return df

def grab_sellsearch(engine):
	
	df = pd.read_sql_query('SELECT * FROM predict_labels where sell_date IS NULL',engine)
	return df

def norm_metrics(engine):
	
	df = pd.read_sql_query('SELECT * FROM norm_metrics',engine)
	return df

def query_tickers(engine):

	 df = pd.read_sql_query('SELECT * FROM ticker_list',engine)
	 return df
	 
def query_tickers_blacklist(engine):

	df = pd.read_sql_query('SELECT * FROM ticker_blacklist',engine)
	return df

def query_recent_date(engine):

	df = pd.read_sql_query('SELECT ticker,max(date) from daily_trade_data GROUP BY ticker',engine)
	return df

def query_missing_data(engine):

	df = pd.read_sql_query('SELECT ticker,max from missing_data',engine)
	return df

def prediction_dupe_check(alg_name,ticker,buy_date,engine):

	df = pd.read_sql_query(f"SELECT * FROM predict_labels WHERE alg_name = '{alg_name}' AND ticker = '{ticker}' AND buy_date = '{buy_date}' ",engine)
	print(df)
	if len(df)>0:
		return True
	else:
		return False




	 