from flask import Flask, render_template, request, redirect, url_for,flash,session
from flask_socketio import SocketIO, emit # 非同期通信のために追加
from dotenv import load_dotenv
from models import User, Channel, Message
import hashlib,os, re
load_dotenv() # 追加しました.envファイルの内容を環境変数に反映

app = Flask(__name__)

# sessionの暗号化キー .envから取得
app.secret_key = os.getenv('SECRET_KEY')
# SockeyIOのセットアップのため追加
socketio = SocketIO(app)


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
    
    password_pattern = password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+-=;:,./?~])[a-zA-Z0-9!@#$%^&*()_+-=;:,./?~]{8,64}$'
    if re.match(password_pattern, password) is None:
        flash('パスワードは8文字から64文字以内で、英大文字・英小文字・数字・記号をそれぞれ1文字以上含めてください<br>'
              '使用できる記号は右のとおりです&emsp;! @ # $ % ^ & * ( ) _ + - = ; : , . / ? ~'
        ) 
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


@app.route('/messages', methods=['GET'])
def messages_view():
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))

    cid = request.args.get('cid')
    if cid is None:
        return redirect(url_for('channels_view'))
    
    channel = Channel.find_by_cid(cid)
    if channel is None:
        return redirect(url_for('channels_view'))
    
    messages = Message.get_all(cid)

    return render_template('messages.html', messages=messages, channel=channel, uid=uid)


@app.route('/messages', methods=['POST'])
def create_message():
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))
    
    cid = request.args.get('cid')
    if cid is None:
        return redirect(url_for('channels_view'))
    
    message = request.form.get('message')

    if message:
        Message.create(uid, cid, message)

    return redirect(url_for('messages_view', cid=cid))


# HTMLのformは PUT,DELETEは扱えないので、JavaScriptやミドルウェアライブラリを使わずに実装すると一旦全部POSTで受けるようになる
@app.route('/messages/<mid>', methods=['POST'])
def message_action(mid):
    cid = request.args.get('cid')
    if cid is None:
        return redirect(url_for('channels_view'))
    
    pseudo_method = request.form.get('_method', '').upper()
    if pseudo_method == 'PUT':
        new_message = request.form.get('message')
        return update_message(cid, mid, new_message)
    elif pseudo_method == 'DELETE':
        return delete_message(cid, mid)
    else:
        return redirect(url_for('messages_view', cid=cid))


def update_message(cid, mid, new_message):
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))

    message = Message.find_by_mid(mid)
    if message is None:
        return redirect(url_for('messages_view', cid=cid))

    if message['user_id'] != uid:
        flash('メッセージは投稿者のみ更新可能です')
    else:
        Message.update(new_message, mid)

    return redirect(url_for('messages_view', cid=cid))


def delete_message(cid, mid):
    uid = session.get('user_id')
    if uid is None:
        return redirect(url_for('login_view'))

    message = Message.find_by_mid(mid)
    if message is None:
        return redirect(url_for('messages_view', cid=cid))

    if message['user_id'] != uid:
        flash('メッセージは投稿者のみ削除可能です')
    else:
        Message.delete(mid)

    return redirect(url_for('messages_view', cid=cid))

# SocketIOの実行部分を追加
# メッセージの読み込み
@socketio.on('load messages')
def load_messages(data=None):
    if not data:
        return
    cid = data.get('cid')
    if not cid:
        return
    messages = Message.get_all(cid)
    messages_list = [msg['message'] for msg in messages]
    emit('messages loaded', messages_list)

# メッセージの登録
@socketio.on('send message')
def send_message(data):
    uid = data.get('user_id')
    cid = data.get('cid')
    message = data.get('message')
    if uid and cid and message:
        Message.create(uid, cid, message)
        emit('new message', message, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
