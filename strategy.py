from blueshift.api import symbol, schedule_function, date_rules, time_rules, order_target_percent
import talib as ta

def initialize(context):
    """
    A function to define things to do at the start of the strategy
    """
    context.asset = symbol('HAL')
    context.fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 1.0]  # Fibonacci levels to plot
    context.signal_triggered = False
    context.risk_factor = 0.02
    context.rsi_lookback = 14
    context.rsi_oversold = 30
    context.rsi_overbought = 70
    context.stop_loss_factor = 0.95
    context.atr_period = 14
    context.macd_fast_period = 12
    context.macd_slow_period = 26
    context.macd_signal_period = 9
    context.bb_period = 20
    context.bb_deviation = 2.0
    
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())

def rebalance(context, data):
    # Get historical price data
    prices = data.history(context.asset, 'close', context.macd_slow_period + context.macd_signal_period, '1d')
    close_prices = data.history(context.asset, 'close',15, '1min')
    high_prices = data.history(context.asset, 'high',15, '1min')
    low_prices = data.history(context.asset, 'low',15, '1min')
    atr = ta.ATR(high_prices, low_prices, close_prices, timeperiod=context.atr_period)
    position_size = context.portfolio.portfolio_value * context.risk_factor/atr[-1]
    rsi = ta.RSI(close_prices, timeperiod=context.rsi_lookback)
    macd, macd_signal, _ = ta.MACD(prices, context.macd_fast_period, context.macd_slow_period, context.macd_signal_period)
    BB_prices = data.history(context.asset, 'close', context.bb_period, '1d')
    upper_band, middle_band, lower_band = ta.BBANDS(BB_prices, context.bb_period, context.bb_deviation)
    ma =  data.history(context.asset,'close',50,'1d').mean()

    # Calculate the high and low points for plotting Fibonacci retracement levels
    high = close_prices.max()
    low = close_prices.min()

    # Calculate the Fibonacci retracement levels
    fib_prices = []
    for level in context.fib_levels:
        fib_price = low + level * (high - low)
        fib_prices.append(fib_price)

    # Generate buy and sell signals based on the Fibonacci retracement levels
    current_price = data.current(context.asset, 'close')
    if (rsi[-1] < context.rsi_oversold) and close_prices[-1] > ma and current_price > fib_prices[0] and not context.signal_triggered:
        order_target_percent(context.asset, position_size)
        context.signal_triggered = True
    elif rsi[-1] > context.rsi_overbought and close_prices[-1] < close_prices[-2] and current_price < fib_prices[5] and not context.signal_triggered:
        order_target_percent(context.asset, -position_size)
        context.signal_triggered = True
    
    if context.signal_triggered:
        stop_loss_price = fib_prices[0] * context.stop_loss_factor
        if current_price < lower_band[-1] * context.stop_loss_factor and current_price < stop_loss_price:
            order_target_percent(context.asset, 0)
            context.signal_triggered = False
        else:
            pass  # Hold the position