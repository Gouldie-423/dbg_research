import csv
from sqlalchemy import create_engine
import psycopg2

ticker_SP500path = '/Users/timothygould/Desktop/Python/Projects/Quant Trading/S&P500List.csv'
ticker_NASDAQpath ='/Users/timothygould/Desktop/Python/Projects/Quant Trading/NASDAQ.csv'

global tickers
tickers = []

localpwd = 'pwd'
localengine = create_engine(f'postgresql://postgres:{localpwd}@localhost/dbg_research')
validationengine = create_engine(f'postgresql://postgres:{localpwd}@localhost/dbg_validation')

#pulls tickers from saved file. Single file required b/c changes to S&P500 happened quite often in 2020
def pull_SP_tickers():
	with open (ticker_SP500path) as csv_file:
		reader = csv.reader(csv_file)
		for row in reader:
			tickers.append(row[0])

#need to rename dataframe columns so that they're queryable in postgresql
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

#generates technical indicators
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




	