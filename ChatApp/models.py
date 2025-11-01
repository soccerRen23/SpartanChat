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


class Channel:
    @classmethod
    def create(cls, uid, channel_name, channel_description):
        conn = db_pool.get_conn()
        try:
            with conn.cursor() as cur:
                sql = "INSERT INTO channels (user_id, name, description) VALUES (%s, %s, %s);"
                cur.excute(sql, (uid, channel_name, channel_description,))
                conn.commit()
        except pymysql.Error as e:
            print(f'エラーが発生しています：{e}')
            abort(500)
        finally:
            db_pool.release(conn)


    @classmethod
    def get_all(cls):
        conn = db_pool.get_conn()
        try:
            with conn.cursor() as cur:
                sql = "SELECT * FROM channels;"
                cur.execute(sql)
                channels = cur.fetchall()
                return channels
        except pymysql.Error as e:
            print(f'エラーが発生しています：{e}')
            abort(500)
        finally:
            db_pool.release(conn)


    @classmethod
    def update(cls, new_channel_name, new_channel_description, cid):
        conn = db_pool.get_conn()
        try:
            with conn.cursor() as cur:
                sql = "UPDATE channels SET name=%s, description=%s WHERE id=%s;"
                cur.execute(sql, (new_channel_name, new_channel_description, cid,))
        except pymysql.Error as e:
            print(f'エラーが発生しています：{e}')
            abort(500)
        finally:
            db_pool.release(conn)


    @classmethod
    def delete(cls, cid):
        conn = db_pool.get=conn()
        try:
            with conn.cursor() as cur:
                sql = "DELETE FROM channels WHERE id=%s;"
        except pymysql.Error as e:
            print(f'エラーが発生しています：{e}')
            abort(500)
        finally:
            db_pool.release(conn)
