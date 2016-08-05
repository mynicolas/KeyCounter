#!/usr/bin/env python
#-*- coding: utf-8 -*-
import MySQLdb
import datetime
from flask import Flask, request
from flask.ext.restful import reqparse, Resource, Api
from gevent.wsgi import WSGIServer


app = Flask(__name__)
api = Api(app)


class Index(Resource):
    def get(self):
        return {"version": "v1"}


class KeyCounter(Resource):
    def post(self):
        data = request.get_json(force=True)
        date = datetime.datetime.now().date()

        db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="root",
            db="ws",
            charset="utf8")
        cursor = db.cursor()
        cursor.execute(u'select * from user where username="%s" and password="%s"' % (data['username'], data['password']))
        this_user = cursor.fetchone()
        if not this_user:
            return {'result': 'error', "message": 'username or password is wrong'}

        cursor.execute(u'select * from keycount where uid=%d and date="%s"' % (int(this_user[0]), '%s-%s-%s' % (date.year, date.month, date.day)))
        this_keycount = cursor.fetchone()

        if this_keycount[1] == int(data['count']):
            return {'result': 'ok', "message": 'not changed'}

        if this_keycount:
            cursor.execute(u'update keycount set keycount=%d where uid=%d and date="%s"' % (data['count'], int(this_user[0]), '%s-%s-%s' % (date.year, date.month, date.day)))
        else:
            cursor.execute(u'insert into keycount values (%d, %d, "%s")' % (int(this_user[0]), data['count'], '%s-%s-%s' % (date.year, date.month, date.day)))
        db.commit()
        return {'result': 'ok', "message": ''}

    def get(self, username, date):
        db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="root",
            db="ws",
            charset="utf8")
        cursor = db.cursor()
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
        counts = [k[1] for k in keycounts]

        return {"result": "ok", "message": "", "data": {"username": username, 'date': date, 'counts': counts}}




class User(Resource):
    def post(self):
        user = request.get_json(force=True)
        if not user['username'] or not user['password']:
            return {'result': 'error', 'message': 'username or password is empty'}

        db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="root",
            db="ws",
            charset="utf8")
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
        user = request.get_json(force=True)
        if not user['username'] or not user['password']:
            return {'result': 'error', 'message': 'username or password is empty'}

        db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="root",
            db="ws",
            charset="utf8")
        cursor = db.cursor()
        cursor.execute(u'select * from user where username="%s"' % user['username'])
        this_user = cursor.fetchone()
        if not this_user:
            return {'result': 'error', "message": 'user not existed'}
        if this_user[2] == u'%s' % user['password']:
            return {'result': 'error', "message": 'password not changed'}

        cursor.execute(u'update user set password="%s" where username="%s"' % (user['password'], user['username']))
        db.commit()
        db.close()
        return {'result': 'ok', "message": ""}


api.add_resource(Index, '/')
api.add_resource(User, '/user')
api.add_resource(KeyCounter, '/data', '/data/username/<username>/date/<date>')
# api.add_resource(KeyCounter)
if __name__ == '__main__':
    server = WSGIServer(("0.0.0.0", 5000), app)
    server.serve_forever()