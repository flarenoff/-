# в начало
import os
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, send_from_directory


app = Flask(__name__)
app.secret_key = 'your_secret_key'

def generate_id():
    try:
        with open('video_counter.txt', 'r') as f:
            current_id = int(f.read())
    except FileNotFoundError:
        current_id = 0
    video_id = hex(current_id)[2:].upper()
    with open('video_counter.txt', 'w') as f:
        f.write(str(current_id + 1))
    return video_id

def register_user(username, password):
    with open('users.txt', 'a') as f:
        f.write(f'{username}:{password}\n')

def check_user(username, password):
    with open('users.txt', 'r') as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) >= 2 and parts[0] == username and parts[1] == password:
                return True
    return False

def upload_video(video_id, title, video_file, thumbnail_file, username):
    video_path = f'studio/{video_id}.mp4'
    thumbnail_path = f'studio/{video_id}.jpg'  
    video_file.save(video_path)
    thumbnail_file.save(thumbnail_path)
    with open('videos.txt', 'a') as f:
        f.write(f'{video_id}:{title}:{username}:0:0:\n')  # Сохраняем ID, заголовок, пользователя, лайки, дизлайки и пользователей, которые лайкнули.

def get_videos():
    videos = []
    with open('videos.txt', 'r') as f:
        for line in f:
            video_id, title, username, likes, dislikes, liked_users = line.strip().split(':')
            views = 0
            videos.append({
                'id': video_id,
                'title': title,
                'username': username,
                'likes': int(likes),
                'dislikes': int(dislikes),
                'liked_users': liked_users.split(',') if liked_users else [],
                'fun_factor': int(likes) - int(dislikes),
                'views': int(views)
            })
    return sorted(videos, key=lambda x: x['fun_factor'], reverse=True)

@app.route('/')
def index():
    videos = get_videos()
    return render_template('index.html', videos=videos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        register_user(username, password)
        flash("Registration successful!")
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_user(username, password):
            session['username'] = username  # Храним имя пользователя в сессии
            flash("Login successful!", 'success')  # Сообщение об успешном входе
            return redirect(url_for('index'))
        else:
            flash("Неверный пароль или имя пользователя.", 'error')  # Сообщение о неверных данных
            return redirect(url_for('login'))  # Перенаправляем обратно на страницу входа
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)  # Удаляем пользователя из сессии
    return redirect(url_for('index'))  # Перенаправляем на главную страницу


@app.route('/studio', methods=['GET', 'POST'])
def studio():
    if request.method == 'POST':
        title = request.form['title']
        video_file = request.files['video_file']
        thumbnail_file = request.files['thumbnail_file']
        video_id = generate_id()
        username = session.get('username') # Получаем имя пользователя из сессии
        if username: # Проверяем, что пользователь залогинен
            upload_video(video_id, title, video_file, thumbnail_file, username)
            flash("Video uploaded successfully!")
            return redirect(url_for('index'))
        else:
            flash("You need to be logged in to upload videos.")
            return redirect(url_for('login'))
    return render_template('studio.html')

@app.route('/video', methods=['GET'])
def video():
    videos = get_videos()  # Получаем все видео
    video_id = request.args.get('id')  # ID текущего видео

    if not video_id:
        return 'Video ID not provided', 400

    for i, video in enumerate(videos):
        if video['id'] == video_id:
            videos[i]['views'] += 1
            update_videos(videos)
            return render_template('video.html', video=video, videos=videos, video_id=video_id)

    return 'Video not found', 404



@app.route('/like/<video_id>', methods=['POST'])
def like(video_id):
    username = session.get('username')
    if not username:
        flash("You need to be logged in to like videos.")
        return redirect(url_for('login'))

    videos = get_videos()
    for i, video in enumerate(videos):
        if video['id'] == video_id:
            liked_users = video['liked_users']
            if username not in liked_users:
                videos[i]['likes'] += 1
                videos[i]['views'] -= 1
                liked_users.append(username)
                videos[i]['liked_users'] = liked_users
            break

    update_videos(videos)
    return redirect(url_for('video', video_id=video_id))

@app.route('/dislike/<video_id>', methods=['POST'])
def dislike(video_id):
    username = session.get('username')
    if not username:
        flash("You need to be logged in to dislike videos.")
        return redirect(url_for('login'))

    videos = get_videos()
    for i, video in enumerate(videos):
        if video['id'] == video_id:
            videos[i]['dislikes'] += 1
            videos[i]['views'] -= 1
            break

    update_videos(videos)
    return redirect(url_for('video', video_id=video_id))

def update_videos(videos):
    with open('videos.txt', 'w') as f:
        for video in videos:
            f.write(f"{video['id']}:{video['title']}:{video['username']}:{video['likes']}:{video['dislikes']}:" + ','.join(video['liked_users']) + '\n')

@app.route('/uploads/<path:filename>')
def upload_video_file(filename):
    return send_from_directory('studio', filename)

@app.route('/media/<filename>')
def media(filename):
    return send_from_directory('media', filename)


if __name__ == '__main__':
    if not os.path.exists('studio'):
        os.makedirs('studio')
    app.run(host='0.0.0.0', port=5000, debug=True)
