from flask import Flask, request
from main import *

app = Flask(__name__)

@bot.event
async def on_message(message):
    # Your existing on_message code...

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Extract the command from the incoming JSON payload
    command = data.get('command')

    # Process the command (add your logic here)
    if command == 'play':
        url = data.get('url')
        bot.loop.create_task(play_music(ctx, url))  # Replace ctx with a valid context

    # Add more command handling as needed...

    return 'Command received'

if __name__ == '__main__':
    app.run(port=5000)  # You can change the port number as needed
