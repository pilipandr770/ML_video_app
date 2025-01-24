from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import os
from app.tasks import process_video
from config import Config

# Инициализация приложения Flask
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app)

# Инициализация базы данных
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    profit = db.Column(db.Float, default=0.0)

# Главная страница
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Проверка уникальности email
        if User.query.filter_by(email=email).first():
            return "Email already registered", 400

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

# Авторизация пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "Invalid credentials", 400

    return render_template('login.html')

# Выход пользователя
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Личный кабинет пользователя
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            app.logger.info("Начало обработки запроса")
            if 'video' in request.files:
                video = request.files['video']
                if video.filename == '':
                    app.logger.error("Имя файла видео пустое")
                    return jsonify({"error": "Empty filename"}), 400

                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], "live_stream.mp4")
                video.save(filepath)
                app.logger.info(f"Видео сохранено по пути: {filepath}")

                # Ensure the file is properly closed before deletion
                video.close()

                # Check if the file is properly saved
                if not os.path.exists(filepath) or os.path.getsize(filepath) < 1024:  # Minimum size check
                    app.logger.error(f"Видео файл {filepath} не найден или его размер слишком мал: {os.path.getsize(filepath)} байт")
                    raise ValueError("Некорректный файл")
                app.logger.info(f"Видео файл {filepath} успешно сохранён. Размер файла: {os.path.getsize(filepath)} байт")

                # Передаём файл і настройки в обработку
                process_video(filepath, update_dashboard_callback=update_dashboard)
                app.logger.info("Обработка завершена успешно")
                return jsonify({"message": "Видео обработано успешно"}), 200
            else:
                # Обработка сохранения настроек без видео
                language = request.form.get('language')
                topic = request.form.get('topic')
                agreement = 'agreement' in request.form

                # Сохраните настройки пользователя в базе данных или выполните другие действия
                app.logger.info(f"Настройки сохранены: язык={language}, тема={topic}, согласие={agreement}")
                return jsonify({"message": "Настройки сохранены успешно"}), 200
        except Exception as e:
            app.logger.error(f"Ошибка: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500

    user = User.query.get(session['user_id'])
    videos = Video.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, videos=videos)

@socketio.on('connect')
def handle_connect():
    print("Клієнт підключён")

def update_dashboard(sent_parts, failed_parts):
    """Обновление статистики через WebSocket."""
    socketio.emit('update_stats', {'sent_parts': sent_parts, 'failed_parts': len(failed_parts)}, namespace='/')

# Создание базы данных
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)
