
import pandas as pd
import numpy as np
import openpyxl
import csv
import trade_sim_config as config
from sqlalchemy import create_engine

#remember to check algname before you run

def run(train):
	if train == True:
		tradesim('2010/01/01','2019/12/31','train')
	else:
		tradesim('2021/01/01','2021/06/30','test')

def tradesim(start_date,end_date,data_function):
	alg_name = 'V1'
	for ticker in config.tickers:
		#pulling in data for each ticker within specified time range
		df = config.grab_data(ticker,config.localengine,start_date,end_date)
		#resetting index when loaded from db it gives the record # as default
		df.set_index('date',inplace=True)
		#some securities have different lengths, counting backward from beginning may not be the same # for each
		buysearch = -len(df.index)
		#not super computationally efficient, but putting buys and sells in diff columns for sake of dataflow tracking
		df['buys'] = df['adj_close']
		df['sells'] = df['adj_close']

		
		for i in df.index[buysearch:]:
			trade = config.trade(ticker,alg_name,data_function,config.localengine) #creating new potential trade instance on each iteration
			holding_period = [] #easiest way to do business day calculation is by grabbinglen of holding_period list
			if trade.buy_flag(df,buysearch) == True: #buy criteria for algorithm
				sellsearch=buysearch
				for l in df.index[sellsearch:]:
					holding_period.append(l) #easiest way to calculate holding period while remaining mindful of business days/market holidays. If the market is down, there is no day
					if trade.sell_flag(df,sellsearch) == True: #sell criteria algorithm
						trade.export(df,buysearch,holding_period) #takes all data from trade class & exports label, training data, assorted other data points
						break			
					sellsearch=sellsearch+1
			buysearch=buysearch+1

	#Global Metrics
	
	global_metrics = pd.DataFrame({'alg_name':alg_name,'win_ratio':(len(config.total_wins)/len(config.total_trades)*100),
					'num_trades':len(config.total_trades),
					'avg_holding_period':sum(config.global_holding_period)/len(config.global_holding_period),
					'avg_daily_increase':sum(config.avg_daily_return)/len(config.avg_daily_return),
					'over_14':(len(config.pct_over_14)/len(config.total_trades)*100)},
					index=[0])

	global_metrics.to_sql(f'{data_function}_global_alg_data',config.localengine,if_exists='append',index=False)

train = True
	
# config.pull_SP_tickers()
# run(train)
	
