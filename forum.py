from flask import request, abort
from utils import Response, Conn
from app import app

@app.route("/forum", methods=["GET"])
def forum():
  try:
    conn = Conn("forum")

    res = {
      "categories": { 0: { "blocks": [] } }
    }

    c_rows = conn.select("category")

    for row in c_rows:
      if row["hidden"]:
        continue
      del row["hidden"]
      row["blocks"] = []
      res["categories"][row["id"]] = row

    b_rows = conn.select("block")

    for row in b_rows:
      if row["hidden"]:
        continue
      del row["hidden"]
      block = row
      c_id = block["category"] or 0
      if res["categories"][c_id] is None:
        c_id = 0
      res["categories"][c_id]["blocks"].append(block)

    conn.close()

    return Response().data(res).get()
  except Exception as e:
    raise e

@app.route("/forum/posts", methods=["GET"])
def posts():
  if request.method == "POST":
    # TODO
    abort(405)
  else:
    block = request.args.get("block")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("size", 32))

    conn = Conn("forum")

    res = {}

    if not block:
      res["count"] = conn.select(
        "count",
        where = "`item` = 'post'"
      )[0]["count"]

    p_rows = conn.select(
      "post",
      order=("`latest_comment` DESC",),
      where="`block` = %(block)s" if block else None,
      limit=((page - 1) * page_size, page_size),
      params={ "block": block }
    )

    res["posts"] = []
    for row in p_rows:
      if row["hidden"]:
        keys = (
          "pid", "author", "block", "creation_time"
        )
        row = {
          key: row[key] for key in keys
        }
        row["hidden"] = True
      else:
        del row["hidden"]

      res["posts"].append(row)

    conn.close()

    return Response().data(res).get()

