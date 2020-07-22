import sys

from flask import Flask
from flask_restful import abort, Api
from resources import PlotGenerator
import finviz
import pandas as pd
import numpy as np
import quandl
import yfinance as yf
import matplotlib.pyplot as plt
import os

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
quandl.ApiConfig.api_key = "txYdeX4SX2NxGzzJYsLT"

app = Flask(__name__)
api = Api(app)

# Setup the Api resource routing here
# Route the URL to the resource
valid_transactioncode = ["A", "P", "S", "M"]
data = quandl.get_table("SHARADAR/SF2", paginate=True)
data = data.dropna(subset=["transactiondate"])
data = data.sort_values(["transactiondate"], ascending=False)
data = data[data["transactioncode"].isin(valid_transactioncode)]
symbols = data["ticker"].unique()
ticker2name = data[["ticker", "issuername"]].drop_duplicates().\
                set_index("ticker").to_dict()["issuername"]

dict_frames = {}
amount_negotiated_avg = pd.DataFrame()
for symbol in symbols:
    curr_table = pd.pivot_table(data[data["ticker"]==symbol], 
                                values=["transactionshares", 
                                        "transactionpricepershare", 
                                        "transactionvalue"], 
                                index=['transactiondate'],
                                columns=['transactioncode'], 
                                aggfunc={"transactionshares": np.sum, 
                                        "transactionpricepershare": np.mean,
                                        "transactionvalue": np.sum})
    curr_table.columns = [code + "_" + transaction for transaction, code in curr_table.columns]
    serie = yf.Ticker(symbol)
    stock_df = serie.history(start=data["transactiondate"].min(), 
                             end=data["transactiondate"].max(), 
                             interval="1d")
    dict_frames[symbol] = stock_df.merge(curr_table, how="left", left_index=True, right_index=True)
    
    dict_frames[symbol]["Amount_negotiated"] = dict_frames[symbol]["Volume"]*dict_frames[symbol]["Close"]
    dict_frames[symbol]["Amount_negotiated_MA"] = dict_frames[symbol]["Amount_negotiated"].rolling(5).mean().shift(1)
    dict_frames[symbol]["Perc_amount_vs_MA"] = dict_frames[symbol]["Amount_negotiated"]\
                                                /dict_frames[symbol]["Amount_negotiated_MA"]
    if len(amount_negotiated_avg)<1:
        amount_negotiated_avg[symbol] = dict_frames[symbol]["Amount_negotiated"]
    else:
        amount_negotiated_avg[symbol] = dict_frames[symbol]["Amount_negotiated"]

amount_negotiated_avg = amount_negotiated_avg.mean(axis=1)
for key, val in dict_frames.items():
    dict_frames[key]["Perc_amount_sp100"] = dict_frames[key]["Amount_negotiated"]/amount_negotiated_avg    

api.add_resource(PlotGenerator, '/generate_plot', resource_class_kwargs={'dict_frames':dict_frames, 
                                                                    'ticker_name':ticker2name})


if __name__ == '__main__':
    app.run(debug=True)