from datetime import datetime
from secedgar.filings import Filing, FilingType
import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib

# Params mpl
size = 15
font = {'weight': 'bold',
        'size': size}
params = {'legend.fontsize': size*0.7,
          'figure.figsize': (30, 8),
          'axes.labelsize': size,
          'axes.titlesize': size,
          'axes.titleweight': "bold",
          'xtick.labelsize': size*0.9,
          'ytick.labelsize': size*0.9,
          'axes.formatter.limits': (-4, 4),
          'legend.fancybox': True,
          'legend.framealpha': 0.5,
          'legend.title_fontsize': size*0.8}
matplotlib.rcParams.update(params)


def create_dir(directory):
    """Creates directory if not exists"""
    if os.path.isfile(directory):
        raise ValueError("Is a file")

    if not(os.path.exists(directory)):
        os.mkdir(directory)


def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


def download_filing_4(symbol, data_filings_path,
                      start_date=datetime(2019, 7, 1),
                      end_date=datetime(2020, 6, 30)):
    """
    Download Form 4 from SEC
    Downloads all the info about the form 4 in multiple txt files.
    TODO:
    Look if it overwrites.
    Save a file with metadata of already looked dates.
    Create a folder for the symbol and for the looked filing
    """
    current_path = os.path.join(data_filings_path, symbol.lower())
    if not(os.path.exists(current_path)):
        filing = Filing(cik_lookup=symbol.lower(),
                        filing_type=FilingType.FILING_4,
                        start_date=start_date,
                        end_date=end_date)
        filing.save(data_filings_path)
    else:
        print("Already downloaded")


def read_all_form_4(data_filings_path):
    data = pd.DataFrame(columns=['transactiondate', 'transactionshares',
                                 'transactionpricepershare',
                                 'transactioncode', 'officerTitle',
                                 'rptOwnerName', 'issuername', 'ticker'])
    for company in os.listdir(data_filings_path):
        company_path = os.path.join(data_filings_path, company)
        for form in os.listdir(company_path):
            company_form_path = os.path.join(company_path, form)
            files = os.listdir(company_form_path)
            for file in files:
                form_4 = open(os.path.join(company_form_path, file), "r")
                sec_form_raw = form_4.read()
                index_begin = sec_form_raw.find("FORM TYPE")
                index_end = sec_form_raw.find("SEC ACT")
                if not(sec_form_raw[index_begin:index_end].split("\t\t")[1]
                       .replace("\n", "") == '4'):
                    # print("Not Form 4 -",file)
                    continue
                else:
                    # print("Form 4 -", file)
                    pass
                index_begin_xml = sec_form_raw.find('<?xml version="1.0"?>')
                index_end_xml = sec_form_raw.find('</XML>')
                sec_form_processed = sec_form_raw[index_begin_xml:
                                                  index_end_xml]

                try:
                    root = ET.fromstring(sec_form_processed)
                except Exception as e:
                    print(e)
                    print(file)
                    # print(sec_form_processed)
                row = {}
                for x in root.iter('transactionDate'):
                    row['transactiondate'] = x[0].text
                for x in root.iter('transactionShares'):
                    txt = x[0].text
                    # if "." in txt:
                    #     print(company, txt)
                    #     txt = txt.replace(".", "")
                    row['transactionshares'] = txt
                for x in root.iter('transactionPricePerShare'):
                    row['transactionpricepershare'] = x[0].text
                for x in root.iter('transactionCode'):
                    row['transactioncode'] = x.text
                for x in root.iter('officerTitle'):
                    row['officerTitle'] = x.text
                for x in root.iter('rptOwnerName'):
                    row['rptOwnerName'] = x.text
                for x in root.iter('issuerName'):
                    row['issuername'] = x.text
                for x in root.iter('issuerTradingSymbol'):
                    row['ticker'] = x.text
                data = data.append(row, ignore_index=True)
    data = data.astype({'transactiondate': np.datetime64,
                        'transactionshares': np.float64,
                        'transactionpricepershare': np.float64,
                        'transactioncode': np.dtype('O'),
                        'officerTitle': np.dtype('O'),
                        'rptOwnerName': np.dtype('O'),
                        'issuername': np.dtype('O'),
                        'ticker': np.dtype('O')})
    data["transactionvalue"] = data["transactionshares"] *\
        data["transactionpricepershare"]
    return data


def create_ticker2name(data):
    ticker2name = data[["ticker", "issuername"]].drop_duplicates()\
        .set_index("ticker").to_dict()["issuername"]
    return ticker2name


def create_combined_data(data, start=datetime(2019, 7, 21)):
    """
    Combined the insider data with the stock daily information
    """
    symbols = data["ticker"].unique()
    dict_frames = {}
    amount_negotiated_avg = pd.DataFrame()
    for symbol in symbols:
        curr_table = pd.pivot_table(data[data["ticker"] == symbol],
                                    values=["transactionshares",
                                            "transactionpricepershare",
                                            "transactionvalue"],
                                    index=['transactiondate'],
                                    columns=['transactioncode'],
                                    aggfunc={"transactionshares": np.sum,
                                             "transactionpricepershare":
                                             InsiderAggregators
                                                 .mean_exclude_le_0,
                                             "transactionvalue": np.sum})
        curr_table.columns = [code + "_" + transaction for transaction,
                              code in curr_table.columns]
        serie = yf.Ticker(symbol)
        stock_df = serie.history(start=data["transactiondate"].min(),
                                 end=data["transactiondate"].max(),
                                 interval="1d")
        dict_frames[symbol] = stock_df.merge(
            curr_table, how="left", left_index=True, right_index=True)
        dict_frames[symbol]["Amount_negotiated"] = dict_frames[symbol]["Volume"] * \
            dict_frames[symbol]["Close"]
        dict_frames[symbol]["Amount_negotiated_MA"] = dict_frames[symbol]["Amount_negotiated"]\
            .rolling(5).mean().shift(1)
        dict_frames[symbol]["Perc_amount_vs_MA"] = dict_frames[symbol]["Amount_negotiated"]\
            / dict_frames[symbol]["Amount_negotiated_MA"]
        if len(amount_negotiated_avg) < 1:
            amount_negotiated_avg[symbol] = dict_frames[symbol]["Amount_negotiated"]
        else:
            amount_negotiated_avg[symbol] = dict_frames[symbol]["Amount_negotiated"]
    amount_negotiated_avg = amount_negotiated_avg.mean(axis=1)
    for key, val in dict_frames.items():
        dict_frames[key]["Perc_amount_sp100"] = dict_frames[key]["Amount_negotiated"] / \
            amount_negotiated_avg
    return dict_frames


def visualization_insider_stock(key, val, ticker2name, save_path=None,
                                from_api=False,
                                start_date=datetime(2019, 7, 21), figsize=(30, 30),
                                codes=["S", "P", "M", "A"],
                                display=["price", "volume",
                                         "relative_volume",
                                         "amount_ma",
                                         "sp100"]):
    """
    Plot the insider trading with the stock information
    Parameters:
    -----------
    key : str
        Key of dict_frames
    val : pd.DataFrame
        Val of dict frame
    save_path : os.path or None
        Path to save the figure
    """
    dict_codes = {
        "S": {"color": "g",
              "label": "Sell",
              "alpha": 0.5},
        "P": {"color": "r",
              "label": "Purchase",
              "alpha": 0.5},
        "M": {"color": "b",
              "label": "Derivative",
              "alpha": 0.5},
        "A": {"color": "k",
              "label": "Award",
              "alpha": 0.3},
        "F": {"color": "purple",
              "label": "Payment w/security",
              "alpha": 0.5},
        "G": {"color": "aqua",
              "label": "Gift",
              "alpha": 0.7}}
    if "Dividends" in val.columns:
        val = val.drop(columns=["Dividends", "Stock Splits"])
    if start_date:
        val = val.loc[val.index >= start_date, :]
    if from_api:
        matplotlib.use('agg')
    if ("amount_ma" in display) and ("sp100" in display):
        n_plots = 3
    elif ("amount_ma" in display) or ("sp100" in display):
        n_plots = 2
    else:
        n_plots = 1
    fig, ax = plt.subplots(n_plots, 1, figsize=figsize)
    if n_plots > 1:
        ax1 = ax[0]
        ax4 = ax[1]
        if ("amount_ma" in display) and ("sp100" in display):
            ax5 = ax[2]
            ax4 = plot_ma_5days(ax4, val)
            ax5 = plot_sp100(ax5, val)
        elif "amount_ma" in display:
            ax4 = plot_ma_5days(ax4, val)
        elif "sp100" in display:
            ax4 = plot_ma_5days(ax4, val)
        else:
            raise SystemExit("Something weird happened about display")
    else:
        ax1 = ax
    ax1.plot(val["Close"], color="k")
    ax1.errorbar(val.index, val["Close"],
                 yerr=[val["Close"]-val["Low"], val["High"]-val["Close"]],
                 fmt=".", color="k", ecolor='y', capthick=2,
                 label="Close Price (Low/High error)")
    for code in codes:
        if f"{code}_transactionpricepershare" in val.columns:
            label = dict_codes[code]["label"]
            color = dict_codes[code]["color"]
            ax1.plot(val.index, val[f"{code}_transactionpricepershare"],
                     "o", color=color, label=f"{label} insider")
    ax1.set_ylabel("Price")
    ax1 = legend_if_exist(ax1, loc=2, title="Price")

    if len(display) > 1:
        if "volume" in display:
            ax2 = ax1.twinx()
            for code in codes:
                if f"{code}_transactionshares" in val.columns:
                    label = dict_codes[code]["label"]
                    color = dict_codes[code]["color"]
                    alpha = dict_codes[code]["alpha"]
                    ax2.bar(val.index, val[f"{code}_transactionshares"], 1,
                            alpha=alpha, color=color,
                            label=f"{label} insider")
            ax2 = legend_if_exist(ax2, loc=1, title="Volume")
            ax2.set_ylabel("Volume")
        if "relative_volume" in display:
            ax3 = ax1.twinx()
            if "volume" in display:
                ax3.spines["right"].set_position(("axes", 1.055))
                make_patch_spines_invisible(ax3)
                ax3.spines["right"].set_visible(True)
            for code in codes:
                if f"{code}_transactionshares" in val.columns:
                    label = dict_codes[code]["label"]
                    color = dict_codes[code]["color"]
                    ax3.plot(val.index,
                             np.abs(val[f"{code}_transactionshares"] /
                                    val["Volume"]),
                             "x", color=color,
                             label=f"{label} insider")
            ax3 = legend_if_exist(ax3, loc=3, title="Relative Volume")
            ax3.set_ylabel("Relative Volume")
    fig.subplots_adjust(hspace=.3)
    plt.title("Insider Trading Events")
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path, bbox_inches='tight')


def legend_if_exist(ax, loc, title):
    handles, labels = ax.get_legend_handles_labels()
    if len(labels) > 0:
        ax.legend(loc=loc, title=title)
    return ax


def barplot_base_centered(ax, values, base=100, width=0.9, alpha=0.7):
    values = values - base
    ax.bar(values[values >= 0].index, values[values >= 0], width=width,
           color="g", alpha=alpha, zorder=3)
    ax.bar(values[values < 0].index, values[values < 0], width=width,
           color="r", alpha=alpha, zorder=4)
    or_yticks = ax.get_yticks()
    transformed_ticks = base + or_yticks
    ax.set_yticklabels(transformed_ticks.astype(np.int64))
    return ax


def plot_ma_5days(ax, val):
    delta = 0
    aux = val["Perc_amount_vs_MA"]*100 - delta
    threshold = 100 - delta
    ax = barplot_base_centered(ax, aux, base=threshold)
    ax.set_ylabel("% Volume")
    legend_if_exist(ax, loc=2, title=None)
    ax.set_title("% Volume relative to MA(5)")
    return ax


def plot_sp100(ax, val):
    color = "steelblue"
    ax.plot(val["Perc_amount_sp100"]*100, linestyle="-",
            color=color, label="% Volume relative to Avg SP500 Company")
    ax.set_ylabel("% Volume")
    ax.set_title("% Volume relative to Avg SP500 Company")
    # legend_if_exist(ax, loc=2, title=None)
    return ax


class InsiderAggregators():
    @staticmethod
    def count(x, label):
        return (x == label).sum()

    @staticmethod
    def total_sell(x):
        return InsiderAggregators.count(x, "S")

    @staticmethod
    def total_options(x):
        return InsiderAggregators.count(x, "M")

    @staticmethod
    def total_awards(x):
        return InsiderAggregators.count(x, "A")

    @staticmethod
    def total_purchase(x):
        return InsiderAggregators.count(x, "P")

    @staticmethod
    def head(x):
        return x.head(1)

    @staticmethod
    def title(x):
        return InsiderAggregators.head(x)

    @staticmethod
    def mean_exclude_le_0(x):
        return x[x > 0].mean()


def calculate_aggregates_per_insider(data, ticker):
    out = data[data["ticker"] == ticker].groupby(["rptOwnerName"])\
        .agg({"officerTitle": InsiderAggregators.title,
              "transactionpricepershare": InsiderAggregators.mean_exclude_le_0,
              "transactionshares": np.sum}).sort_values("transactionshares",
                                                        ascending=False).reset_index()
    out.columns = ["Owner Name", "Officer Title",
                   "Avg Price Per Share", "Shares Traded"]
    out["Officer Title"] = out["Officer Title"].fillna("-")

    aux = data[data["ticker"] == ticker].groupby(["rptOwnerName",
                                                  "transactioncode"])["transactionshares"]\
        .sum().to_frame().unstack(1)
    aux.columns = [code + " Shares Reported" for _, code in aux.columns]
    aux = aux.fillna(0).reset_index()
    aux = aux.rename(columns={"rptOwnerName": "Owner Name"})
    out = out.merge(aux, how="left", on="Owner Name")

    # style_dict = {col: "{:,.0f}" for col in out.columns[4:]}
    # style_dict["Avg Price Per Share"] = "{:.2f}"
    # style_dict["Shares Traded"] = "{:,.0f}"
    # styled_output = out.style.format(style_dict, na_rep="-").hide_index()
    # styled_output = styled_output.set_properties(**{"text-align": "center"})
    return out  # styled_output.render()
