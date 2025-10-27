from flask import abort
import pymysql
from util.DB import DB


# 初期起動時にコネクションプールを作成し接続を確立
db_pool = DB.init_db_pool()


# ユーザークラス
class User:
   @classmethod
   def create(cls, name, email, password_hash):
       # データベース接続プールからコネクションを一つ借りる
       conn = db_pool.get_conn()
       # エラーが起こるかもしれないがまずはtryでまずは実行してみる
       try:
            # コネクションからカーソル（操作用のオブジェクト）を取得する
           with conn.cursor() as cur:  # withはカーソルを自動で閉じる
               sql = "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s);"
               # SQLを実行し、パラメータ（name, email, password_hash）を埋め込む
               cur.execute(sql, (name, email, password_hash,))
               # データベースに変更を反映（保存）する
               conn.commit()
        # エラーが起きたらexceptで書いた処理を実行する
       except pymysql.Error as e:
           print(f'エラーが発生しています：{e}')
           abort(500)
        # エラーの有無にかかわらず、finally最後にこの処理を実行する
       finally:
           # 借りてたコネクションを返す
           db_pool.release(conn)


   @classmethod
   def find_by_email(cls, email):
       conn = db_pool.get_conn()
       try:
               with conn.cursor() as cur:
                   sql = "SELECT * FROM users WHERE email=%s;"
                   cur.execute(sql, (email,))
                   user = cur.fetchone()  # 1件だけ取得
               return user
       except pymysql.Error as e:
           print(f'エラーが発生しています：{e}')
           abort(500)
       finally:
           db_pool.release(conn)