# from evaluate import Eval
from web.api_utils import visualization_insider_stock


def generate_plot(dict_frames, ticker_name, ticker):
    # use parser and find the user's query
    val = dict_frames[ticker]
    visualization_insider_stock(ticker, val, ticker_name,
                                save_path="insider_plot.png", from_api=True)
