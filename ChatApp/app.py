from flask import Flask, render_template,redirect, url_for

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login')
def login():
    return render_template('auth/login.html')
    # return redirect(url_for('login'))


@app.route('/signup', methods=['GET'])
def signup():
    return render_template('auth/signup.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
