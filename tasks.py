import os
import subprocess
from flask import current_app
import cv2
import numpy as np
import requests
from flask_socketio import emit
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_video(file, filename):
    """Збереження відео у тимчасову папку."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath

def get_ffmpeg_path():
    """Повертає шлях до ffmpeg, якщо він доступний у PATH, інакше повертає повний шлях."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True)
        logger.info("FFmpeg знайдено та доступно.")
        return "ffmpeg"
    except FileNotFoundError:
        logger.error("FFmpeg не знайдено у PATH. Використовується повний шлях.")
        # Оновіть цей шлях до коректного місця, де у вас лежить виконавчий файл ffmpeg
        return r"C:\Users\ПК\Downloads\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

def split_video(filepath, output_dir, segment_duration=60):
    """Розбиття відео на частини, ігноруючи аудіо."""
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, 'part_%03d.mp4')
    ffmpeg_path = get_ffmpeg_path()
    command = [
        ffmpeg_path, '-i', filepath, '-c:v', 'libx264', '-an',  # '-an' вимикає аудіо
        '-map', '0', '-segment_time', str(segment_duration), '-f', 'segment', output_template
    ]
    logger.info(f"Запуск команди: {' '.join(command)}")
    logger.info(f"PATH: {os.environ['PATH']}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(result.stdout)
        logger.error(result.stderr)
    except FileNotFoundError:
        logger.error(f"FFmpeg не знайдено за шляхом: {ffmpeg_path}. Перевірте коректність шляху.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Помилка при розбитті відео: {e}")
        logger.error(f"Стандартний вивід помилки: {e.stderr}")
        raise
    return [os.path.join(output_dir, f) for f in os.listdir(output_dir)]

def check_quality(video_path):
    """Перевірка якості відео."""
    command = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration', '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return {"status": "error", "reason": "ffprobe failed"}
    width, height, duration = map(float, result.stdout.strip().split(','))
    if width < 640 or height < 480 or duration < 10:  # Зменшено мінімальні вимоги до якості
        return {"status": "fail", "reason": "low quality"}
    return {"status": "pass"}

def upload_to_openai(video_path, metadata):
    """Відправка відео в OpenAI через API (приклад)."""
    url = "https://api.openai.com/v1/videos"  # Прикладний URL, замініть на актуальний
    headers = {
        'Authorization': f'Bearer {current_app.config["OPENAI_API_KEY"]}'
    }
    with open(video_path, 'rb') as file:
        files = {'file': file}
        data = {'metadata': metadata}
        response = requests.post(url, headers=headers, files=files, data=data)
    return response.status_code == 200

def update_dashboard(sent_parts, failed_parts):
    """Відправка оновлень статистики через WebSocket."""
    emit('update_stats', {'sent_parts': sent_parts, 'failed_parts': len(failed_parts)}, broadcast=True, namespace='/')

def process_video(filepath, update_dashboard_callback=None):
    """Основний процес обробки відео з файлу."""
    current_app.logger.info("Початок обробки відео")
    output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'parts')
    sent_parts = 0
    failed_parts = []

    try:
        # Перевірка, чи файл збережений коректно
        if not os.path.exists(filepath) or os.path.getsize(filepath) < 1024:  # Мінімальна перевірка розміру
            current_app.logger.error(f"Файл відео {filepath} не знайдено або його розмір надто малий: {os.path.getsize(filepath)} байт")
            raise ValueError("Некоректний файл")
        current_app.logger.info(f"Файл відео {filepath} успішно збережено. Розмір файлу: {os.path.getsize(filepath)} байт")

        # Крок 1: Розбиття відео
        parts = split_video(filepath, output_dir)
        emit('update_progress', {'status': 'splitting_video', 'total_parts': len(parts)}, broadcast=True, namespace='/')
        current_app.logger.info(f"Файл відео {filepath} розбито на {len(parts)} частин.")

        # Крок 2: Перевірка якості частин
        valid_parts = []
        for part in parts:
            quality_result = check_quality(part)
            if quality_result["status"] == "pass":
                valid_parts.append(part)
            else:
                failed_parts.append({'part': part, 'reason': quality_result['reason']})
                os.remove(part)  # Видаляємо неякісні частини
            emit('update_progress', {'status': 'checking_quality', 'checked_parts': len(valid_parts)}, broadcast=True, namespace='/')
            current_app.logger.info(f"Перевірка якості частини {part}: {quality_result['status']}")

        # Крок 3: Відправка якісних частин в OpenAI
        for valid_part in valid_parts:
            metadata = {"user_id": "example_user"}  # Приклад метаданих
            if upload_to_openai(valid_part, metadata):
                sent_parts += 1
                os.remove(valid_part)  # Видаляємо частину після відправки
                if update_dashboard_callback:
                    update_dashboard_callback(sent_parts, failed_parts)  # Оновлення статистики
                current_app.logger.info(f"Частину {valid_part} успішно відправлено в OpenAI.")

        current_app.logger.info("Відео оброблено успішно")

    except Exception as e:
        current_app.logger.error(f"Помилка обробки відео: {str(e)}")
        raise

    finally:
        # Видалення оригінального файлу та тимчасових частин
        try:
            if os.path.exists(filepath):
                time.sleep(1)  # Невелика затримка перед видаленням
                os.remove(filepath)
        except OSError as e:
            logger.error(f"Помилка при видаленні файлу {filepath}: {e}")

        try:
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    os.remove(os.path.join(output_dir, file))
                os.rmdir(output_dir)
        except OSError as e:
            logger.error(f"Помилка при видаленні директорії {output_dir}: {e}")

        logger.info(f"Завершення обробки: надіслано частин - {sent_parts}, Відхилено - {len(failed_parts)}")
        for failed in failed_parts:
            logger.info(f"Відхилений файл: {failed['part']}, причина: {failed['reason']}")

