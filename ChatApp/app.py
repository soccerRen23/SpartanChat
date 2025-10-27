from flask import Flask, render_template, request, redirect, url_for,flash,session
from models import User
import hashlib,os

app = Flask(__name__)

# sessionの暗号化キー .envから取得
app.secret_key = os.getenv('SECRET_KEY')


# ルート画面のリダイレクト処理
@app.route('/', methods=['GET'])
def  index():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login_view'))
    else:
        return redirect(url_for('channels_view'))


# サインアップ画面の表示
@app.route('/signup', methods=['GET'])
def signup_view():
    return render_template('auth/signup.html')

# サインアップ処理
@app.route('/signup', methods=['POST'])
def signup_process():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    passwordConfirmation = request.form.get('password-confirmation')

    if name == '' or email == '' or password == '':
        flash('名前、メールアドレス、パスワードの全てを入力してください')
        return redirect(url_for('signup_view'))
    
    if password != passwordConfirmation:
        flash('二つのパスワードが一致しません')
        return redirect(url_for('signup_view'))

    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    # 入力されたemailを引数として関数に渡しDBからユーザー情報取得。情報なければNoneを返す
    registered_user = User.find_by_email(email)

    if registered_user != None:
        flash('既に登録されています')
        return redirect(url_for('signup_view'))
    else:
        User.create(name, email, password_hash)  # DBに登録
        new_user = User.find_by_email(email)  # DBからユーザー情報を取得
        user_id = str(new_user['id'])  # ユーザーのidを取得（辞書型なのでこの書き方、strは不要かも）
        session['user_id'] = user_id  # sessionにidを追加
        return redirect(url_for('channels_view'))


# ログインページの表示
@app.route('/login', methods=['GET'])
def login_view():
    return render_template('auth/login.html')


# ログイン処理
@app.route('/login', methods=['POST'])
def login_process():
    email = request.form.get('email')
    password = request.form.get('password')

    if email == "" or  password == "":
        flash('メールアドレスとパスワードを入力してください')
        return redirect(url_for('login_view'))
    
    registered_user = User.find_by_email(email)
    if registered_user is None:
        flash('このユーザーは存在しません')
        return redirect(url_for('login_view'))
    
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if password_hash != registered_user["password_hash"]:
        flash('パスワードが違います')
        return redirect(url_for('login_view'))
    else:
        session['user_id'] = registered_user["id"]  # sessionにDB上のユーザーidを入れておこう
        return redirect(url_for('channels_view'))


# ログアウト
@app.route('/logout', methods=["GET"])  # 後でメソッドをPOST変更します
def logout():
    session.clear()
    return redirect(url_for('login_view'))


# （仮置き）チャンネル一覧ページ chennnels.htmlが表示されるようにしただけ
@app.route('/channels', methods=['GET'])
def channels_view():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login_view'))
    else:
        channels = []
        uid = user_id
        return render_template('channels.html', channels=channels, uid=uid)


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)