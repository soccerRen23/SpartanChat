from flask import Flask, render_template, request, redirect, url_for,flash,session
from models import User, Channel
import hashlib,os


app = Flask(__name__)

# sessionの暗号化キー .envから取得
app.secret_key = os.getenv('SECRET_KEY')


# ルート画面のリダイレクト処理
@app.route('/', methods=['GET'])
def index():
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
    registered_user = User.find_by_email(email)

    # 既存ユーザーの重複登録防止
    if registered_user != None:
        flash('既に登録されています')
        return redirect(url_for('signup_view'))
    else:
        # DBへ登録しログイン状態をセッションで保持
        User.create(name, email, password_hash)
        new_user = User.find_by_email(email)
        user_id = str(new_user['id'])
        session['user_id'] = user_id
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
    
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    registered_user = User.find_by_email(email)

    # 「ユーザー不存在」または「パスワードの誤り」を区別せず同一のメッセージを返す
    # これによりアカウントを推察する手掛かりを遮断する
    if registered_user is None or password_hash != registered_user["password_hash"]:
        flash('情報が正しくありません')
        return redirect(url_for('login_view'))
    else:
        # ログイン状態をセッションで保持
        session['user_id'] = registered_user["id"]
        return redirect(url_for('channels_view'))


# ログアウト
@app.route('/logout', methods=["GET"])  # 後でメソッドをPOST変更します
def logout():
    session.clear()
    return redirect(url_for('login_view'))


@app.route('/channels', methods=['GET'])
def channels_view():
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))
    else:
        channels = Channel.get_all()
        channels.reverse()
        return render_template('channels.html', channels=channels, uid=uid)


@app.route('/channels', methods=['POST'])
def create_channel():
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))

    channel_name = request.form.get('channelName')
    channel = Channel.find_by_name(channel_name)

    if channel == None:
        channel_description = request.form.get('channelDescription')
        Channel.create(uid, channel_name, channel_description)
    else:
        flash('既に同じ名前のチャンネルが存在しています')

    return redirect(url_for('channels_view'))

# HTMLのformは PUT,DELETEは扱えないので、JavaScriptやミドルウェアライブラリを使わずに実装すると一旦全部POSTで受けるようになる
@app.route('/channels/<cid>', methods=['POST'])
def channel_action(cid):
    pseudo_method = request.form.get('_method', '').upper()
    if pseudo_method == 'PUT':
        channel_name = request.form.get('channelName')
        channel_description = request.form.get('channelDescription')
        return update_channel(cid, channel_name, channel_description)
    elif pseudo_method == 'DELETE':
        return delete_channel(cid)
    else:
        return redirect(url_for('channels_view'))

def update_channel(cid, channel_name, channel_description):
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))

    channel = Channel.find_by_cid(cid)
    if channel is None:
        return redirect(url_for('login_view'))

    if channel['user_id'] != uid:
        flash('チャンネルは作成者のみ更新可能です')
    else:
        Channel.update(channel_name, channel_description, cid)

    return redirect(url_for('channels_view'))

def delete_channel(cid):
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))

    channel = Channel.find_by_cid(cid)
    if channel is None:
        return redirect(url_for('login_view'))

    if channel['user_id'] != uid:
        flash('チャンネルは作成者のみ削除可能です')
    else:
        Channel.delete(cid)

    return redirect(url_for('channels_view'))



@app.route('/login')
def login():
    return render_template('auth/login.html')
    # return redirect(url_for('login'))


@app.route('/signup', methods=['GET'])
def signup():
    return render_template('auth/signup.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
