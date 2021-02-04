import os, re
import mysql.connector
from datetime import datetime, timedelta, timezone
from random import randrange
from flask import request, make_response

# types
from typing import Any, Dict, Iterable, List, NamedTuple, NoReturn, Optional, Sequence, Tuple, Union
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import CursorBase
from mysql.connector.pooling import PooledMySQLConnection

class RegexPatterns(NamedTuple):
  url = re.compile(
    r"^"
    r"(?:https?://)?"
    r"(?:"
      r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+?"
      r"(?:[a-z]{2,6}\.?){1,2}"
      r"|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r")"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)"
    r"$",
    re.IGNORECASE
  )

def randstr(length: int = 32, chars: Sequence = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"):
  num = len(chars)

  result = str()
  for _ in range(length):
    result += str(chars[randrange(num)])

  return result

def comma_separate_iter(iter: Iterable, wrapper: str = "'"):
  return ", ".join(map(lambda e: f"{wrapper}{e}{wrapper}", iter))

def now():
  return int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())

class Response:
  __response = dict()
  __sid = str()

  def __init__(
    self,
    success: bool = True,
    message: str = "",
    data: Dict = {}
  ):
    self.__response["success"] = success
    self.__response["message"] = message
    self.__response["data"] = data

  def success(self, success: bool = True):
    self.__response["success"] = success
    return self

  def fail(self):
    self.success(False)
    return self

  def data(self, data: Dict):
    self.__response["data"] = data
    return self

  def message(self, message: str):
    self.__response["message"] = message
    return self

  def session(self, sid: str):
    self.__sid = sid
    return self

  def get(self):
    res = make_response(self.__response)

    if self.__sid:
      res.set_cookie(
        "__sid",
        self.__sid,
        expires=(datetime.utcnow() + timedelta(days=7)),
        secure=True,
        httponly=True
      )

    return res

class Conn:
  def __init__(self, database: str):
    host = os.getenv("DB_HOSTNAME")
    user = os.getenv("DB_USERNAME")

    self.__conn: Union[MySQLConnection, PooledMySQLConnection] = mysql.connector.connect(
      host=host,
      user=user,
      password=os.getenv("DB_PASSWORD"),
      database=database,
      pool_name=f"{host[:host.index('.')]}_{user}_{database}",
      pool_size=3
    )

  def select(
    self,
    table: str,
    cols: Tuple[str, ...] = None,
    where: str = None,
    order: Tuple[str, ...] = None,
    limit: Union[int, Tuple[int, int]] = None,
    params: Union[Tuple[str, ...], Dict[str, Any]] = None
  ) -> List[Dict[str, Union[str, int, float]]]:
    cursor: CursorBase = self.__conn.cursor(dictionary=True)

    query = "SELECT {select} FROM `{table}` {where} {order} {limit}".format(
      select=comma_separate_iter(cols, "`")\
        if cols else "*",
      table=table,
      where=" WHERE %s" % (where)\
        if where else "",
      order=" ORDER BY %s" % (" ".join(order)) if order else "",
      limit=" LIMIT %s" % (limit)\
        if limit and type(limit) is int\
        else " LIMIT %s,%s" % (limit[0], limit[1])\
          if limit and type(limit) is tuple\
          else ""
    )

    cursor.execute(query, params=params, multi=False)

    rows = cursor.fetchall()

    cursor.close()

    return rows

  def insert(
    self,
    table: str,
    values: Dict[str, Union[str, int, float]],
    ignore: bool = True
  ) -> int:
    cursor: CursorBase = self.__conn.cursor()

    query = "INSERT {ignore}INTO `{table}` ({columns}) VALUES ({values})".format(
      ignore="IGNORE " if ignore else "",
      table=table,
      columns=comma_separate_iter(values.keys(), "`"),
      values=comma_separate_iter(values.values())
    )

    cursor.execute(query)
    self.__conn.commit()

    newid = cursor.lastrowid
    cursor.close()

    return newid

  def update(
    self,
    table: str,
    where: str,
    values: Dict[str, Union[str, int, float]],
    params: Union[Tuple[str, ...], Dict[str, Any]] = None
  ) -> NoReturn:
    cursor: CursorBase = self.__conn.cursor()

    query = "UPDATE `{table}` SET {values} WHERE {where}".format(
      table=table,
      values=comma_separate_iter([ f"`{k}`='{v}'" for k, v in values.items() ], ""),
      where=where
    )

    cursor.execute(query, params=params, multi=False)
    self.__conn.commit()

    cursor.close()

  def delete(
    self,
    table: str,
    where: str,
    params: Union[Tuple[str, ...], Dict[str, Any]] = None
  ) -> NoReturn:
    cursor: CursorBase = self.__conn.cursor()

    query = "DELETE FROM `{table}` WHERE {where}".format(
      table=table,
      where=where
    )

    cursor.execute(query, params=params, multi=False)
    self.__conn.commit()

    cursor.close()

  def close(self):
    return self.__conn.close()

class Session(NamedTuple):
  uid: int
  sid: str

def verify_session(token: Optional[str] = None, reuse_conn: Optional[Conn] = None) -> Optional[Session]:
  if not token:
    token = request.cookies.get("__sid", None)

  if token:
    if not reuse_conn:
      conn = Conn("auth")
    else:
      conn = reuse_conn

    sr = conn.select("session", ("uid", "last_request"), "`sid` = %s", params=(token,))

    if len(sr):
      sr = sr[0]

      if sr["last_request"] < now() - 604800:
        conn.delete("session", "`sid` = %s", (token,))
      else:
        conn.update("session", "`sid` = %s", { "last_request": now() }, (token,))

        if not reuse_conn:
          conn.close()

        return Session(int(sr["uid"]), token)

    if not reuse_conn:
      conn.close()

  return None
