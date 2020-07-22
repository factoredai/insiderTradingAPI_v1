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

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

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
        matplotlib.use('agg')
        fig, ax = plt.subplots(2, 1, figsize=(20, 12))
        ax1 = ax[0]
        ax4 = ax[1]
        ax2 = ax1.twinx()
        ax3 = ax1.twinx()
        ax3.spines["right"].set_position(("axes", 1.055))
        # Having been created by twinx, par2 has its frame off, so the line of its
        # detached spine is invisible.  First, activate the frame but make the patch
        # and spines invisible.
        make_patch_spines_invisible(ax3)
        # Second, show the right spine.
        ax3.spines["right"].set_visible(True)
        ax1.plot(val["Close"], color="k")
        ax1.errorbar(val.index, val["Close"], yerr=[val["Close"]-val["Low"], val["High"]-val["Close"]], fmt=".",
                     color="k", ecolor='y', capthick=2, label="Close Price (Low/High error)")
        if "S_transactionpricepershare" in val.columns:
            ax1.plot(val.index, val["S_transactionpricepershare"],
                     "o", color="g", label="Sell insider price")
        if "P_transactionpricepershare" in val.columns:
            ax1.plot(val.index, val["P_transactionpricepershare"],
                     "o", color="r", label="Purchase insider price")
        if "M_transactionpricepershare" in val.columns:
            ax1.plot(val.index, val["M_transactionpricepershare"], "o",
                     color="b", label="Derivative Conversion insider price")
        ax1.legend(loc=2)
        #ax2.bar(val.index, val["Volume"], 1, alpha=0.1, color="b", label="Volume")
        if "S_transactionshares" in val.columns:
            ax2.bar(val.index, val["S_transactionshares"], 1,
                    alpha=0.5, color="g", label="Sell insider")
            ax3.plot(val.index, np.abs(val["S_transactionshares"]/val["Volume"]),
                     "x", color="g", label="Sell relative volume")
        if "P_transactionshares" in val.columns:
            ax2.bar(val.index, val["P_transactionshares"], 1,
                    alpha=0.5, color="r", label="Purchase insider")
            ax3.plot(val.index, np.abs(val["P_transactionshares"]/val["Volume"]),
                     "x", color="r", label="Purchase relative volume")
        if "A_transactionshares" in val.columns:
            ax2.bar(val.index, val["A_transactionshares"], 1,
                    alpha=0.3, color="k", label="Award insider")
            ax3.plot(val.index, np.abs(val["A_transactionshares"]/val["Volume"]),
                     "x", alpha=0.3, color="k", label="Award relative volume")
        if "M_transactionshares" in val.columns:
            ax2.bar(val.index, val["M_transactionshares"], 1, alpha=0.5,
                    color="b", label="Derivative Conversion insider")
            ax3.plot(val.index, np.abs(val["M_transactionshares"]/val["Volume"]),
                     "x", color="b", label="Derivative relative volume")
        ax2.legend(loc=1)
        ax3.legend(loc=3)
        #plt.boxplot(data, positions=x, notch=True)
        ax4_color = "steelblue"
        ax4.plot(val["Perc_amount_vs_MA"]*100, color=ax4_color,
                 label="%Amount traded relative to MA 5 last days")
        ax4.plot(val["Perc_amount_sp100"]*100, linestyle="--",
                 color=ax4_color, label="%Amount relative to SP100")

        ax1.set_ylabel("Price")
        ax2.set_ylabel("Volume")
        ax3.set_ylabel("Relative Volume")
        ax4.set_ylabel("% Percentage")

        # ax3.yaxis.label.set_color(ax3_color)
        #ax3.tick_params(axis='y', colors=ax3_color)
        ax4.legend(loc=2)
        #plt.boxplot(data, positions=x, notch=True)
        plt.title(self.ticker_name[ticker])
        plt.savefig('plot.png')
      

        return send_file(os.getcwd() + '/plot.png', as_attachment=True)
