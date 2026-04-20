from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'apec_secret_key_2026'
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "tickets": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    if 'user' not in session: 
        return redirect(url_for('auth'))
    return render_template('index.html', user=session['user'])

@app.route('/auth_firebase', methods=['POST'])
def auth_firebase():
    data_req = request.json
    email = data_req.get('email')
    role = data_req.get('role', 'student')
    
    if not email.endswith('@apec.edu.kz'):
        return jsonify({"status": "error", "message": "Домен не разрешен"}), 403

    data = load_data()
    user = next((u for u in data['users'] if u['email'] == email), None)
    
    if not user:
        user = {"email": email, "name": data_req.get('name'), "role": role}
        data['users'].append(user)
    else:
        # Если зашел админ с кодом, обновляем роль в базе
        if role == 'admin':
            user['role'] = 'admin'
    
    save_data(data)
    session['user'] = user
    return jsonify({"status": "success"})

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/submit', methods=['POST'])
def submit_ticket():
    if 'user' not in session: return jsonify({"status": "error"})
    data = load_data()
    new_ticket = {
        "id": len(data['tickets']) + 1,
        "student": session['user']['email'],
        "room": request.form.get('room'),
        "category": request.form.get('category'),
        "description": request.form.get('description'),
        "date": datetime.now().strftime("%d.%m %H:%M"),
        "status": "pending"
    }
    data['tickets'].append(new_ticket)
    save_data(data)
    return jsonify({"status": "success", "message": "Заявка отправлена!"})

@app.route('/admin')
def admin():
    if session.get('user', {}).get('role') != 'admin': return "Доступ запрещен", 403
    tickets = load_data()['tickets']
    return render_template('admin.html', tickets=tickets[::-1])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth'))

if __name__ == '__main__':
    app.run(debug=True)