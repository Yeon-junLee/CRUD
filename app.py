from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request, session
from flask.json.provider import JSONProvider

import json
import sys
import hashlib
import zlib
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'secretkey'    # 세션을 위한 비밀 키
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)    # 세션 유지 30분

client = MongoClient('localhost', 27017)
db = client.CRUD

@app.route('/')
def home():
    if 'user' in session:       ### 세션에 유저 정보가 있다면 메인 페이지로 이동
        print("유저 아이디 : ", session['user'])
        return render_template('index.html', user=session['user'])
    return render_template('login.html')

@app.route('/toSignUp')
def toSignUp():
    return render_template('signup.html')

@app.route('/toMain')
def toMain():
    return render_template('index.html', user=session['user'])

@app.route('/toLogIn')
def toLogIn():
    return render_template('login.html')

@app.route('/api/signup', methods=['POST'])
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
    
@app.route('/api/login', methods=['POST'])
def login():
    uid = request.form['uid']
    pwd_input = request.form['pwd']
    pwd = hashlib.sha256(pwd_input.encode('utf-8')).hexdigest()
    user = db.users.find_one({'uid':uid})

    if user and user['pwd'] == pwd:
        session['user'] = uid
        ### 세션에 유저 정보 저장
        return jsonify({'result':'success'})
    return jsonify({'result':'failure', 'msg':'아이디 혹은 비밀번호가 틀렸습니다.'})

@app.route('/api/logout', methods=['GET'])
def logout():
    print("로그아웃 버튼 누름")
    session.pop('user', None)
    return jsonify({'result':'success'})
    
@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        posts = list(db.posts_collection.find())
        for post in posts:
            post['_id'] = str(post['_id'])
        return jsonify(posts)
    if request.method == 'POST':
        uid = request.form['uid']
        title = request.form['title']
        content = request.form['content']
        
        print("게시글 입력 받음!")
        print("유저 아이디 : ", uid)
        print("제목 : ", title)
        print("내용 : ", content)
        post_id = db.posts_collection.insert_one({'uid': uid, 'title': title, 'content': content}).inserted_id
        return jsonify({'result':'success'})

@app.route('/api/posts/<id>', methods=['PATCH'])
def update_post(id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    user_id = session['user']
    data = request.json
    
    try:
        post_id = ObjectId(id)
    except InvalidId:
        return jsonify({'error' : 'invalid post ID'}), 400
    
    post = db.posts_collection.find_one({'_id': post_id})
    print("수정될까?")
    if post and post['uid'] == user_id:
        db.posts_collection.update_one({'_id': post_id}, {'$set': {'title': data['title'], 'content': data['content']}})
        return jsonify({'message': 'Post updated successfully'})
    else:
        return jsonify({'error': 'You are not authorized to update this post'}), 403
    
@app.route('/api/posts/<id>', methods=['DELETE'])
def delete_post(id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401
    print("삭제 시도")
    user_id = session['user']
    post = db.posts_collection.find_one({'_id': ObjectId(id)})
    
    if post and post['uid'] == user_id:
        db.posts_collection.delete_one({'_id': ObjectId(id)})
        return jsonify({'message': 'Post deleted successfully'})
    else:
        return jsonify({'error': 'You are not authorized to delete this post'}), 403
    
@app.route('/api/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    content = data.get('content')
    user_id = session.get('user')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    comment = {'uid': user_id, 'content': content}
    result = db.posts_collection.update_one(
        {'_id': ObjectId(post_id)},
        {'$push': {'comments': comment}}
    )
    if result.modified_count == 1:
        return jsonify({'message': 'Comment added successfully'}), 200
    return jsonify({'error': 'Post not found'}), 404

@app.route('/api/posts/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    post = db.posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify(post.get('comments', [])), 200

    
if __name__ == '__main__':
    print(sys.executable)
    app.run('0.0.0.0', port=5000, debug=True)