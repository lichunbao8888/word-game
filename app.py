# -*- coding: utf-8 -*-
"""
单词虾记忆闯关游戏 - Web版
部署: python app.py 或 Render.com
"""

import os
import json
import pandas as pd
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# 词库文件
WORD_FILE = '单词虾词库模版.xlsx'

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

# API: 获取词库
@app.route('/api/words')
def get_words():
    words = load_words()
    return jsonify(words)

# 首页
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# 其他静态文件
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    words = load_words()
    port = int(os.environ.get('PORT', 8000))
    print(f"\n{'='*40}")
    print(f"单词虾游戏")
    print(f"词库: {len(words)} 个单词")
    print(f"访问: http://localhost:{port}/")
    print(f"{'='*40}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
