import os
from flask import abort, request
from utils import Response, Conn, randstr, verify_session
from google.oauth2 import id_token
from google.auth.transport import requests
from app import app

# types
from typing import Any, Dict, Mapping, Union

def verify_id_token(token: str):
  try:
    idinfo: Mapping[str, Any] = id_token.verify_oauth2_token(
      token,
      requests.Request(),
      os.getenv("GOOGLE_AUTH_CLIENT_ID")
    )

    if idinfo["hd"] != "winchesterthurston.org":
      raise ValueError("Wrong hosted domain.")

    return idinfo
  except ValueError as e:
    if app.debug:
      print(e)
    return False

def noauth():
  return Response().data({ "empty": True }).message("Not signed in.").get()

@app.route("/user", methods=["GET", "POST"])
def user():
  session = verify_session()

  # /user GET
  if request.method == "GET":
    uid: int = request.args.get("uid", 0)
    name: str = str(request.args.get("name", ""))
    code: int = request.args.get("code", 0)
    user_page: bool = bool(request.args.get("userpage", 0))

    if not uid and not name and not session:
      return noauth()

    try:
      uid = int(uid)
      code = int(code)
    except ValueError:
      return Response().fail().message("Invalid uid or code.").get()

    conn = Conn("auth")

    user_cols = (
      "uid", "name", "code", "email", "bio", "picture",
      "lv", "exp",
      "is_member", "is_moderator", "verify", "register_time", "join_time"
    )

    if user_page:
      user_cols += ("user_page",)

    if uid:
      condition = (str("`uid` = %s"), (uid,))
    elif name:
      condition = (str("`name` = %s AND `code` = %s"), (name, code))
    else:
      # session type cannot be None here
      condition = (str("`uid` = %s"), (session.uid,))

    user = conn.select(
      "user",
      cols=user_cols,
      where=f"{condition[0]} AND `gid` IS NOT NULL",
      params=condition[1]
    )

    if not user:
      conn.close()
      return Response().fail().message("User not found.").get()

    res = user[0]

    level = conn.select(
      "level",
      cols=("id", "name", "color", "text_color"),
      where="`id` = %s",
      params=(res["lv"],)
    )

    if level:
      res["lv"] = level[0]

    verid = res["verify"]
    if verid:
      verify = conn.select("verify", where="`id` = %s", params=(verid,))
      if verify:
        res["verify"] = verify[0]
      else:
        res["verify"] = None

    conn.close()
    return Response().data(res).session(session and session.sid).get()

  # /user POST
  if request.method == "POST":
    if not session:
      return noauth()

    allowed = set([
      "name", "bio", "picture", "user_page"
    ])

    updates: Dict[str, str] = {
      k: request.form.get(k, "", str)\
        for k in filter(lambda k: k in allowed, request.form.keys())
    }

    if updates:
      conn = Conn("auth")
      conn.update("user", "`uid` = %s" % session.uid, updates)
      conn.close()

    return Response().get()

@app.route("/user/check", methods=["GET"])
def check():
  name = request.args.get("name", "", str)
  code = request.args.get("code", 0, int)

  if not name:
    return Response().fail().message("Not enough arguments.").get()

  res = {
    "available": False
  }

  conn = Conn("auth")

  result = conn.select(
    "user",
    ("uid",),
    "`name` = %s AND `code` = %s",
    params=(name, code)
  )

  if not result:
    res["available"] = True

  conn.close()

  return Response().data(res).get()

@app.route("/auth", methods=["POST"])
def auth():
  if request.method != "POST":
    abort(405)

  res = {
    "newbie": False
  }

  ss = verify_session()
  if ss:
    return Response().data(res).session(ss.sid).get()

  token = str(request.form.get("token", ""))

  if not token:
    return Response().fail().message("Missing token or session id.").get()

  info = verify_id_token(token)
  if info:
    conn = Conn("auth")

    gid = str(info["sub"])

    user = conn.select(
      "user",
      ("uid",),
      "`gid` = %s" % gid
    )

    if not len(user):
      res["newbie"] = True

      userdata: Dict[str, Union[str, int]] = {
        "gid": gid,
        "name": str(info["given_name"]),
        "code": -1,
        "email": str(info["email"]),
        "picture": str(info["picture"])
      }

      while True:
        userdata["code"] = int(randstr(4, "0123456789"))
        if not userdata["code"] or userdata["code"] < 1000:
          continue
        result = conn.select(
          "user",
          ("uid",),
          "`name` = %s AND `code` = %s" % (userdata["name"], userdata["code"])
        )
        if not len(result):
          break

      user = conn.insert("user", userdata)
    else:
      user = user[0]["uid"]

    sid = randstr()
    conn.insert("session", {
      "sid": sid,
      "uid": user,
      "platform": request.user_agent.platform,
      "browser": request.user_agent.browser
    })

    conn.close()
    return Response().data(res).session(sid).get()

  else:
    return Response().fail().message("Token is invalid.").get()
