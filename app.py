from flask import Flask, render_template
from flask_socketio import SocketIO

# Створення об'єкта Flask
app = Flask(__name__)

# Ініціалізація SocketIO
socketio = SocketIO(app)

# Шлях до головної сторінки
@app.route('/')
def home():
    return render_template('index.html')

# Обробник підключення сокетів
@socketio.on('connect')
def handle_connect():
    print("Клієнт підключений")

# Запуск серверу
if __name__ == '__main__':
    # Запуск через socketio.run() замість app.run()
    socketio.run(app, debug=True)
