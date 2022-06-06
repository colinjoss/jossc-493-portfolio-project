from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, url_for, request
from constants import *
from google.cloud import datastore
from common_functions import new_user
from urllib.parse import quote_plus, urlencode
import truck
import package
import user


client = datastore.Client()


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(truck.bp)
app.register_blueprint(package.bp)
app.register_blueprint(user.bp)

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{DOMAIN}/.well-known/openid-configuration'
)


@app.route("/", methods=["GET", "POST"])
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        if request.form.get("login") is not None:
            return oauth.auth0.authorize_redirect(
                redirect_uri=url_for("user_info", _external=True)
            )
        elif request.form.get("logout") is not None:
            return redirect(
                "https://" + DOMAIN
                + "/v2/logout?"
                + urlencode(
                    {
                        "returnTo": url_for("index", _external=True),
                        "client_id": CLIENT_ID,
                    },
                    quote_via=quote_plus,
                )
            )
        else:
            return 'Nope'
    else:
        return render_template('login.html')


@app.route("/user-info", methods=["GET", "POST"])
def user_info():
    token = oauth.auth0.authorize_access_token()
    query = client.query(kind=USER)
    users = query.fetch()
    for usr in users:
        if str(usr['sub']) == str(token['userinfo']['sub']):
            return render_template('user-info.html', jwt=token['id_token'], user=token['userinfo']['nickname'])
    new_user(client, datastore, {
        'nickname': token['userinfo']['nickname'],
        'email': token['userinfo']['email'],
        'sub': token['userinfo']['sub']
    })
    return render_template('user-info.html',
                           jwt=token['id_token'],
                           authid=token['userinfo']['sub'],
                           user=token['userinfo']['nickname'])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
