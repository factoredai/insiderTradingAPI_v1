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

api.add_resource(PlotGenerator, '/generate_plot', resource_class_kwargs={'dict_frames':dict_frames, 
                                                                    'ticker_name':ticker2name})


if __name__ == '__main__':
    app.run(debug=True)