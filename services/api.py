from nitric.resources import api
from nitric.application import Nitric
from nitric.context import HttpContext
import yfinance as yf

main = api("finance-api")

@main.get("/stock-data")
async def stock_data(ctx: HttpContext):
    try:
        tickers = ctx.req.query.get('tickers')
        if not tickers:
            ctx.res.status = 400
            ctx.res.body = {"error": "Missing 'tickers' parameter"}
            return

        if isinstance(tickers, list):
            tickers = tickers[0]

        time_period = ctx.req.query.get('time_period', '1mo')
        data_intervals = ctx.req.query.get('data_intervals', '1d')
        if isinstance(data_intervals, list):
            data_intervals = data_intervals[0]
        print("🔍 Fetching:", tickers, time_period, data_intervals)

        valid_intervals = ["1d", "5d", "1wk", "1mo", "3mo"]
        if data_intervals not in valid_intervals:
            ctx.res.json = {
                "error": f"Invalid data interval. Choose from {valid_intervals}."
            }
            return

        # Updated line using yf.download
        data = yf.download(tickers, period=time_period, interval=data_intervals)

        if data.empty:
            ctx.res.status = 404
            ctx.res.body = {"error": "No data found for the given parameters"}
            return

        ctx.res.json = data.to_dict()

    except Exception as e:
        ctx.res.status = 500
        ctx.res.body = {"error": str(e)}

Nitric.run()
