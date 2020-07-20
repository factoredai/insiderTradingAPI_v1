from flask_restful import reqparse, Resource
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os 
from flask import send_file
import sys

#from evaluate import Eval
sys.path.insert(0, '../')
print(sys.path)

parser = reqparse.RequestParser()
parser.add_argument('query')

class PlotGenerator(Resource):
    def __init__(self, dict_frames={}, ticker_name=None):
        super(PlotGenerator, self).__init__()
        self.dict_frames = dict_frames
        self.ticker_name = ticker_name
    def post(self):
        # use parser and find the user's query
        parser = reqparse.RequestParser()
        parser.add_argument('ticker', type=str, required=True, help='Company ticker')

        args = parser.parse_args()
        ticker = args['ticker']
        val = self.dict_frames[ticker]
        val = val.drop(columns=["Dividends", "Stock Splits"])
        fig, ax1 = plt.subplots(figsize=(30,12))
        ax2 = ax1.twinx()
        ax1.plot(val["Close"], color="k")
        ax1.errorbar(val.index, val["Close"], yerr=[val["Close"]-val["Low"], val["High"]-val["Close"]], fmt=".",
                    color="k", ecolor='y', capthick=2, label="Close Price (Low/High error)")
        if "S_transactionpricepershare" in val.columns:
            ax1.plot(val.index, val["S_transactionpricepershare"], "o", color="g", label="Sell insider price")
        if "P_transactionpricepershare" in val.columns:
            ax1.plot(val.index, val["P_transactionpricepershare"], "o", color="r", label="Purchase insider price")
        if "M_transactionpricepershare" in val.columns:
            ax1.plot(val.index, val["M_transactionpricepershare"], "o", color="b", label="Derivative Conversion insider price")
        ax1.legend(loc=2)        
        #ax2.bar(val.index, val["Volume"], 1, alpha=0.1, color="b", label="Volume")
        if "S_transactionshares" in val.columns:
            ax2.bar(val.index, val["S_transactionshares"], 1, alpha=0.5, color="g", label="Sell insider")
        if "P_transactionshares" in val.columns:
            ax2.bar(val.index, val["P_transactionshares"], 1, alpha=0.5, color="r", label="Purchase insider")
        if "A_transactionshares" in val.columns:
            ax2.bar(val.index, val["A_transactionshares"], 1, alpha=0.3, color="k", label="Award insider")
        if "M_transactionshares" in val.columns:
            ax2.bar(val.index, val["M_transactionshares"], 1, alpha=0.5, color="b", label="Derivative Conversion insider")
        ax2.legend(loc=1)
        #plt.boxplot(data, positions=x, notch=True)
        plt.title(self.ticker_name[ticker])
        plt.savefig('plot.png')
        matplotlib.use('agg')

        return send_file(os.getcwd() + '/plot.png', as_attachment=True)
