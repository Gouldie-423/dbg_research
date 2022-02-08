import csv
import db_refresh as refresh
import datetime as dt
from datetime import timedelta
from datetime import datetime
import load_data as load
import basic_rnn_model as rnn
import screening_alg as alg
import numpy as np
from sqlalchemy.sql import text
import requests
import pandas as pd

def pull_SP_tickers():
	tickers = []
	
	with open ('/Users/timothygould/Desktop/Python/Projects/Quant Trading/S&P500List.csv') as csv_file:
		reader = csv.reader(csv_file)
		for row in reader:
			tickers.append(row[0])
	
	return tickers

def ticker_check(today,engine):

	#on this table tickers are dataframe index
	database_tickers = load.query_tickers(engine)
	database_tickers.set_index('ticker',inplace=True)
	refreshed_tickers = refresh.scrape_SP_tickers(engine)

	#making sure index is in alphabetical order
	database_tickers.sort_index(inplace=True)
	refreshed_tickers.sort_index(inplace=True)

	check = database_tickers.equals(refreshed_tickers)

	if check:
		pass

	if not check:
		#checking to see if a new security has been added
		for i in refreshed_tickers.index.values:
			
			if i not in database_tickers.index.values:
				#running through refresh of recent values
				new_data = refresh.pull_data('2020-01-01',today+timedelta(days=1),i)
				refresh.write_data(new_data,engine)

				updated_ticker_info = refreshed_tickers.loc[(refreshed_tickers.index==i)].copy()
				updated_ticker_info.to_sql('ticker_list',engine,if_exists='append')

		#loading database tickers again after last round of changes
		database_tickers = load.query_tickers(engine)
		database_tickers.set_index('ticker',inplace=True)

		#adjusting status based on most recent refresh
		for i in refreshed_tickers.index.values:
			refreshed_status = np.squeeze(refreshed_tickers.loc[(refreshed_tickers.index==i)])
			database_status = np.squeeze(database_tickers.loc[(database_tickers.index==i)])
			
			if refreshed_status != database_status:
				with engine.connect() as con:
					query=text(f'''UPDATE "ticker_list" SET "status" = '{refreshed_status}' WHERE "ticker" = '{i}'
						''')
					con.execute(query)
		check = True

		database_tickers = load.query_tickers(engine)
		database_tickers.set_index('ticker',inplace=True)


	working_tickers = database_tickers.index[(database_tickers['status']!='inactive')&(database_tickers['status']!='legacy')].values
	return working_tickers

def dupe_check(data,last_data_received,today):

	try:
		print(last_data_received)
		max_data_scraped = datetime.strptime(str(data.index[-1]),'%Y-%m-%d 00:00:00').date()
		last_data_received = datetime.strptime(str(np.squeeze(last_data_received['max'])), '%Y-%m-%d 00:00:00').date()
		if max_data_scraped <= last_data_received: #needs to be <= so old data doesn't get written in 
			return []
		else:
			return data
	except TypeError: #system returns type error when blank df (nonetype) is passed into datetime function,
		return []
	except ValueError: #system returns value error when no datetime is fetched from db and df is blank
		return []

def missing_data_check(data,last_data_received,today):
	try:
		max_data_db = datetime.strptime(str(np.squeeze(last_data_received['max'])),'%Y-%m-%d 00:00:00').date()
		if max_data_db < today:
			return []
		else:
			return data
	except TypeError: #system returns type error when blank df (nonetype) is passed into datetime function
		return []
	except IndexError: #index -1 is out of bounds for axis 0 with size 0 (when blank df is passed in). Only seems to happen when data is loaded from db.
		return []	   #scraping does not have same error
	except ValueError: # 'Series([], Name: max, dtype: datetime64[ns])' does not match format '%Y-%m-%d 00:00:00' : system also returns error when blank df is brought to system
		return []

def missing_data_refresh(active_tickers,today,max_dates,engine):
	
	for ticker in active_tickers:
		last_data_received = max_dates[max_dates['ticker']==ticker].copy()
		data = load.grab_data(ticker,engine,today-timedelta(days=365),today+timedelta(days=1))
		data.set_index('date',inplace=True)

		data = missing_data_check(data,last_data_received,today)
		
		if len(data) == 0:
			last_data_received.to_sql(f'missing_data',engine,if_exists='append',index=True)
		else:
			pass
			
def daily_refresh(engine,today,manual_refresh=False):

	if manual_refresh:
		active_tickers = manual_refresh
		
	else:
		active_tickers = ticker_check(today,engine)

	max_dates = load.query_recent_date(engine)	
	
	for ticker in active_tickers:
		
		print(ticker)
		data = refresh.pull_data(today-timedelta(days=360),today+timedelta(days=1),ticker)
		last_data_received = max_dates[max_dates['ticker']==ticker].copy()

		data = dupe_check(data,last_data_received,today)
		
		if len(data) > 0:
			refresh.write_data(data,engine,refresh=True)
		else:
			pass

	#more efficient to pull query again after initial pull has taken place opposed to trying to find missing data
	#during pull			

	max_dates = load.query_recent_date(engine)

	missing_data_refresh(active_tickers,today,max_dates,engine)

	return active_tickers

def buy_search(tickers,today,engine):
	norm_metrics = load.norm_metrics(engine)

	#day we're testing on with known data

	for ticker in tickers:
		print(ticker)
		trade = alg.trade(ticker,'V1','predict',engine)
		df = load.grab_data(ticker,engine,today-timedelta(days=100),today)
		df = df.tail(60).copy()
		df.set_index('date',inplace=True)
		
		for day in range((len(df.index)-20),len(df.index)):

			if len(df)==0:
				print(f'No Data for {ticker}')
				pass
			else:
				if trade.buy_flag(df,day)==True:
					norm_df = trade.normalize_data(df,norm_metrics)
					matrix = trade.process_data(norm_df)
					model = rnn.model(matrix,'13')
					prediction = model.run()
					pred_dupe = load.prediction_dupe_check('V1',ticker,df.index[day],engine)
					if pred_dupe == False:
						trade.export(prediction)
						break
					else:
						break

def sell_search(today,engine):
	open_sells = load.grab_sellsearch(engine)
	date = open_sells['buy_date'].values
	tickers = open_sells['ticker'].values

	for ticker in range(len(tickers)):
		trade = alg.trade(ticker,'V1','predict',engine)
		data = load.grab_data(tickers[ticker],engine,date[ticker],today)
		for day in range(len(data.index)):
			if trade.sell_flag(data,day)==True:
				ticker = tickers[ticker]
				sell_date = data['date'][day]
				buy_price = data['adj_close'][0]
				buy_date = data['date'][0]
				holding_period = day+1
				trade.update(engine,ticker,sell_date,buy_price,buy_date,holding_period)
				break

def backfill(tickers,engine):
	
	norm_metrics = load.norm_metrics(engine)

	for ticker in tickers:
		print(ticker)
		df = load.grab_data(ticker,engine,'2021/01/01','2021/12/31')
		df.set_index('date',inplace=True)

		trade = alg.trade(ticker,'V1','predict',engine)
		buysearch = -len(df.index)

		for i in df.index[buysearch:]:
			holding_period = [] #easiest way to do business day calculation is by grabbinglen of holding_period list
			if trade.buy_flag(df,buysearch) == True: #buy criteria for algorithm
				norm_df = trade.normalize_data(df[buysearch-60:buysearch],norm_metrics)
				matrix = trade.process_data(norm_df)
				model = rnn.model(matrix,'13')
				prediction = model.run()

				sellsearch=buysearch
				for l in df.index[sellsearch:]:
					holding_period.append(l) #easiest way to calculate holding period while remaining mindful of business days/market holidays. If the market is down, there
					if trade.sell_flag(df,sellsearch) == True: #sell criteria algorithm
						trade.export(prediction,backfill=True,holding_period=holding_period) #takes all data from trade class & exports label, training data, assorted other data points
						break			
					sellsearch=sellsearch+1
			buysearch=buysearch+1
			
def load_database(today,engine):

	database_tickers = load.query_tickers(engine)
	database_tickers.set_index('ticker',inplace=True)

	active_tickers = database_tickers.index[(database_tickers['status']!='inactive')&(database_tickers['status']!='legacy')].values

	for ticker in active_tickers:
		print(ticker)
		df = refresh.pull_data('2020-01-01',today+timedelta(days=1),ticker)
		refresh.write_data(df,engine,refresh=False)

def backfill_trade_data(): #need to remove arguments to import as cron job to flask
	engine = refresh.serverengine
	today = dt.date.today()
	begin_date = today-timedelta(days=365)
	end_date = today+timedelta(days=1)

	missing_data = load.query_missing_data(engine)
	missing_tickers = missing_data['ticker'].values.copy()

	for ticker in missing_tickers:
		try:
			df = refresh.pull_data(begin_date,end_date,ticker)
			last_data_received = str(np.squeeze(missing_data['max'][missing_data['ticker']==ticker].values)) #last data we have in db
			last_data_pulled = str(df.index[-1]) #last data that was pulled from yahoo finance
			after_missing_date = df.index > last_data_received
			new_data = df.loc[after_missing_date]

			new_data = dupe_check(new_data,last_data_received,today)
			if len(new_data)==0:
				pass
			else:
				refresh.write_data(new_data,engine,refresh=False)
				
		except TypeError: #new data might not be available, if not, error will raise
			print('pass')
			pass

	#deleting missing data before running missing_data refresh again
	with engine.connect() as con:
		query=text('DELETE FROM missing_data')
		con.execute(query)

	#missing data refresh
	max_dates = load.query_recent_date(engine)
	missing_data_refresh(missing_tickers,today,max_dates,engine)

	buy_search(missing_tickers,today,engine)
	sell_search(today,engine)

	now = dt.datetime.now()
	now = dt.datetime(now.year,now.month,now.day,now.hour,now.minute,now.second)

	last_refresh = pd.DataFrame({'last_refresh':str(now)},index=[0])
	last_refresh.to_sql(f'refresh',engine,if_exists='append',index=True)

def full_test_job():
	engine = refresh.serverengine #needed to remove engine argument otherwise couldn't call it in flask scheduler
	today = dt.date.today()
	tickers = daily_refresh(engine,today)

	buy_search(tickers,today,engine)
	sell_search(today,engine)

	now = dt.datetime.now()
	now = dt.datetime(now.year,now.month,now.day,now.hour,now.minute,now.second)

	last_refresh = pd.DataFrame({'last_refresh':str(now)},index=[0])
	last_refresh.to_sql(f'refresh',engine,if_exists='append',index=True)

