from flask import Flask, render_template, redirect, request, url_for, make_response, session
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

# 思い出テーブル
class Memory(db.Model):
    __tablename__ = 'memories'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    ip_addr = db.Column(db.String())
    image = db.Column(db.LargeBinary)
    def to_dict(self):
        tags = db.session.query(Tag).filter(Tag.memory_id == self.id).all()
        tags = [tag.name for tag in tags]
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_addr': self.ip_addr,
            'tags': tags
        }

# タグテーブル
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key = True)
    memory_id = db.Column(db.Integer)
    name = db.Column(db.String())
    def to_dict(self):
        return {
            'id': self.id,
            'memory_id': self.memory_id,
            'name': self.name
        }

# 自身のユーザー取得
def get_own_user():
    user_id = session.get('user_id')
    return db.session.query(User).filter(User.id == user_id).first()

# IDからユーザー取得
def get_user_by_id(user_id):
    return db.session.query(User).filter(User.id == user_id).first()

# ユーザーネームからユーザー取得
def get_user_by_name(username):
    return db.session.query(User).filter(User.name == username).first()

# IDから思い出を取得
def get_memory(memory_id):
    return db.session.query(Memory).filter(Memory.id == memory_id).first()

# 思い出IDからタグを所得
def get_tags(memory_id):
    return db.session.query(Tag).filter(Tag.memory_id == memory_id).all()

# パスワードをハッシュ化して取得
def get_hash(password):
    text = password.encode('utf-8')
    return hashlib.sha512(text).hexdigest()

# IPアドレス取得
def get_ip_addr():
    return request.access_route[0]

# 自身の思い出であるかどうか
def is_own_memory(memory, user):
    if memory.user_id:
        if user: return memory.user_id == user.id
        else: return False
    else:
        return memory.ip_addr == get_ip_addr()

# トップページ
@app.route('/')
def index():
    user = get_own_user()
    message = session.pop('message', None)
    return render_template('index.html', user = user, message = message)

# ログインページ
@app.route('/signin')
def signin_page():
    user = get_own_user()
    if user: return redirect(url_for('index'))
    return render_template('signin.html')

# ログイン処理
@app.route('/signin/submit', methods = ['POST'])
def signin():
    user = get_own_user()
    if user: return redirect(url_for('index'))
    username = request.form['username']
    password = request.form['password']
    user = get_user_by_name(username)
    if user is None: return render_template('signin.html', error = True, username = username, password = password)
    if not password.isalnum(): return render_template('signin.html', error = True, username = username, password = password)
    hash = get_hash(password)
    if hash != user.hash: return render_template('signin.html', error = True, username = username, password = password)
    session['user_id'] = user.id
    return redirect(url_for('index'))

# 新規登録ページ
@app.route('/signup')
def signup_page():
    user = get_own_user()
    if user: return redirect(url_for('index'))
    return render_template('signup.html')

# 新規登録処理
@app.route('/signup/submit', methods = ['POST'])
def signup():
    user = get_own_user()
    if user: return redirect(url_for('index'))
    username = request.form['username']
    password = request.form['password']
    password_confirm = request.form['password_confirm']
    if username == '':
        message = "ユーザー名を入力してください"
        return render_template('signup.html', username_error_message = message)
    user = get_user_by_name(username)
    if user:
        message = "このユーザー名は既に使用されています"
        return render_template('signup.html', username_error_message = message, username = username)
    if not password.isalnum() or len(password) < 6:
        message = "パスワードは6文字以上の英数字で設定してください"
        return render_template('signup.html', password_error_message = message, username = username)
    if password != password_confirm:
        message = "パスワードが一致しません"
        return render_template('signup.html', password_confirm_error_message = message, username = username, password = password)
    user = User()
    user.name = username
    user.hash = get_hash(password)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    session['message'] = "ようこそ！さっそく思い出を投稿してみましょう！"
    return redirect(url_for('index'))

# ログアウト
@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('index'))

# 思い出の作成ページ
@app.route('/memory/create')
def create_memory_page():
    user = get_own_user()
    return render_template('create_memory.html', user = user)

# 思い出の作成処理
@app.route('/memory/submit', methods = ['POST'])
def create_memory():
    user = get_own_user()
    image = request.files['image']
    tags = request.form.getlist('tags')
    tags = [tag for tag in tags if tag.strip() != '' and len(tag.strip()) <= 10]
    if not image: return render_template('create_memory.html', user = user, error = True)
    memory = Memory()
    if user: memory.user_id = user.id
    memory.ip_addr = get_ip_addr()
    memory.image = image.read()
    db.session.add(memory)
    db.session.commit()
    for tag_name in tags:
        tag = Tag()
        tag.memory_id = memory.id
        tag.name = tag_name
        db.session.add(tag)
    db.session.commit()
    session['message'] = "思い出を投稿しました！"
    return redirect(url_for('index'))

# 思い出を削除するAPI
@app.route('/api/memory/delete', methods = ['POST'])
def delete_memory_api():
    memory_id = request.form['id']
    user = get_own_user()
    memory = get_memory(memory_id)
    if memory is None: return {'status': 'MEMORY_NOT_FOUND_ERROR'}
    if not is_own_memory(memory, user): return {'status': 'NOT_OWN_MEMORY_ERROR'}
    tags = get_tags(memory_id)
    for tag in tags:
        db.session.delete(tag)
    db.session.delete(memory)
    db.session.commit()
    session['message'] = "思い出を削除しました！"
    return {'status': 'SUCCESS'}

# 思い出を全て取得するAPI
@app.route('/api/memories')
def get_memories_api():
    memories = db.session.query(Memory).order_by(Memory.id.desc()).all()
    memories = [memory.to_dict() for memory in memories]
    return json.dumps(memories)

# IDから思い出を取得するAPI
@app.route('/api/memory')
def get_memory_api():
    memory_id = request.args.get('id')
    memory = get_memory(memory_id)
    if memory is None: return {}
    updatable = is_own_memory(memory, get_own_user())
    user = get_user_by_id(memory.user_id)
    memory = memory.to_dict()
    memory['user'] = user.to_dict() if user else {'name': get_ip_addr()}
    memory['updatable'] = updatable
    return json.dumps(memory)

# 思い出の画像を取得するAPI
@app.route('/api/memory/<memory_id>/image')
def get_memory_image_api(memory_id = None):
    memory = get_memory(memory_id)
    response = make_response()
    response.data = memory.image
    response.headers['Content-Disposition'] = f"attachment; filename={memory.id}.png"
    response.mimetype = 'image/*'
    return response

# マイユーザーを取得するAPI
@app.route('/api/user')
def get_own_user_api():
    user = get_own_user()
    user = user.to_dict() if user else {'ip_addr': get_ip_addr()}
    return json.dumps(user)

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 8080, debug = True)
