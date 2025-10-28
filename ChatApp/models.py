from flask import abort
import pymysql
from util.DB import DB


# 初期起動時にコネクションプールを作成し接続を確立
db_pool = DB.init_db_pool()


# ユーザークラス
class User:
   @classmethod
   def create(cls, name, email, password_hash):
       conn = db_pool.get_conn()
       try:
           # withでカーソルを自動クローズしカーソルを安全に扱う
           with conn.cursor() as cur:
               sql = "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s);"
               cur.execute(sql, (name, email, password_hash,))
               conn.commit()
       except pymysql.Error as e:
           # 例外時に500エラーを返すことで異常を検知
           print(f'エラーが発生しています：{e}')
           abort(500)
       finally:
           # コネクションを返却
           db_pool.release(conn)


   @classmethod
   def find_by_email(cls, email):
       conn = db_pool.get_conn()
       try:
               with conn.cursor() as cur:
                   sql = "SELECT * FROM users WHERE email=%s;"
                   cur.execute(sql, (email,))
                   user = cur.fetchone()  # 1件だけ取得（emailはユニーク）
               return user
       except pymysql.Error as e:
           print(f'エラーが発生しています：{e}')
           abort(500)
       finally:
           db_pool.release(conn)
