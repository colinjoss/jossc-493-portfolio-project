from flask import Flask, redirect, request, render_template
from authlib.integrations.flask_client import OAuth
import requests
from constants import *
import truck
import package
import user


app = Flask(__name__)
oauth = OAuth(app)
app.register_blueprint(truck.bp)
app.register_blueprint(package.bp)
app.register_blueprint(user.bp)


auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)


@app.route('/')
def index():
    return "Please navigate to /login to create a JWT"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        content = request.form
        username = content['username']
        password = content['password']
        body = {'grant_type': 'password',
                'username': username,
                'password': password,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
                }
        headers = {'content-type': 'application/json'}
        url = 'https://' + DOMAIN + '/oauth/token'
        res = requests.post(url, json=body, headers=headers)
        id_token = res.json()['id_token']
        return redirect(f"{URL}/user-info?id_token={id_token}")
    else:
        return render_template('login.html')


@app.route('/user-info', methods=['GET'])
def user_info():
    jwt = request.args.get('id_token')
    return render_template('user-info.html', jwt=jwt)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
