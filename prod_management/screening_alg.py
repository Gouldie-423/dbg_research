import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import csv
import numpy as np
import matplotlib.pyplot as plt


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
			print(f'{df.index[bs]} not processed for {self.ticker}') #if MA35 begins under MA50
		except TypeError:
			print(f'{df.index[bs]} not processed for {self.ticker}') #if not enough data in backfill '<' not supported between instances of 'NoneType' and 'NoneType'


	def sell_flag(self,df,sellsearch):
		try:
			ss = sellsearch
			if df['ma15'][ss]>df['ma35'][ss] and df['ma15'][ss-1]<df['ma35'][ss-1]:
				self.sell_price = df['adj_close'][ss]
				self.sell_date = df.index[ss]
				return True
		except KeyError:
			return False

	def ma_pct_diff(self,df):

		new_df = df.copy()

		new_df['ma200'] = ((df['ma200']-df['adj_close'])/df['ma200'])*100
		new_df['ma150'] = ((df['ma150']-df['adj_close'])/df['ma150'])*100
		new_df['ma100'] = ((df['ma100']-df['adj_close'])/df['ma100'])*100
		new_df['ma75'] = ((df['ma75']-df['adj_close'])/df['ma75'])*100
		new_df['ma50'] = ((df['ma50']-df['adj_close'])/df['ma50'])*100
		new_df['ma35'] = ((df['ma35']-df['adj_close'])/df['ma35'])*100
		new_df['ma25'] = ((df['ma25']-df['adj_close'])/df['ma25'])*100
		new_df['ma15'] = ((df['ma15']-df['adj_close'])/df['ma15'])*100
		new_df['ma10'] = ((df['ma10']-df['adj_close'])/df['ma10'])*100

		return new_df

	def normalize_data(self,data,norm_metrics):
		data = self.ma_pct_diff(data)
		data.drop(columns=['ticker','adj_close','macd_5d','signal_5d','macd_5diff',
		'macd_10d','signal_10d','macd_10diff','rsi30','rsi40'],inplace=True)
		train_min = norm_metrics[norm_metrics['metric']=='train_min'].copy()
		train_max = norm_metrics[norm_metrics['metric']=='train_max'].copy()
		train_min2 = {}
		train_max2 = {}
		for column in data.columns:
			#need to multiply df by scalar value. Otherwise will just get NAN values
			train_min2[column] = np.squeeze(float(train_min[column].values))
			train_max2[column] = np.squeeze(float(train_max[column].values))
			#performing actual min-max norm
			data[column] = (data[column] - train_min2[column])/(train_max2[column]-train_min2[column])
		return data

	def process_data(self,data):
		#num_features, batch_size, time steps
		matrix = np.zeros((15,1,60))
		data = data.fillna(0)

		for time in range(len(data)):
			datapoint = data.loc[data.index[time]].copy()
			matrix[:,0,time] = datapoint

		return matrix
	def export(self,prediction,backfill=False,holding_period=[]):

		if backfill:

			self.holding_period = len(holding_period)
			self.diff = ((self.sell_price/self.buy_price)-1)*100
			self.avg_diff = (self.diff)/self.holding_period
	
		else:
			pass
	
		label = pd.DataFrame({'alg_name':self.alg_name,'ticker':self.ticker,
				'buy_date':self.buy_date,
				'sell_date':self.sell_date,
				'pct_diff':self.diff,
				'pct_diff_avg':self.avg_diff,
				'holding_period':self.holding_period,
				'classification':prediction},
				index=[0])
		label.to_sql(f'{self.data_function}_labels',self.engine,if_exists='append',index=False)

	def update(self,engine,ticker,sell_date,buy_price,buy_date,holding_period):

		pct_diff = ((self.sell_price/buy_price)-1)*100

		with engine.connect() as con:
			query = text(f'''UPDATE "predict_labels" SET "sell_date" = '{sell_date}', 
							"pct_diff" = {float(pct_diff)},
							"holding_period" = {float(holding_period)},
							"pct_diff_avg" = {float(pct_diff/holding_period)}
							WHERE ticker = '{ticker}'
							AND
							buy_date = '{buy_date}';''')
			con.execute(query)
