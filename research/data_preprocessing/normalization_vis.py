import numpy as np
import pandas as pd
from numpy import load
import matplotlib.pyplot as plt
import preprocessing_config as config

def normalize_zero_to_one(train_data):
	# train_data.drop(['ticker','keys','date','tx'],inplace=True,axis=1)
	print(train_data.min())
	train_data = config.ma_pct_diff(train_data)
	print(train_data['ma200'].min())
	train_max = train_data.max()
	train_min = train_data.min()
	print(train_min)
	for i in train_data.columns:
		if train_data[i].dtype == float:
			train_data[i] = (train_data[i] - train_min[i]) / (train_max[i] - train_min[i])
		else:
			pass
	return train_data,train_max,train_min

def normalize_standard(train_data):
	train_data = config.ma_pct_diff(train_data)
	train_mean = train_data.mean()
	train_std = train_data.std()
	for i in train_data.columns:
		if train_data[i].dtype == float:
			train_data[i] = (train_data[i]-train_mean[i])/train_std[i]
		else:
			pass
	return train_data,train_mean.to_frame(),train_std.to_frame()

def norm_export_db(train_mean,train_std,train_max,train_min,train_data):
	metrics = {'train_mean':train_mean,'train_std':train_std,'train_max':train_max,'train_min':train_min}
	train_data.drop(['ticker','keys','date','tx'],inplace=True,axis=1)
	columns = train_data.columns.tolist()
	for label,metric in metrics.items():
		print(metric)
		export_dict = {'metric':str(label),'key':'2010/01/01-2019/12/31'}
		metric = np.squeeze(metric.values).tolist()
		for i in range(0,len(columns)):
			if metric[i] == str:
				print(metric[i])
				export_dict[str(columns[i])] = metric[i+1]
			else:
				print(columns[i])
				print(metric[i])
				print(metric[i+1])
				export_dict[str(columns[i])] = metric[i+1]

		export = pd.DataFrame(export_dict,index=[-1])
		export.to_sql('norm_metrics',config.localengine,if_exists='append',index=False)

def export_vis(train_data):

	for key in range(0,len(keys)):
		datapoint = train_data[train_data['keys']==keys[key]].copy()
		dates = datapoint['tx'].values.tolist()
		ax1 = plt.subplot2grid((8,1),(0,0),rowspan = 2,colspan = 1)
		ax2 = plt.subplot2grid((8,1),(2,0),rowspan = 2,colspan = 1)
		ax3 = plt.subplot2grid((8,1),(4,0),rowspan = 2,colspan = 1)
		ax4 = plt.subplot2grid((8,1),(6,0),rowspan = 2,colspan = 1)
		ax1.set_ylim([-1.5,1.5])
		ax2.set_ylim([-1.5, 1.5])
		ax3.set_ylim([-1.5,1.5])
		ax4.set_ylim([-1.5,1.5])
		#cold = slow
		#hot = fast
		#roygbiv
		ax1.plot(dates,datapoint['ma200'].values.tolist(),c='black',label='ma200')
		ax1.plot(dates,datapoint['ma150'].values.tolist(),c='grey',label='ma150')
		ax1.plot(dates,datapoint['ma100'].values.tolist(),c='violet',label='ma100')
		ax1.plot(dates,datapoint['ma75'].values.tolist(),c='indigo',label='ma75')
		ax1.plot(dates,datapoint['ma50'].values.tolist(),c='blue',label='ma50')
		ax1.plot(dates,datapoint['ma35'].values.tolist(),c='green',label='ma35')
		ax1.plot(dates,datapoint['ma25'].values.tolist(),c='yellow',label='ma25')
		ax1.plot(dates,datapoint['ma15'].values.tolist(),c='orange',label='ma15')
		ax1.plot(dates,datapoint['ma10'].values.tolist(),c='red',label='ma10')
		# ax1.set_ylim([.5,.9])
		ax1.set_title(keys[key])
		ax1.hlines(y=0,xmin=dates[0],xmax=dates[-1],linewidth=2)
		ax1.legend(loc='upper left')

		ax2.plot(dates,datapoint['rsi50'].values.tolist(),c='violet',label='rsi50')
		ax2.plot(dates,datapoint['rsi20'].values.tolist(),c='red',label='rsi20')
		# ax2.set_ylim([0,.9])
		ax2.legend(loc='center left')

		ax3.plot(dates,datapoint['macd'].values.tolist(),c='red',label='macd')
		ax3.plot(dates,datapoint['signal'].values.tolist(),c='green',label='signal')
		ax3.plot(dates,datapoint['macd_diff'].values.tolist(),c='blue',label='macd_diff')
		# ax3.set_ylim([.3,.75])
		ax3.legend(loc='center left')

		ax4.plot(dates,datapoint['vol_as_pct'].values.tolist(),c='blue',label='volume as pct')
		# ax4.set_ylim([-.1,.1])

		ax4.legend(loc='center left')
		plt.savefig(f"/Users/timothygould/dbg_research/research/indicator_vis/standard/{keys[key]}")



train_data,train_labels,train_keys,norm_metrics = config.grab_data('train',config.localengine)

keys = train_keys.values.tolist()
keys = list(np.concatenate(keys).flat)

# train_data,train_max,train_min = normalize_zero_to_one(train_data)

# export_vis(train_data)

# train_data,train_labels,train_keys = config.grab_data('train',config.localengine)

train_data,train_mean,train_std = normalize_standard(train_data)
export_vis(train_data)

# norm_export_db(train_mean,train_std,train_max,train_min,train_data)
