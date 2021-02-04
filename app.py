from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
CORS(app, supports_credentials=True)

from forum import *
from user import *

@app.errorhandler(HTTPException)
def handle_httperror(error: HTTPException):
  return Response(False, error.description).get(), error.code

@app.errorhandler(Exception)
def handle_error(error: Exception):
  return Response(False, str(error)), 500

@app.route("/", methods=["GET"])
def index():
  return "Please refer to the documentation."

if (__name__ == "__main__"):
  app.run(host="0.0.0.0", port=8000, debug=True)
