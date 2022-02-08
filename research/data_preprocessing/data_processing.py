#turn into matrix first to verify results before creating function to normalize data beforehand
import numpy as np
from numpy import save
import pandas as pd
import preprocessing_config as config

def training_data(nx,batch_size,Tx,data,keys,lookback_range):
	
	matrix = np.zeros((nx,batch_size,Tx))
	#need to fillna post normalization
	data = data.fillna(0)

	for key in range(len(keys)-1,len(keys)):#,len(keys)):
		datapoint = data[data['keys']==str(keys[key])]
		diff_padding = (batch_size-len(datapoint))-1
		
		#bumping up tx values so matrix correctly reflects data if < 60 training days
		#to learn from
		if diff_padding > -1:
			pass
		else:
			datapoint['keys'] = datapoint['keys'] + diff_padding
	
		#each dp now isolated. Need to fill in each record in 
		for time in range(len(datapoint)-1,-1,-1):
			data_tx = datapoint[datapoint['tx']==time].copy()
			#remember to change nx if you drop a new column
			data_tx.drop(['ticker','keys','date','tx'],inplace=True,axis=1)
			#rotates counter clockwise
			data_tx = np.rot90(data_tx.values,k=3,axes=(0,1))
			data_tx = np.squeeze(data_tx)
			matrix[:,key,time] = data_tx

	return matrix

def label_data(keys,labels,batch_size):
	#needs to be a (1,batch_size,1) matrix
	matrix = np.zeros((1,batch_size))

	for key in range(1,len(keys)):
	
		datapoint = labels[labels['key']==str(keys[key])].copy()
		result = datapoint['result']
		result = np.squeeze(result.values)
		matrix[0,key] = result
	
	return matrix

def remove_fields(train_data,fields_for_removal,remove=False):

	if remove:
		train_data.drop(fields_for_removal,inplace=True,axis=1)

	else:
		pass

	return train_data		

def normalize_data(train_data,norm_metrics,norm_type=None):
	metrics = norm_metrics['metric'].unique
	train_data = config.ma_pct_diff(train_data)

	train_min = {}
	train_max = {}
	train_std = {}
	train_mean = {}

	if norm_type == 'zero_to_one':
		train_min2 = norm_metrics[norm_metrics['metric']=='train_min'].copy()
		train_max2 = norm_metrics[norm_metrics['metric']=='train_max'].copy()
		train_min2.drop(['metric','key'],inplace=True,axis=1)
		train_max2.drop(['metric','key'],inplace=True,axis=1)

		for column in train_min2.columns:
			train_min[column] = np.squeeze(float(train_min2[column].values))
			train_max[column] = np.squeeze(float(train_max2[column].values))

		for k in train_min.keys():

			train_data[k] = (train_data[k] - train_min[k]) / (train_max[k] - train_min[k])

	if norm_type == 'standard':
		train_std2 = norm_metrics[norm_metrics['metric']=='train_std'].copy()
		train_mean2 = norm_metrics[norm_metrics['metric']=='train_mean'].copy()
		train_std2.drop(['metric','key'],inplace=True,axis=1)
		train_mean2.drop(['metric','key'],inplace=True,axis=1)

		for column in train_mean2.columns:
			train_std[column] = np.squeeze(float(train_std2[column].values))
			train_mean[column] = np.squeeze(float(train_mean2[column].values))

		for k in train_std.keys():
			train_data[k] = (train_data[k]-train_mean[k])/train_std[k]
	
	if norm_type == None:

		train_data = train_data

	return train_data

def process_data(data,labels,keys,norm_metrics,lookback_range,norm_type=None):

	keys = keys.values.tolist()
	keys = list(np.concatenate(keys).flat)
	#had some extra fields in each training record that needs to be discarded
	#just before data is inserted into matrix (keys,ticker symbols,etc).
	#manually putting in nx

	nx = 15
	batch_size = len(keys)
	Tx = 60
	fields_for_removal = ['adj_close','macd_5d','signal_5d','macd_5diff',
		'macd_10d','signal_10d','macd_10diff','rsi30','rsi40']
	remove = True

	if norm_type == 'zero_to_one':
		train_data = normalize_data(data,norm_metrics,norm_type)
		train_data = remove_fields(train_data,fields_for_removal,remove)

		training_matrix = training_data(nx,batch_size,Tx,train_data,keys,lookback_range)
		label_matrix = label_data(keys,labels,batch_size)

		path = config.zero_to_one

	if norm_type == 'standard':
		train_data = normalize_data(data,norm_metrics,norm_type)
		train_data = remove_fields(train_data,fields_for_removal,remove)

		training_matrix = training_data(nx,batch_size,Tx,train_data,keys,lookback_range)
		label_matrix = label_data(keys,labels,batch_size)

		path = config.standard_norm
	
	if norm_type == None:

		train_data = normalize_data(data,norm_metrics,norm_type)
		train_data = remove_fields(train_data,fields_for_removal,remove)

		training_matrix = training_data(nx,batch_size,Tx,train_data,keys,lookback_range)
		label_matrix = label_data(keys,labels,batch_size)
		
		path = config.vanilla_data
	
	return training_matrix,label_matrix,path



# commented out export code so file can quickly be brought into data_processing_test.py as a library

normtype = None
export = False

train_data,train_labels,train_keys,norm_metrics = config.grab_data('train',config.localengine)
test_data,test_labels,test_keys,norm_metrics = config.grab_data('test',config.localengine)

train_matrix,train_label_matrix,path = process_data(train_data,train_labels,train_keys,norm_metrics,lookback_range=60,norm_type = normtype)
test_matrix,test_label_matrix,path = process_data(test_data,test_labels,test_keys,norm_metrics,lookback_range=60,norm_type = normtype)

if export:
	print(f'{path}train_x.npy')
	np.save(f'{path}train_x.npy', train_matrix)
	np.save(f'{path}train_y.npy', train_label_matrix)

	np.save(f'{path}test_x.npy',test_matrix)
	np.save(f'{path}test_y.npy', test_label_matrix)

else:
	pass

