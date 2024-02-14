from websocket_server import WebsocketServer
def new_client(client,server):
    print("New client connected with id %d" %client['id'])
    server.send_message('Hello Client!',client)
def message_received(client, server, message):
    print("Client(%d)sent:%s"%(client['id'], message))
    server.send_message('You said:%s'%message,client)
PORT = 9001
server = WebsocketServer(port=PORT)
server.set_fn_new_client(new_client)
server.set_fn_message_receive(message_received)
server.run_forever()