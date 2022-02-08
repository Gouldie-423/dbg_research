import numpy as np
import pandas as pd
from numpy import load
import os
import torch
import torch.nn as nn

class model:
    
    def __init__(self,data,algorithm,threshold = .65):
        self.data = torch.from_numpy(data)
        self.layers_dims = {'rnn':[data.shape[0],data.shape[0]],'ff':[data.shape[0],3,1]}
        self.algorithm = algorithm
        self.params = {}
        self.threshold = threshold

    def load_params(self):

        for i in range(0,len(self.layers_dims['rnn'])):
            self.params['Waa'+str(i+1)] = torch.load(f'/Users/timothygould/dbg_research/research/models/new_threshold_test/V{self.algorithm}/Waa{str(i+1)}.pt')
            self.params['Wax'+str(i+1)] = torch.load(f'/Users/timothygould/dbg_research/research/models/new_threshold_test/V{self.algorithm}/Wax{str(i+1)}.pt')
            self.params['ba'+str(i+1)] = torch.load(f'/Users/timothygould/dbg_research/research/models/new_threshold_test/V{self.algorithm}/ba{str(i+1)}.pt')

        for i in range(0,len(self.layers_dims['ff'])-1):
            self.params['W'+str(i+1)] = torch.load(f'/Users/timothygould/dbg_research/research/models/new_threshold_test/V{self.algorithm}/W{str(i+1)}.pt')
            self.params['b'+str(i+1)] = torch.load(f'/Users/timothygould/dbg_research/research/models/new_threshold_test/V{self.algorithm}/b{str(i+1)}.pt')


    def ff_forward(self,a):
        a_next = a #need this here so a_next can be overridden inbetween layers
        for i in range(1,len(self.layers_dims['ff'])-1):
            w = self.params['W'+str(i)]
            b = self.params['b'+str(i)]
            z = torch.matmul(w,a_next)+b
            a_next = torch.tanh(z)
        
        w = self.params['W'+str(len(self.layers_dims['ff'])-1)]
        b = self.params['b'+str(len(self.layers_dims['ff'])-1)]
        z = torch.matmul(w,a_next)+b
        y_pred = torch.sigmoid(z)
        
        return y_pred
    
    def rnn_cell_forward(self,layer,a_prev,xt):
        
        Wax = self.params['Wax'+str(layer)]
        Waa = self.params['Waa'+str(layer)]
        ba = self.params['ba'+str(layer)]

        z = torch.matmul(Waa,a_prev)+torch.matmul(Wax,xt)+ba
        a_next = torch.tanh(z)
        
        return a_next
    
    def forward_pass(self):
        
        
        tx = self.data.shape[2]
        
        a_next1 = torch.zeros(self.data.shape[0],self.data.shape[1],dtype = torch.float64)
        a_next2 = torch.zeros(self.data.shape[0],self.data.shape[1],dtype = torch.float64)
        
        for xt in range(tx):
            a_next1 =  self.rnn_cell_forward(1,a_next1,self.data[:,:,xt])
            
            a_next2 = self.rnn_cell_forward(2,a_next2,a_next1)
            
        y_pred = self.ff_forward(a_next2)
        return y_pred
    
    def run(self):
        self.load_params()
        y_pred = self.forward_pass()

        if y_pred >= .65:
            return 'Group A'
        else:
            return 'Group B'


        return y_pred
