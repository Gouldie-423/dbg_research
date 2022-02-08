import numpy as np
import pandas as pd
from numpy import load
import data_processing as dp
import preprocessing_config as config

def load_data(path):
	train_x=np.load(f'{path}train_x.npy',allow_pickle=True,fix_imports=True,encoding='latin1')
	train_y=np.load(f'{path}train_y.npy',allow_pickle=True,fix_imports=True,encoding='latin1')
	test_x=np.load(f'{path}test_x.npy',allow_pickle=True,fix_imports=True,encoding='latin1')
	test_y=np.load(f'{path}test_y.npy',allow_pickle=True,fix_imports=True,encoding='latin1')

	return train_x,train_y,test_x,test_y
#running through 10k diff tx and key combos
def spot_check(training_matrix,train_data,keys,threshold):
	
	failed_tests = 0
	
	for i in range(0,threshold):
		if i % 1000 == 0:
			print(i)
		check = np.random.randint(len(keys))
		tx = np.random.randint(60)
		datapoint = train_data[train_data['keys']==str(keys[check])].copy()
		record = datapoint[datapoint['tx']==tx].copy()
		record.drop(['ticker','keys','date','tx'],inplace=True,axis=1)

		if np.allclose(np.squeeze(record.values),train_x[:,check,tx],equal_nan=False) == False:
			print(f'Fail on {keys[check]} timestep:{tx}')
			print(np.squeeze(record.values))
			print(train_x[:,check,tx])
			failed_tests+=1
		else:
			pass

	return failed_tests

def full_test(training_matrix,training_data,keys):
	# tests 
	training_data = training_data.fillna(0)
	failed_tests_full = 0
	for key in range(0,len(keys)): #each unique key 
		datapoint = training_data[training_data['keys']==str(keys[key])].copy()
		if key % 100 == 0:
			print(key)
		for tx in range(0,60): #60 time steps in each datapoint
			record = datapoint[datapoint['tx']==tx].copy()
			record.drop(['ticker','keys','date','tx'],inplace=True,axis=1)

			if np.allclose(np.squeeze(record.values),train_x[:,key,tx],equal_nan=True) == False:
				print(f'failed test {keys[key]}')
				print(np.squeeze(record.values))
				print(train_x[:,key,tx])
				failed_tests_full+=1

	return failed_tests_full


paths = {None:config.vanilla_data,
		'standard':config.standard_norm,
		'zero_to_one':config.zero_to_one}

#final checkh
for k,v in paths.items():

	training_data,training_labels,training_keys,norm_metrics = config.grab_data('train',config.localengine)
	keys = training_keys.values.tolist()
	keys = list(np.concatenate(keys).flat)

	train_x,train_y,test_x,test_y = load_data(v)

	train_data = dp.normalize_data(training_data,norm_metrics,norm_type=k)
	# failed_tests = spot_check(train_x,train_data,keys,20_000)
	failed_tests_full = full_test(train_x,training_data,keys)
	print(f'Normalization: {k}\nFull Dataset Failed Tests: {failed_tests_full}')
