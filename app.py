# -*- coding: utf-8 -*-
"""
单词虾记忆闯关游戏 - Streamlit Web版
部署: streamlit run app.py 或 Streamlit Cloud
"""

import streamlit as st
import random
import pandas as pd
import json
import os
from io import BytesIO

# ==================== 配置 ====================
WORD_FILE = '单词虾词库模版.xlsx'

# ==================== 词库解析 ====================
class WordParser:
    def __init__(self):
        self.all_words = []
    
    def load_excel(self, file_obj=None) -> bool:
        try:
            if file_obj:
                df = pd.read_excel(file_obj, engine='openpyxl')
            else:
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
            
            self.all_words = [{'w': data['w'], 'p': '/'.join(data['p']), 'm': '/'.join(data['m'])} 
                             for data in words_dict.values()]
            return True
            
        except Exception as e:
            return False
    
    def get_level_words(self, level: int) -> list:
        if level == 6:
            return self.all_words
        
        return [w for w in self.all_words if self._get_pos_count(w) == level]
    
    def _get_pos_count(self, word_data: dict) -> int:
        pos_list = word_data['p'].split('/')
        return len([p for p in pos_list if p.strip()])

# ==================== Session State 初始化 ====================
if 'parser' not in st.session_state:
    st.session_state.parser = WordParser()
    st.session_state.parser.load_excel()

if 'users' not in st.session_state:
    st.session_state.users = {}

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'game_started' not in st.session_state:
    st.session_state.game_started = False

if 'current_level' not in st.session_state:
    st.session_state.current_level = 1

if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

if 'level_words' not in st.session_state:
    st.session_state.level_words = []

if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# ==================== 页面 ====================
st.set_page_config(page_title="单词虾", page_icon="🪐")

st.title("🪐 单词虾记忆闯关")

# 侧边栏 - 用户信息
with st.sidebar:
    if st.session_state.current_user:
        user_data = st.session_state.users[st.session_state.current_user]
        st.header(f"👤 {user_data['username']}")
        st.metric("正确", user_data['correct'])
        st.metric("错误", user_data['wrong'])
        st.metric("当前关卡", user_data['level'])
        
        if st.button("退出登录"):
            st.session_state.current_user = None
            st.session_state.game_started = False
            st.rerun()
        
        st.divider()
        st.header("📚 词库管理")
        st.write(f"当前词库: {len(st.session_state.parser.all_words)} 个单词")
        
        # 上传Excel
        uploaded_file = st.file_uploader("导入Excel词库", type=['xlsx'])
        if uploaded_file:
            if st.session_state.parser.load_excel(uploaded_file):
                st.success(f"导入成功! {len(st.session_state.parser.all_words)} 个单词")
                st.rerun()
            else:
                st.error("导入失败")
        
        # 手动添加生词
        st.subheader("➕ 添加生词")
        with st.form("add_word_form"):
            new_word = st.text_input("单词")
            new_pos = st.text_input("词性")
            new_meaning = st.text_input("释义")
            submit = st.form_submit_button("添加")
            if submit and new_word and new_pos and new_meaning:
                st.session_state.parser.all_words.append({
                    'w': new_word, 'p': new_pos, 'm': new_meaning
                })
                st.success(f"已添加: {new_word}")
                st.rerun()
        
        # 导出词库
        if st.session_state.parser.all_words:
            df = pd.DataFrame(st.session_state.parser.all_words)
            df.columns = ['单词', '词性', '释义']
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button(
                "📥 导出词库",
                data=buffer.getvalue(),
                file_name="词库.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.header("👤 用户登录")

# 主界面
if not st.session_state.current_user:
    tab_login, tab_register = st.tabs(["登录", "注册"])
    
    with tab_login:
        with st.form("login_form"):
            login_phone = st.text_input("手机号")
            login_password = st.text_input("密码", type="password")
            login_submit = st.form_submit_button("登录")
            if login_submit:
                if login_phone in st.session_state.users:
                    if st.session_state.users[login_phone]['pw'] == login_password:
                        st.session_state.current_user = login_phone
                        st.rerun()
                    else:
                        st.error("密码错误")
                else:
                    st.error("用户不存在")
    
    with tab_register:
        with st.form("register_form"):
            reg_phone = st.text_input("手机号")
            reg_username = st.text_input("用户名")
            reg_password = st.text_input("密码", type="password")
            reg_submit = st.form_submit_button("注册")
            if reg_submit:
                if reg_phone in st.session_state.users:
                    st.error("手机号已注册")
                elif not reg_phone or not reg_username or not reg_password:
                    st.error("请填写完整信息")
                else:
                    st.session_state.users[reg_phone] = {
                        'pw': reg_password,
                        'username': reg_username,
                        'level': 1,
                        'correct': 0,
                        'wrong': 0,
                        'wrongWords': []
                    }
                    st.session_state.current_user = reg_phone
                    st.success("注册成功!")
                    st.rerun()

elif not st.session_state.game_started:
    st.header("🎮 选择关卡")
    
    user_data = st.session_state.users[st.session_state.current_user]
    current_lvl = user_data['level']
    
    level_names = {
        1: "关卡1: 单词性·释义单选",
        2: "关卡2: 双词性·释义单选", 
        3: "关卡3: 三词性·释义单选",
        4: "关卡4: 多词性·释义单选",
        5: "关卡5: 词性多选",
        6: "关卡6: 听音写词"
    }
    
    for level_num, name in level_names.items():
        unlocked = level_num <= current_lvl
        
        if unlocked:
            if st.button(name, use_container_width=True):
                words = st.session_state.parser.get_level_words(level_num)
                if words:
                    # 错题优先：错题出现2次
                    wrong_words = user_data.get('wrongWords', [])
                    if wrong_words:
                        wrong_list = [w for w in words if w['w'] in wrong_words] * 2
                        normal_list = [w for w in words if w['w'] not in wrong_words]
                        random.shuffle(wrong_list)
                        random.shuffle(normal_list)
                        level_words = wrong_list + normal_list
                    else:
                        random.shuffle(words)
                        level_words = words
                    
                    st.session_state.level_words = level_words
                    st.session_state.current_level = level_num
                    st.session_state.current_idx = 0
                    st.session_state.game_started = True
                    st.session_state.last_result = None
                    st.rerun()
        else:
            st.button(f"🔒 {name}", disabled=True, use_container_width=True)
    
    st.info("💡 提示: 答对所有题目即可解锁下一关")

else:
    # 游戏界面
    user_data = st.session_state.users[st.session_state.current_user]
    
    if st.session_state.current_idx >= len(st.session_state.level_words):
        st.success(f"🎉 通关!")
        
        if st.session_state.current_level < 6:
            new_level = st.session_state.current_level + 1
            if user_data['level'] < new_level:
                st.session_state.users[st.session_state.current_user]['level'] = new_level
        
        if st.button("返回关卡选择"):
            st.session_state.game_started = False
            st.rerun()
    else:
        # 显示结果
        if st.session_state.last_result:
            if st.session_state.last_result['correct']:
                st.success("✅ 正确!")
                # 播放音效需要前端JS，这里用st.audio如果需要可以添加
            else:
                st.error(f"❌ 错误! 正确答案: {st.session_state.last_result['correct_answer']}")
        
        # 当前题目
        word_data = st.session_state.level_words[st.session_state.current_idx]
        
        st.subheader(f"第 {st.session_state.current_idx + 1} / {len(st.session_state.level_words)} 题 | 关卡{st.session_state.current_level}")
        
        # 发音按钮
        if st.button("🔊 播放发音"):
            # Streamlit不能直接播放音频，用JavaScript
            st.markdown(f"""
                <script>
                var utt = new SpeechSynthesisUtterance("{word_data['w']}");
                utt.lang = 'en-US';
                utt.rate = 0.7;
                speechSynthesis.speak(utt);
                </script>
            """, unsafe_allow_html=True)
        
        st.markdown(f"## 📝 {word_data['w']}")
        
        # 选项
        if st.session_state.current_level < 5:
            # 选择题模式
            correct_meaning = word_data['m'].split('/')[0].strip()
            
            all_meanings = []
            for w in st.session_state.parser.all_words:
                meanings = w['m'].split('/')
                for m in meanings:
                    m = m.strip()
                    if m and m != correct_meaning and m not in all_meanings:
                        all_meanings.append(m)
            
            random.shuffle(all_meanings)
            wrong_opts = all_meanings[:3]
            options = [correct_meaning] + wrong_opts
            random.shuffle(options)
            
            st.markdown("**选择正确释义:**")
            
            for i, option in enumerate(options):
                if st.button(f"{i+1}. {option}", use_container_width=True):
                    if option == correct_meaning:
                        st.session_state.users[st.session_state.current_user]['correct'] += 1
                        # 答对移除错题
                        ww = st.session_state.users[st.session_state.current_user]['wrongWords']
                        if word_data['w'] in ww:
                            ww.remove(word_data['w'])
                        st.session_state.last_result = {'correct': True}
                        st.session_state.current_idx += 1  # 答对才进入下一题
                    else:
                        st.session_state.users[st.session_state.current_user]['wrong'] += 1
                        ww = st.session_state.users[st.session_state.current_user]['wrongWords']
                        if word_data['w'] not in ww:
                            ww.append(word_data['w'])
                        st.session_state.last_result = {
                            'correct': False,
                            'correct_answer': word_data['p'] + ' | ' + correct_meaning
                        }
                        # 错题不进入下一题，继续当前题
                    st.rerun()
        
        elif st.session_state.current_level == 5:
            # 词性多选
            correct_pos = word_data['p'].split('/')
            
            all_pos = []
            for w in st.session_state.parser.all_words:
                for p in w['p'].split('/'):
                    if p.strip() and p.strip() not in all_pos:
                        all_pos.append(p.strip())
            
            wrong_opts = [p for p in all_pos if p not in correct_pos]
            random.shuffle(wrong_opts)
            options = correct_pos + wrong_opts[:4-len(correct_pos)]
            random.shuffle(options)
            
            st.markdown("**选择所有正确词性(多选):**")
            
            if 'selected_options' not in st.session_state:
                st.session_state.selected_options = []
            
            # 显示选项
            cols = st.columns(2)
            for i, option in enumerate(options):
                with cols[i % 2]:
                    if st.checkbox(option, key=f"opt_{i}"):
                        if i not in st.session_state.selected_options:
                            st.session_state.selected_options.append(i)
                    else:
                        if i in st.session_state.selected_options:
                            st.session_state.selected_options.remove(i)
            
            if st.button("✅ 确认答案"):
                selected_pos = [options[i] for i in st.session_state.selected_options]
                correct_sorted = sorted(correct_pos)
                selected_sorted = sorted(selected_pos)
                
                if correct_sorted == selected_sorted:
                    st.session_state.users[st.session_state.current_user]['correct'] += 1
                    ww = st.session_state.users[st.session_state.current_user]['wrongWords']
                    if word_data['w'] in ww:
                        ww.remove(word_data['w'])
                    st.session_state.last_result = {'correct': True}
                    st.session_state.current_idx += 1  # 答对才进入下一题
                else:
                    st.session_state.users[st.session_state.current_user]['wrong'] += 1
                    ww = st.session_state.users[st.session_state.current_user]['wrongWords']
                    if word_data['w'] not in ww:
                        ww.append(word_data['w'])
                    st.session_state.last_result = {
                        'correct': False,
                        'correct_answer': ' / '.join(correct_pos)
                    }
                    # 错题不进入下一题，继续当前题
                    st.session_state.selected_options = []，继续当前题
                    st.session_state.selected_options = []  # 重置选项
                st.rerun()
        
        else:
            # 听音写词
            st.markdown("**请输入听到的单词:**")
            
            # 自动播放发音
            st.markdown(f"""
                <script>
                setTimeout(function() {{
                    var utt = new SpeechSynthesisUtterance("{word_data['w']}");
                    utt.lang = 'en-US';
                    utt.rate = 0.7;
                    speechSynthesis.speak(utt);
                }}, 500);
                </script>
            """, unsafe_allow_html=True)
            
            with st.form("answer6_form"):
                answer = st.text_input("输入单词", key="answer6_input")
                submit = st.form_submit_button("提交")
                if submit:
                    if answer.strip().lower() == word_data['w'].lower():
                        st.session_state.users[st.session_state.current_user]['correct'] += 1
                        ww = st.session_state.users[st.session_state.current_user]['wrongWords']
                        if word_data['w'] in ww:
                            ww.remove(word_data['w'])
                        st.session_state.last_result = {'correct': True}
                        st.session_state.current_idx += 1  # 答对才进入下一题
                    else:
                        st.session_state.users[st.session_state.current_user]['wrong'] += 1
                        ww = st.session_state.users[st.session_state.current_user]['wrongWords']
                        if word_data['w'] not in ww:
                            ww.append(word_data['w'])
                        st.session_state.last_result = {
                            'correct': False,
                            'correct_answer': word_data['w']
                        }
                        # 错题不进入下一题
                    st.rerun()
        
        # 退出按钮
        if st.button("退出游戏"):
            st.session_state.game_started = False
            st.rerun()
