# -*- coding: utf-8 -*-
"""
单词虾记忆闯关游戏 - Web版
部署: python app.py 或 Render.com
"""

import os
import json
import pandas as pd
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 文件路径
WORD_FILE = '单词虾词库模版.xlsx'
USER_FILE = 'users.json'

# ==================== 用户数据管理 ====================
def load_users():
    """加载用户数据"""
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """保存用户数据"""
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ==================== 词库管理 ====================
def load_words():
    """从Excel加载词库"""
    try:
        df = pd.read_excel(WORD_FILE, engine='openpyxl')
        words_dict = {}
        
        for _, row in df.iterrows():
            word = str(row['单词']).strip() if pd.notna(row['单词']) else ''
            pos = str(row['词性']) if pd.notna(row['词性']) else ''
            meaning = str(row['释义']) if pd.notna(row['释义']) else ''
            
            if not word:
                continue
            if word not in words_dict:
                words_dict[word] = {'w': word, 'p': [], 'm': []}
            if pos and pos not in words_dict[word]['p']:
                words_dict[word]['p'].append(pos)
            if meaning and meaning not in words_dict[word]['m']:
                words_dict[word]['m'].append(meaning)
        
        word_list = [{'w': data['w'], 'p': '/'.join(data['p']), 'm': '/'.join(data['m'])} 
                     for data in words_dict.values()]
        return word_list
    except Exception as e:
        print(f"词库加载失败: {e}")
        return []

# ==================== API ====================
@app.route('/api/words')
def get_words():
    words = load_words()
    return jsonify(words)

# 管理员查看所有用户
@app.route('/api/admin/users')
def admin_users():
    users = load_users()
    # 返回脱敏后的用户数据（不包含密码）
    safe_users = {}
    for uid, data in users.items():
        safe_users[uid] = {
            'username': data.get('username', ''),
            'level': data.get('level', 1),
            'correct': data.get('correct', 0),
            'wrong': data.get('wrong', 0),
            'wrongWords': data.get('wrongWords', [])
        }
    return jsonify(safe_users)

@app.route('/api/users', methods=['GET', 'POST', 'PUT'])
def api_users():
    users = load_users()
    
    if request.method == 'GET':
        # 获取用户数据
        user_id = request.args.get('user_id')
        if user_id and user_id in users:
            return jsonify(users[user_id])
        return jsonify(users)
    
    elif request.method == 'POST':
        # 注册新用户
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': '缺少user_id'}), 400
        if user_id in users:
            return jsonify({'error': '用户已存在'}), 400
        
        users[user_id] = {
            'pw': data.get('password', ''),
            'username': data.get('username', ''),
            'level': 1,
            'correct': 0,
            'wrong': 0,
            'wrongWords': []
        }
        save_users(users)
        return jsonify({'success': True, 'user': users[user_id]})
    
    elif request.method == 'PUT':
        # 更新用户数据
        data = request.json
        user_id = data.get('user_id')
        if not user_id or user_id not in users:
            return jsonify({'error': '用户不存在'}), 400
        
        # 更新字段
        for key in ['level', 'correct', 'wrong', 'wrongWords']:
            if key in data:
                users[user_id][key] = data[key]
        
        save_users(users)
        return jsonify({'success': True})

# 首页
@app.route('/')
def index():
    return send_file('index.html')

# 词库文件
@app.route('/单词虾词库模版.xlsx')
def word_file():
    return send_file(WORD_FILE)

# 调试：检查用户文件
@app.route('/api/debug')
def debug():
    import os
    return jsonify({
        'user_file_exists': os.path.exists(USER_FILE),
        'user_file_path': USER_FILE,
        'cwd': os.getcwd(),
        'files': os.listdir('.')
    })

# 调试
@app.route('/api/debug')
def debug():
    import os
    return jsonify({
        'user_file_exists': os.path.exists(USER_FILE),
        'user_file_path': USER_FILE,
        'cwd': os.getcwd(),
        'files': os.listdir('.')
    })

if __name__ == '__main__':
    words = load_words()
    port = int(os.environ.get('PORT', 8000))
    print(f"\n{'='*40}")
    print(f"单词虾游戏")
    print(f"词库: {len(words)} 个单词")
    print(f"访问: http://localhost:{port}/")
    print(f"{'='*40}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
