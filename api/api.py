#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# 创建user表:
# uid
# username
# password
# info
#
#
# 创建keycount表
# uid
# keycount
# date
#
import MySQLdb
import datetime
from flask import Flask, request, render_template, url_for
from flask.ext.restful import Resource, Api
from gevent.wsgi import WSGIServer


app = Flask(__name__)
api = Api(app)
app.jinja_env.variable_start_string = '{{ '
app.jinja_env.variable_end_string = ' }}'

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "passwd": "root",
    "db": "keycount",
    "charset": "utf8"
}


def db_connection():
    global DB_CONFIG
    return MySQLdb.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        passwd=DB_CONFIG['passwd'],
        db=DB_CONFIG['db'],
        charset=DB_CONFIG['charset'])


# API首页
@app.route('/')
def index():
    return render_template('index.html')


# 按键数据API
class KeyCounter(Resource):
    def post(self):
        """
        添加或修改指定用户的按键数据
        """
        data = request.get_json(force=True)
        date = datetime.datetime.now().date()

        db = db_connection()
        cursor = db.cursor()
        cursor.execute(u'select * from user where username="%s" and password="%s"' % (data['username'], data['password']))
        this_user = cursor.fetchone()

        if not this_user:
            return {'result': 'error', "message": 'username or password is wrong'}

        cursor.execute(u'select * from keycount where uid=%d and date="%s"' % (int(this_user[0]), '%s-%s-%s' % (date.year, date.month, date.day)))
        this_keycount = cursor.fetchone()

        if this_keycount and this_keycount[1] == int(data['count']):
            return {'result': 'ok', "message": 'not changed'}

        if this_keycount:
            cursor.execute(u'update keycount set keycount=%d where uid=%d and date="%s"' % (int(data['count']), int(this_user[0]), '%s-%s-%s' % (date.year, date.month, date.day)))
        else:
            cursor.execute(u'insert into keycount (`uid`, `keycount`, `date`) values (%d, %d, "%s")' % (int(this_user[0]), int(data['count']), '%s-%s-%s' % (date.year, date.month, date.day)))
        db.commit()
        db.close()
        return {'result': 'ok', "message": ''}

    def get(self, username, date):
        """
        获取指定用户的按键数据
        """
        db = db_connection()
        cursor = db.cursor()
        if username != 'all':
            cursor.execute(u'select * from user where username="%s"' % username)
            this_user = cursor.fetchone()
            if not this_user:
                return {'result': 'error', "message": 'user not existed'}

            if date:
                condition = u'select * from keycount where uid=%d and date="%s"' % (this_user[0], date)
            else:
                condition = u'select * from keycount where uid=%d' % this_user[0]

            cursor.execute(condition)
            keycounts = cursor.fetchall()
            if date:
                counts = [k[1] for k in keycounts][0]
            else:
                counts = [k[1] for k in keycounts]

            result = {"username": username, 'date': date, 'counts': counts}
        else:
            if date == 'today':
                date = datetime.datetime.now().date()
                cursor.execute(u'select user.username,keycount.keycount,keycount.date from keycount left join user on user.uid = keycount.uid where keycount.date="%s-%s-%s" order by keycount.keycount desc' % (date.year, date.month, date.day))
            else:
                cursor.execute(u'select user.username,keycount.keycount,keycount.date from keycount left join user on user.uid = keycount.uid where keycount.date="%s" order by keycount.keycount desc' % date)

            users = cursor.fetchall()
            result = []
            order = 1
            for user in users:
                result.append({'order': order, 'username': user[0], 'keycount': user[1], 'date': '%s-%s-%s' % (user[2].year, user[2].month, user[2].day)})
                order += 1

        db.close()
        return {"result": "ok", "message": "", "data": result}


# 用户数据API
class User(Resource):
    def post(self):
        """
        注册或者创建用户
        """
        user = request.get_json(force=True)
        if not user['username'] or not user['password']:
            return {'result': 'error', 'message': 'username or password is empty'}

        db = db_connection()
        cursor = db.cursor()
        cursor.execute(u'select * from user')
        users = cursor.fetchall()
        for u in users:
            if u'%s' % user['username'] in u:
                return {'result': 'error', "message": 'repeated username'}
        cursor.execute(u'insert into user (username, password) values ("%s", "%s")' % (user['username'], user['password']))
        db.commit()
        db.close()
        return {'result': 'ok', "message": ''}

    def put(self):
        """
        修改用户密码
        """
        user = request.get_json(force=True)
        if not user['username'] or not user['oldpswd'] or not user['newpswd']:
            return {'result': 'error', 'message': 'username or password or new password is empty'}

        db = db_connection()
        cursor = db.cursor()

        # 判断是否存在该用户
        cursor.execute(u'select * from user where username="%s"' % user['username'])
        this_user = cursor.fetchone()
        if not this_user:
            return {'result': 'error', "message": 'user not existed'}

        # 判断该用户的密码是否正确
        this_user = cursor.execute(u'select * from user where username="%s" and password="%s"' % (user['username'], user['oldpswd']))
        this_user = cursor.fetchone()
        if not this_user:
            return {'result': 'error', "message": 'old password is incorrect'}
        if this_user[2] == u'%s' % user['newpswd']:
            return {'result': 'error', "message": 'password not changed'}

        cursor.execute(u'update user set password="%s" where username="%s"' % (user['newpswd'], user['username']))
        db.commit()
        db.close()
        return {'result': 'ok', "message": ""}


api.add_resource(User, '/user')
api.add_resource(KeyCounter, '/data', '/data/username/<username>/date/<date>')

if __name__ == '__main__':
    server = WSGIServer(("0.0.0.0", 5000), app)
    server.serve_forever()
