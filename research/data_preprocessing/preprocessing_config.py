#needs to contain grab_data and ma_pct_diff
#various shared filepaths
import numpy as np
import pandas as pd
from numpy import load
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

localengine = create_engine(f'postgresql://postgres:pwd@localhost/dbg_research')

vanilla_data = '/Users/timothygould/dbg_research/research/training_data/vanilla_data/'
standard_norm = '/Users/timothygould/dbg_research/research/training_data/standard_norm/'
zero_to_one = '/Users/timothygould/dbg_research/research/training_data/zero_to_one_norm/'


def grab_data(function,engine):
	data = pd.read_sql_query(f'SELECT * FROM {function}_data',engine)
	
	labels = pd.read_sql_query(f'SELECT * FROM {function}_labels',engine)
	
	keys = pd.read_sql_query(f'SELECT DISTINCT key FROM {function}_labels',engine)

	norm_metrics = pd.read_sql_query('SELECT * FROM norm_metrics',engine)
	
	return data,labels,keys,norm_metrics


def ma_pct_diff(df):
	df['ma200'] = ((df['ma200']-df['adj_close'])/df['ma200'])*100
	df['ma150'] = ((df['ma150']-df['adj_close'])/df['ma150'])*100
	df['ma100'] = ((df['ma100']-df['adj_close'])/df['ma100'])*100
	df['ma75'] = ((df['ma75']-df['adj_close'])/df['ma75'])*100
	df['ma50'] = ((df['ma50']-df['adj_close'])/df['ma50'])*100
	df['ma35'] = ((df['ma35']-df['adj_close'])/df['ma35'])*100
	df['ma25'] = ((df['ma25']-df['adj_close'])/df['ma25'])*100
	df['ma15'] = ((df['ma15']-df['adj_close'])/df['ma15'])*100
	df['ma10'] = ((df['ma10']-df['adj_close'])/df['ma10'])*100

	return df