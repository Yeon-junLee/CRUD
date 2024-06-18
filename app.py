from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys
import hashlib
import zlib

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.CRUD

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/signup')
def signup():
    uid = request.form['uid']
    pwd_input = request.form['pwd']
    pwd = hashlib.sha256(pwd_input.encode('utf-8')).hexdigest()
    # 해쉬 함수 sha256을 이용해 암호화
    result = db.users.insert_one({'uid':uid, 'pwd':pwd})

    if result:
        return jsonify({'result':'success'})
    else:
        return jsonify({'result':'failure'})
    
@app.route('/api/login')
def login():
    uid = request.form['uid']
    pwd_input = request.form['pwd']
    pwd = hashlib.sha256(pwd_input.encode('utf-8')).hexdigest()
    result = db.users.find_one({'uid':uid, 'pwd':pwd})

    if result:
        return jsonify({'result':'success'})
    else:
        return jsonify({'result':'failure', 'msg':'아이디 혹은 비밀번호가 틀렸습니다.'})
    
@app.route('/api/post')
def post():
    uid = request.form['uid']
    title = request.form['title']
    txt = request.form['txt']
    post_id = db.post.insert_one({'uid':uid, 'title':title, 'txt':txt}).inserted_id
    
    
if __name__ == '__main__':
    print(sys.executable)
    app.run('0.0.0.0', port=5000, debug=True)