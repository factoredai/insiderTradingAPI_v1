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
import matplotlib.pyplot as plt

def infer_year(current_month, current_year):
    dict_cont = {}
    dict_cont["current_year"] = current_year
    dict_cont["previous_month"] = current_month
    def _infer_year(x):
        delta_months = dict_cont["previous_month"] - x
        if x>=1 and delta_months>=0:
            dict_cont["previous_month"] = x
        else:
            dict_cont["previous_month"] = x
            dict_cont["current_year"]-=1
        return dict_cont["current_year"]
    return _infer_year

def data_layer(sp_100_file, data_path, perc_space, perc_time):
    sp_100_df = pd.read_csv(sp_100_file)
    simbols = sp_100_df.Symbol.values[:-1]
    map_month2month_number = dict((v,k) for k,v in enumerate(calendar.month_abbr))
    stock = {}
    cont = 0
    for simbol in simbols:
        try:
            insider_info = fz.get_insider(simbol)
            insider_data = pd.DataFrame.from_dict(insider_info)
            insider_data[["month_name", "day"]]= insider_data.Date.str.split(" ", expand=True)
            insider_data["month"] = insider_data["month_name"].map(map_month2month_number)
            insider_data["year"] = insider_data["month"].apply(infer_year(datetime.datetime.now().month,
                                                                        datetime.datetime.now().year))
            insider_data["date"] = pd.to_datetime(insider_data[["year", "month", "day"]], format="%y%m%d") 
            cont = cont + 1
        except Exception as inst:
            print(simbol, end=" ")
            print(type(inst), end=" ")# the exception instance
            print(inst) 
            continue
        curr_ticker = yf.Ticker(simbol)
        curr_hist = curr_ticker.history(period="1y")
        curr_table = pd.pivot_table(insider_data,
                                    index=['date'],
                                    columns=['Transaction'], aggfunc={"Transaction": len})
        curr_table = ~curr_table.isnull()
        curr_table.columns = [col[1] for col in curr_table.columns]
        curr_hist = curr_hist.merge(curr_table, how="left", left_index=True, right_index=True)
        curr_hist = curr_hist.fillna(False)
        if "Buy" not in curr_hist.columns:
            curr_hist["Buy"] = False
        if "Sale" not in curr_hist.columns:
            curr_hist["Sale"] = False
        if "Option Exercise" not in curr_hist.columns:
            curr_hist["Option Exercise"] = False
        stock[simbol] = curr_hist

        n_train_space = int(len(stock.keys())*perc_space)
        n_train_out_space = len(stock.keys())-n_train_space

        train_space = np.random.choice(list(stock.keys()), size=n_train_space, replace=False).tolist()
        test_space = list(set(stock.keys()) - set(train_space))
    return stock

def get_dataset(stocks, space, train_samples=None, window_size=21):
    train_datasets = []
    expected_columns = ["Open", "High", "Low", "Close", "Volume", "Dividends", 
                        "Stock Splits", "Buy", "Option Exercise", "Sale"]
    if train_samples is not None:
        valid_datasets = []
    print("Companies: ", space)
    for company in space:
        curr_hist = stocks[company]
        stocks[company] = stocks[company].astype({'Open': np.float64,
                                                  'High': np.float64,
                                                  'Low': np.float64,
                                                  'Close': np.float64,
                                                  'Volume': np.float64,
                                                  'Dividends': np.float64,
                                                  'Stock Splits': np.float64,
                                                  'Buy': np.float64,
                                                  'Option Exercise': np.float64,
                                                  'Sale': np.float64})
        if (stocks[company].columns==expected_columns).all():
            pass
        else:
            stocks[company] = stocks[company][expected_columns]
        assert (stocks[company].columns==expected_columns).all(), "Order of columns is different"
        dataset = tf.data.Dataset.from_tensor_slices(stocks[company].values)
        dataset = dataset.window(window_size, shift=1, drop_remainder=True)
        dataset = dataset.flat_map(lambda window: window.batch(window_size))
        dataset = dataset.map(lambda window: (window[:-1], window[-1:, -3:]))
        if train_samples is not None:
            train_datasets.append(dataset.take(train_samples))
            valid_datasets.append(dataset.skip(train_samples))
        else:
            train_datasets.append(dataset)

    train_ds = None
    if train_samples is not None:
        val_ds = None
    for idx, sample in enumerate(train_datasets):
        if train_ds is None:
            train_ds = sample
            if train_samples is not None:
                val_ds = valid_datasets[idx]
        else:
            train_ds = train_ds.concatenate(sample)
            if train_samples is not None:
                val_ds = val_ds.concatenate(valid_datasets[idx])
    if train_samples is not None:
        return train_ds, val_ds
    else:
        return train_ds

def hist_multi_plot(data, col, hue, title=None, bins=100, figsize=None,
                    deviations=5):
    """
    Multi class kde plot
    Parameters:
    -----------
    data : pd.DataFrame
        Data which contains the columns
    col : str
        Column name in df to plot
    hue : str
        Column name of multiclass
    """
    data = data.copy()
    if figsize is not None:
        plt.figure(figsize=figsize)
    else:
        plt.figure()
    classes = np.sort(data[hue].unique())
    mean = data[col].mean()
    std = data[col].std()
    data = data[((data[col] < (mean+deviations*std)) & (data[col] > (mean-deviations*std)))]
    for class_i in classes:
        temp = data[data[hue] == class_i][col]
        _, bins, _ = plt.hist(
            temp[~np.isnan(temp)], bins=bins, alpha=0.3, density=True, label=class_i)
    plt.legend()
    plt.title(col)