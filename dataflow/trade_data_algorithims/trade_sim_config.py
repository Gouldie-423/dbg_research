import pandas as pd
from sqlalchemy import create_engine
import csv
import numpy as np
import matplotlib.pyplot as plt

localpwd = 'pwd'
localengine = create_engine(f'postgresql://postgres:pwd@localhost/dbg_research')

ticker_SP500path = '/Users/timothygould/Desktop/Python/Projects/Quant Trading/S&P500List.csv'

#global variables used for evaluating algorithims

#novice mistake, next step to turn global metrics component into a class & compare results to ensure they're the same

total_wins = []
total_trades = []
global_holding_period = []
avg_daily_return = []
pct_over_14 = []

tickers = []

class trade:

	def __init__(self,ticker,alg_name,data_function,engine):
		self.ticker = ticker
		self.alg_name = alg_name
		self.data_function = data_function
		self.buy_date = None
		self.sell_date = None
		self.buy_price = None
		self.sell_price = None
		self.holding_period = None 
		self.diff = None
		self.avg_diff = None
		self.result = None
		self.key = None
		self.engine = engine	

	def buy_flag(self,df,buysearch):
		bs = buysearch
		RSI_Lookback = []
		try: #need this exception b/c sometimes each trade will start with the ma35 under ma50 and encounters an index error
			if df['ma35'][bs]<df['ma50'][bs] and df['ma35'][bs-1]>df['ma50'][bs-1]:
				pass
				if df['macd_10diff'][bs]<df['macd_5diff'][bs]<df['macd_diff'][bs]:
					pass
					if df['macd_5diff'][bs]-df['macd_10diff'][bs]>0.0: #.2
						pass
						if df['macd_diff'][bs]-df['macd_5diff'][bs]>0.0: #.3
							pass
							for x in df['rsi20'][bs-30:bs]:
								if x < 30:
									RSI_Lookback.append(x)
							if len(RSI_Lookback) > 0 and df['rsi20'][bs]>30:
								self.buy_price = df['adj_close'][bs]
								self.buy_date = df.index[bs]
								return True
		except IndexError:
			print(f'{df.index[bs]} not processed for {self.ticker}')

	def sell_flag(self,df,sellsearch):
		ss = sellsearch
		if df['ma15'][ss]>df['ma35'][ss] and df['ma15'][ss-1]<df['ma35'][ss-1]:
			self.sell_price = df['adj_close'][ss]
			self.sell_date = df.index[ss]
			return True


	#exports metrics surrounding single trade example & training data in 60 days leading up to buy flag
	def export(self,df,buysearch,holding_period):

		self.holding_period = len(holding_period)
		self.diff = ((self.sell_price/self.buy_price)-1)*100
		self.avg_diff = (self.diff)/self.holding_period

		if self.sell_price-self.buy_price > 0:
			self.result = 1
		else:
			self.result = 0
	
		label = pd.DataFrame({'alg_name':self.alg_name,'ticker':self.ticker,
				'buy_date':self.buy_date,
				'sell_date':self.sell_date,
				'pct_diff':self.diff,
				'holding_period':self.holding_period,
				'pct_diff_avg':self.avg_diff,
				'result':self.result,
				'key':str(self.ticker)+str(self.buy_date)},
				index=[0])
		label.to_sql(f'{self.data_function}_labels',self.engine,if_exists='append',index=False)

		#taking current df that sim was run on and making truncated copy of training data
		training_data = df[buysearch-60:buysearch].copy()
		#generating the key field for each record (redundant but necessary for query)
		training_data['keys'] = str(self.ticker)+str(self.buy_date)
		#putting in the correct date. Might no longer be necessary, was used to validate tx column
		training_data['date'] = training_data.index
		#removing duplicate adj closing prices for each day
		training_data.drop(['buys', 'sells'],inplace=True, axis=1)
		#generating tx field
		training_data['tx'] = np.arange(len(training_data))
		#exporting to sql
		training_data.to_sql(f'{self.data_function}_data',self.engine,if_exists='append',index=False)
		#used to store global metrics
	
		global_holding_period.append(self.holding_period)
		avg_daily_return.append(self.diff/self.holding_period)
		total_trades.append(self.diff)
		
		if self.diff>0:
			total_wins.append(self.diff)
		if (self.diff/self.holding_period)>.14:
			pct_over_14.append(self.diff/self.holding_period)
		else:
			pass
