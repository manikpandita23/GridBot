import ccxt
import config
import time
import sys
import websocket
import json

# Connect to WebSocket server
ws = websocket.WebSocket()
ws.connect("ws://localhost:9001")

# Establish connection to the exchange
exchange = ccxt.ftxus({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY
})

# Fetch ticker information
ticker = exchange.fetch_ticker(config.SYMBOL)

# Initialize lists to track buy and sell orders
buy_orders = []
sell_orders = []
closed_orders = []

# Submit initial buy and sell orders based on configured grid lines
for i in range(config.NUM_BUY_GRID_LINES):
    price = ticker['bid'] - (config.GRID_SIZE * (i+1))
    print(f"Submitting market limit buy order at {price}")
    order = exchange.create_limit_buy_order(config.SYMBOL, config.POSITION_SIZE, price)
    buy_orders.append(order['info'])

for i in range(config.NUM_SELL_GRID_LINES):
    price = ticker['bid'] + (config.GRID_SIZE * (i+1))
    print(f"Submitting market limit sell order at {price}")
    order = exchange.create_limit_sell_order(config.SYMBOL, config.POSITION_SIZE, price)
    sell_orders.append(order['info'])

# Main loop to monitor and manage orders
while True:
    # Send order information via WebSocket
    ws.send(json.dumps(buy_orders + sell_orders + closed_orders))
    
    # Initialize list to track closed order IDs
    closed_order_ids = []

    # Check status of buy orders
    for buy_order in buy_orders:
        print(f"Checking buy order {buy_order['id']}")
        try:
            order = exchange.fetch_order(buy_order['id'])
            order_info = order['info']
            if order_info['status'] == config.CLOSED_ORDER_STATUS:
                closed_orders.append(order_info)
                closed_order_ids.append(order_info['id'])
                print(f"Buy order executed at {order_info['price']}")
                new_sell_price = float(order_info['price']) + config.GRID_SIZE
                print(f"Creating new limit sell order at {new_sell_price}")
                new_sell_order = exchange.create_limit_sell_order(config.SYMBOL, config.POSITION_SIZE, new_sell_price)
                sell_orders.append(new_sell_order)
            time.sleep(config.CHECK_ORDERS_FREQUENCY)
        except Exception as e:
            print("Request failed, retrying:", str(e))

    # Check status of sell orders
    for sell_order in sell_orders:
        print(f"Checking sell order {sell_order['id']}")
        try:
            order = exchange.fetch_order(sell_order['id'])
            order_info = order['info']
            if order_info['status'] == config.CLOSED_ORDER_STATUS:
                closed_orders.append(order_info)
                closed_order_ids.append(order_info['id'])
                print(f"Sell order executed at {order_info['price']}")
                new_buy_price = float(order_info['price']) - config.GRID_SIZE
                print(f"Creating new limit buy order at {new_buy_price}")
                new_buy_order = exchange.create_limit_buy_order(config.SYMBOL, config.POSITION_SIZE, new_buy_price)
                buy_orders.append(new_buy_order)
            time.sleep(config.CHECK_ORDERS_FREQUENCY)
        except Exception as e:
            print("Request failed, retrying:", str(e))

    # Remove closed orders from lists
    buy_orders = [buy_order for buy_order in buy_orders if buy_order['id'] not in closed_order_ids]
    sell_orders = [sell_order for sell_order in sell_orders if sell_order['id'] not in closed_order_ids]

    # Check if there are no sell orders left and exit the loop
    if len(sell_orders) == 0:
        sys.exit("Stopping bot, nothing left to sell")
