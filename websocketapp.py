import ccxt
import config
import time
import sys

def create_order(exchange, symbol, order_type, quantity, price):
    try:
        if order_type == 'buy':
            order = exchange.create_limit_buy_order(symbol, quantity, price)
        elif order_type == 'sell':
            order = exchange.create_limit_sell_order(symbol, quantity, price)
        else:
            raise ValueError("Invalid order type")
        return order
    except Exception as e:
        print(f"Error creating {order_type} order: {str(e)}")
        return None

def fetch_order_status(exchange, order_id):
    try:
        order = exchange.fetch_order(order_id)
        return order['info']['status']
    except Exception as e:
        print(f"Error fetching order status: {str(e)}")
        return None

def main():
    exchange = ccxt.ftxus({
        'apiKey': config.API_KEY,
        'secret': config.SECRET_KEY
    })

    symbol = config.SYMBOL
    ticker = exchange.fetch_ticker(symbol)
    buy_orders = []
    sell_orders = []

    for i in range(config.NUM_BUY_GRID_LINES):
        price = ticker['bid'] - (config.GRID_SIZE * (i+1))
        print(f"Submitting market limit buy order at {price}")
        order = create_order(exchange, symbol, 'buy', config.POSITION_SIZE, price)
        if order:
            buy_orders.append(order['info'])

    for i in range(config.NUM_SELL_GRID_LINES):
        price = ticker['bid'] + (config.GRID_SIZE * (i+1))
        print(f"Submitting market limit sell order at {price}")
        order = create_order(exchange, symbol, 'sell', config.POSITION_SIZE, price)
        if order:
            sell_orders.append(order['info'])

    while True:
        closed_order_ids = []

        for buy_order in buy_orders:
            order_status = fetch_order_status(exchange, buy_order['id'])
            if order_status == config.CLOSED_ORDER_STATUS:
                closed_order_ids.append(buy_order['id'])
                print(f"Buy order executed at {buy_order['price']}")
                new_sell_price = float(buy_order['price']) + config.GRID_SIZE
                print(f"Creating new limit sell order at {new_sell_price}")
                new_sell_order = create_order(exchange, symbol, 'sell', config.POSITION_SIZE, new_sell_price)
                if new_sell_order:
                    sell_orders.append(new_sell_order['info'])
            time.sleep(config.CHECK_ORDERS_FREQUENCY)

        for sell_order in sell_orders:
            order_status = fetch_order_status(exchange, sell_order['id'])
            if order_status == config.CLOSED_ORDER_STATUS:
                closed_order_ids.append(sell_order['id'])
                print(f"Sell order executed at {sell_order['price']}")
                new_buy_price = float(sell_order['price']) - config.GRID_SIZE
                print(f"Creating new limit buy order at {new_buy_price}")
                new_buy_order = create_order(exchange, symbol, 'buy', config.POSITION_SIZE, new_buy_price)
                if new_buy_order:
                    buy_orders.append(new_buy_order['info'])
            time.sleep(config.CHECK_ORDERS_FREQUENCY)

        buy_orders = [buy_order for buy_order in buy_orders if buy_order['id'] not in closed_order_ids]
        sell_orders = [sell_order for sell_order in sell_orders if sell_order['id'] not in closed_order_ids]

        if len(sell_orders) == 0:
            sys.exit("Stopping bot, nothing left to sell")

if __name__ == "__main__":
    main()
