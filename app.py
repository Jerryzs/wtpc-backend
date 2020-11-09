from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)

from forum import *
from user import *

@app.route("/", methods=["GET"])
def index():
  return "Please refer to the documentation."

if (__name__ == "__main__"):
  app.run(host="0.0.0.0", port=8000, debug=True)
