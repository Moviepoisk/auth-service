from flask import Flask, request, render_template, redirect, url_for, flash, make_response
import requests
from app.forms.login import LoginForm
from app.forms.signup import SignupForm
from app.core.config import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

@app.route('/login', methods=['GET', 'POST'])
def login():
    API_URL = 'http://0.0.0.0:8000/api/v1/tokens'
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Подготовка данных для отправки на API
        data = {
            'grant_type': 'password',  # Предполагаем, что ваш API требует указания grant_type
            'username': username,
            'password': password,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            # Отправка запроса на API
            response = requests.post(API_URL, data=data, headers=headers)
            
            if response.status_code == 200:
                # Извлечение токенов из ответа API
                tokens = response.json()
                access_token = tokens.get('access_token')
                refresh_token = tokens.get('refresh_token')
                
                # Сохранение access_token и refresh_token в куки
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie('access_token', access_token)
                resp.set_cookie('refresh_token', refresh_token)
                
                return resp
            else:
                # Обработка ситуации с неправильными учетными данными или других ошибок
                flash('Invalid username or password')
        except requests.RequestException:
            flash('Network error. Please try again.')
    
    return render_template('login.html', form=form)

@app.route('/')
def index():
    if request.cookies.get('access_token'):
        return 'You are logged in'
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    
    # Удаляем куки с access_token и refresh_token
    resp.set_cookie('access_token', '', expires=0)
    resp.set_cookie('refresh_token', '', expires=0)
    
    API_URL = 'http://0.0.0.0:8000/api/v1/logout'
    try:
        access_token = request.cookies.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        requests.post(API_URL, headers=headers)
    except requests.RequestException:
        pass
    
    return resp


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        data = {
            "login": form.login.data,
            "first_name": form.first_name.data,
            "last_name": form.last_name.data,
            "email": form.email.data,
            "password": form.password.data
        }
        response = requests.post(
            'http://0.0.0.0:8000/api/v1/signup', 
            json=data,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return redirect(url_for('login'))
        else:
            flash('Signup failed. Please try again.')
    
    return render_template('signup.html', form=form)