import os
import base64
from io import BytesIO
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileAllowed, FileRequired
from flask_bootstrap import Bootstrap
from flask_wtf import RecaptchaField

app = Flask(__name__)

# Настройки (для production замените через переменные окружения)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = os.environ.get('RECAPTCHA_PUBLIC_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get('RECAPTCHA_PRIVATE_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}

Bootstrap(app)

# ------------------- Форма -------------------
class NoiseForm(FlaskForm):
    image = FileField('Выберите изображение',
                      validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')])
    noise_level = FloatField('Уровень шума (0 – 1)',
                             validators=[DataRequired(), NumberRange(min=0, max=1)],
                             default=0.05)
    recaptcha = RecaptchaField()
    submit = SubmitField('Зашумлить')

# ------------------- Функция добавления равномерного шума -------------------
def add_noise(image_array, level):
    noise = np.random.uniform(-level, level, image_array.shape)
    noisy = image_array + noise
    return np.clip(noisy, 0, 1)

# ------------------- Гистограмма в base64 -------------------
def get_histogram_image(image_array):
    plt.figure(figsize=(8, 6))
    colors = ('r', 'g', 'b')
    for i, color in enumerate(colors):
        hist, bins = np.histogram(image_array[:, :, i], bins=256, range=(0, 1))
        plt.plot(bins[:-1], hist, color=color, alpha=0.7)
    plt.xlabel('Интенсивность')
    plt.ylabel('Количество пикселей')
    plt.title('Гистограмма распределения цветов')
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    hist_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return hist_b64

# ------------------- Главная страница -------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NoiseForm()
    if form.validate_on_submit():
        f = form.image.data
        noise_level = form.noise_level.data

        img = Image.open(f)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((400, 400))
        img_array = np.array(img).astype(np.float32) / 255.0

        noisy_array = add_noise(img_array, noise_level)
        noisy_img = Image.fromarray((noisy_array * 255).astype(np.uint8))

        orig_buf = BytesIO()
        img.save(orig_buf, format='PNG')
        orig_b64 = base64.b64encode(orig_buf.getvalue()).decode('utf-8')

        noisy_buf = BytesIO()
        noisy_img.save(noisy_buf, format='PNG')
        noisy_b64 = base64.b64encode(noisy_buf.getvalue()).decode('utf-8')

        orig_hist = get_histogram_image(img_array)
        noisy_hist = get_histogram_image(noisy_array)

        return render_template('result.html',
                               orig_image=orig_b64,
                               noisy_image=noisy_b64,
                               orig_hist=orig_hist,
                               noisy_hist=noisy_hist,
                               noise_level=noise_level)
    return render_template('index.html', form=form)

# ------------------- JSON API (опционально) -------------------
@app.route('/apinet', methods=['POST'])
def apinet():
    if request.mimetype == 'application/json':
        data = request.get_json()
        if 'image' not in data or 'noise_level' not in data:
            return jsonify({'error': 'Missing fields'}), 400
        try:
            img_b64 = data['image']
            noise_level = float(data['noise_level'])
            img_bytes = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_array = np.array(img).astype(np.float32) / 255.0
            noisy_array = add_noise(img_array, noise_level)
            noisy_img = Image.fromarray((noisy_array * 255).astype(np.uint8))
            buf = BytesIO()
            noisy_img.save(buf, format='PNG')
            noisy_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return jsonify({'noisy_image': noisy_b64})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Unsupported media type'}), 415

if __name__ == '__main__':
    app.run(debug=True)
