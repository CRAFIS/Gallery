from flask import Flask, render_template, redirect, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os, json, hashlib

app = Flask(__name__)

app.secret_key = '1234567890'

db_url = os.environ.get('DATABASE_URL') or 'postgresql://localhost/gallery'
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ユーザーテーブル
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(), nullable = False, unique = True)
    hash = db.Column(db.String(), nullable = False)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

# ストーリーテーブル
class Story(db.Model):
    __tablename__ = 'stories'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    path = db.Column(db.String())
    user_id = db.Column(db.Integer)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'user_id': self.user_id
        }

# シーンテーブル
class Scene(db.Model):
    __tablename__ = 'scenes'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String())
    path = db.Column(db.String())
    story_id = db.Column(db.Integer)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'story_id': self.story_id
        }

# マイユーザー取得
def get_self_user():
    user_id = session.get('user_id')
    return db.session.query(User).filter(User.id == user_id).first()

# ユーザーネームからユーザー取得
def get_user(username):
    return db.session.query(User).filter(User.name == username).first()

# IDからストーリー取得
def get_story(story_id):
    return db.session.query(Story).filter(Story.id == story_id).first()

# パスワードをハッシュ化して取得
def get_hash(password):
    text = password.encode('utf-8')
    return hashlib.sha512(text).hexdigest()

# トップページ
@app.route('/')
def index():
    user = get_self_user()
    message = session.pop('message', None)
    return render_template('index.html', user = user, message = message)

# ログインページ
@app.route('/signin')
def signin_page():
    user = get_self_user()
    if user: return redirect(url_for('index'))
    return render_template('signin.html')

# ログイン処理
@app.route('/signin/submit', methods = ['POST'])
def signin():
    user = get_self_user()
    if user: return redirect(url_for('index'))
    user = get_user(request.form['username'])
    if user is None: return render_template('signin.html', error = True)
    password = request.form['password']
    if not password.isalnum(): return render_template('signin.html', error = True)
    hash = get_hash(password)
    if hash != user.hash: return render_template('signin.html', error = True)
    session['user_id'] = user.id
    return redirect(url_for('index'))

# 新規登録ページ
@app.route('/signup')
def signup_page():
    user = get_self_user()
    if user: return redirect(url_for('index'))
    return render_template('signup.html')

# 新規登録処理
@app.route('/signup/submit', methods = ['POST'])
def signup():
    user = get_self_user()
    if user: return redirect(url_for('index'))
    username = request.form['username']
    if username == '':
        message = "ユーザー名を入力してください"
        return render_template('signup.html', username_error_message = message)
    user = get_user(username)
    if user:
        message = "このユーザー名は既に使用されています"
        return render_template('signup.html', username_error_message = message, username = username)
    password = request.form['password']
    if not password.isalnum() or len(password) < 8:
        message = "パスワードは8文字以上の英数字で設定してください"
        return render_template('signup.html', password_error_message = message, username = username)
    user = User()
    user.name = username
    user.hash = get_hash(password)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    session['message'] = "ようこそ！さっそくストーリーを投稿してみましょう！"
    return redirect(url_for('index'))

# ログアウト
@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('index'))

# ストーリー作成ページ
@app.route('/story/create')
def create_story_page():
    user = get_self_user()
    if user is None: return redirect(url_for('index'))
    return render_template('create_story.html', user = user)

# ストーリー作成処理
@app.route('/story/submit', methods = ['POST'])
def create_story():
    user = get_self_user()
    if user is None: return redirect(url_for('index'))
    story_name = request.form['story_name']
    story_image = request.files['story_image']
    if not (story_name and story_image):
        return render_template('create_story.html', user = user, error = True)
    story = Story()
    story.name = story_name
    story.user_id = user.id
    db.session.add(story)
    db.session.commit()
    story_path = f"images/stories/{story.id}.jpg"
    story_image.save(f"./static/{story_path}")
    story.path = story_path
    db.session.commit()
    session['message'] = "ストーリーを投稿しました！"
    return redirect(url_for('index'))

# ストーリー削除処理
@app.route('/story/<story_id>/delete')
def delete_story(story_id = None):
    user = get_self_user()
    if user is None: return redirect(url_for('index'))
    story = get_story(story_id)
    if story is None: return redirect(url_for('index'))
    if user.id != story.user_id: return redirect(url_for('index'))
    os.remove(f"./static/{story.path}")
    db.session.delete(story)
    db.session.commit()
    session['message'] = "ストーリーを削除しました！"
    return redirect(url_for('index'))

# ストーリー取得API
@app.route('/api/stories')
def get_stories_api():
    stories = db.session.query(Story).order_by(Story.id.desc()).limit(100).all()
    stories = [story.to_dict() for story in stories]
    return json.dumps(stories)

# マイユーザー取得API
@app.route('/api/user')
def get_self_user_api():
    user = get_self_user()
    user = user.to_dict() if user else {}
    return json.dumps(user)

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 8080, debug = True)
