from flask import Flask
import truck
import package
import user
from google.cloud import datastore


app = Flask(__name__)
app.register_blueprint(truck.bp)
app.register_blueprint(package.bp)
app.register_blueprint(user.bp)


@app.route('/')
def index():
    return "Please navigate to /users to use this API"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)