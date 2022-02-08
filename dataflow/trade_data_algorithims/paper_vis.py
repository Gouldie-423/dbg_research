import numpy as np
import pandas as pd
from numpy import load
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import trade_sim_config as config
import matplotlib.pyplot as plt

#sample graphs used to 

config.pull_SP_tickers()

def graph_gen(start_date,end_date):
	for ticker in config.tickers:
		df = config.grab_data(ticker,config.localengine,start_date,end_date)
		df.set_index('date',inplace=True)
		buysearch = -len(df.index)
		df['buys'] = df['adj_close']
		df['sells'] = df['adj_close']
		for i in df.index[buysearch:]:
			trade = config.trade(ticker,'V1',None,config.localengine)
			if trade.buy_flag(df,buysearch) == True:
				sellsearch=buysearch
				for l in df.index[sellsearch:]:
					if trade.sell_flag(df,sellsearch)==True:
						new_df = trade.ma_pct_diff(df)
						trade.indicator_export(new_df,buysearch,sellsearch,path='normalized_ma_demo',indicator=True)
						break
					sellsearch += 1
			buysearch += 1

#query to pull number of trades by month
def timeline_pull(result):

		df = pd.read_sql_query(f'''
			select
			date_trunc('year', buy_date), count(1)
			from train_labels
			WHERE result = {result}
			group by 1
			order by date_trunc ASC
			''',config.localengine)
		
		return df

def timeline_graph_gen():

	timelines = {'0':0,'1':0}

	for result in range(0,2):
		df = timeline_pull(result)
		timelines[str(result)] = df

	total = timelines['0']['count']+timelines['1']['count']
	wins = timelines['1']['count']
	losses = timelines['0']['count']

	plt.plot([i for i in timelines['0']['date_trunc']],losses,label='Losses',c='red')
	plt.plot([i for i in timelines['1']['date_trunc']],wins,label='Wins',c='blue')
	plt.plot([i for i in timelines['0']['date_trunc']],total,label='Total Trades',c='green')
	plt.xlabel('Year')
	plt.ylabel('Number of Trades')
	plt.title('Number of Trades vs Year')
	plt.legend()
	plt.ylim([0,250])
	plt.savefig('/Users/timothygould/dbg_research/research/indicator_vis/Trades_by_Year')
	plt.clf()

	pct_wins = (wins/total)*100

	plt.plot([i for i in timelines['0']['date_trunc']],pct_wins,label='Percentage of Wins')
	plt.xlabel('Year')
	plt.ylabel('% of Wins')
	plt.title('% of Wins vs Year')
	plt.legend()
	plt.ylim([0,100])
	plt.savefig('/Users/timothygould/dbg_research/research/indicator_vis/Percent_of_Wins')
	plt.clf()

def trading_frequency_graph():

		num_samples = []

		df = pd.read_sql_query(f'''SELECT ticker,COUNT(*) 
									from train_labels 
									group by ticker''',config.localengine)

		for i in range(1,max(df['count'])+1):
			num_samples.append(len(df[df['count']==i]))
		plt.xlabel('Number of Trades')
		plt.ylabel('Number of Securities')
		plt.title('Number of Securities vs Number of Trades')
		plt.bar(range(1,10),num_samples)
		plt.savefig('/Users/timothygould/dbg_research/research/indicator_vis/Trades_by_Security')

# graph_gen('2010/01/01','2019/12/31')
