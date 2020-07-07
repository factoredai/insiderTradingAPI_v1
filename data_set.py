import pandas as pd
import tensorflow as tf
import numpy
import pickle as pkl
import os
import finviz as fz
import yfinance as yf
import calendar
import datetime
import numpy as np

def get_data_set_train(WINDOW_SIZE,stock,train_space,train_samples):
    train_datasets = []
    valid_datasets = []
    print("Companies: ", train_space)
    for company in train_space:
        curr_hist = stock[company]
        stock[company] = stock[company].astype({'Open': np.float64,
                            'High': np.float64,
                            'Low': np.float64,
                            'Close': np.float64,
                            'Volume': np.float64,
                            'Dividends': np.float64,
                            'Stock Splits': np.float64,
                            'Buy': np.float64,
                            'Option Exercise': np.float64,
                            'Sale': np.float64})
        dataset = tf.data.Dataset.from_tensor_slices(stock[company].values)
        dataset = dataset.window(WINDOW_SIZE, shift=1, drop_remainder=True)
        dataset = dataset.flat_map(lambda window: window.batch(WINDOW_SIZE))
        dataset = dataset.map(lambda window: (window[:-1], window[-1:, -3:]))
        train_datasets.append(dataset.take(train_samples))
        valid_datasets.append(dataset.skip(train_samples))

        train_ds = None
        val_ds = None
        for sample in zip(train_datasets, valid_datasets):
            if train_ds is None:
                train_ds = sample[0]
                val_ds = sample[1]
            else:
                train_ds = train_ds.concatenate(sample[0])
                val_ds = val_ds.concatenate(sample[1])
        return train_ds, val_ds
        
def get_data_set_test(WINDOW_SIZE,stock,test_space):
    print("Companies: ", test_space)
    test_datasets = []
    for company in test_space:
        curr_hist = stock[company]
        stock[company] = stock[company].astype({'Open': np.float64,
                            'High': np.float64,
                            'Low': np.float64,
                            'Close': np.float64,
                            'Volume': np.float64,
                            'Dividends': np.float64,
                            'Stock Splits': np.float64,
                            'Buy': np.float64,
                            'Option Exercise': np.float64,
                            'Sale': np.float64})
        dataset = tf.data.Dataset.from_tensor_slices(stock[company].values)
        dataset = dataset.window(WINDOW_SIZE, shift=1, drop_remainder=True)
        dataset = dataset.flat_map(lambda window: window.batch(WINDOW_SIZE))
        dataset = dataset.map(lambda window: (window[:-1], window[-1:, -3:]))
        test_datasets.append(dataset)
        test_ds = None
        for sample in test_datasets:
            if test_ds is None:
                test_ds = sample
            else:
                test_ds = test_ds.concatenate(sample)
        return test_ds