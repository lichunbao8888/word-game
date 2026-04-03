# -*- coding: utf-8 -*-
"""
单词虾记忆闯关游戏 - Streamlit Web版
部署: streamlit run app.py 或 Streamlit Cloud
"""

import streamlit as st
import random
import pandas as pd

# ==================== 配置 ====================
# 词库文件 - 部署时放到 GitHub 一起上传
WORD_FILE = '单词虾词库模版.xlsx'

# ==================== 词库解析 ====================
class WordParser:
    def __init__(self):
        self.all_words = []
        self.level1_words = []
        self.level2_words = []
        self.level3_words = []
        self.level4plus_words = []
        self.multi_pos_words = []
    
    def load_excel(self) -> bool:
        try:
            df = pd.read_excel(WORD_FILE, engine='openpyxl')
            
            for _, row in df.iterrows():
                word = str(row['单词']).strip() if pd.notna(row['单词']) else ''
                pos_raw = str(row['词性']) if pd.notna(row['词性']) else ''
                meaning = str(row['释义']) if pd.notna(row['释义']) else ''
                
                if not word:
                    continue
                
                pos_list = self._parse_pos(pos_raw)
                pos_count = len(pos_list)
                
                word_data = {
                    'word': word,
                    'pos_list': pos_list,
                    'pos_raw': pos_raw,
                    'meaning': meaning,
                    'pos_count': pos_count
                }
                
                self.all_words.append(word_data)
                
                if pos_count == 1:
                    self.level1_words.append(word_data)
                elif pos_count == 2:
                    self.level2_words.append(word_data)
                elif pos_count == 3:
                    self.level3_words.append(word_data)
                else:
                    self.level4plus_words.append(word_data)
                
                if pos_count >= 2:
                    self.multi_pos_words.append(word_data)
            
            return True
            
        except Exception as e:
            st.error(f"词库加载失败: {e}")
            return False
    
    def _parse_pos(self, pos_raw: str) -> list:
        if not pos_raw or pos_raw == 'nan':
            return []
        
        pos_raw = pos_raw.replace('．', '.').replace('＆', '&')
        separators = ['&', '／', '/', '；', ';', ',', '，']
        pos_list = [pos_raw]
        
        for sep in separators:
            new_list = []
            for p in pos_list:
                new_list.extend(p.split(sep))
            pos_list = new_list
        
        pos_list = [p.strip() for p in pos_list if p.strip()]
        pos_list = list(dict.fromkeys(pos_list))
        return pos_list
    
    def get_level_words(self, level: int) -> list:
        if level == 1:
            return self.level1_words
        elif level == 2:
            return self.level2_words
        elif level == 3:
            return self.level3_words
        elif level == 4:
            return self.level4plus_words
        elif level == 5:
            return self.multi_pos_words
        return []

# ==================== Session State ====================
if 'parser' not in st.session_state:
    st.session_state.parser = WordParser()
    if not st.session_state.parser.load_excel():
        st.stop()

if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'current_level': 1,
        'current_question': 0,
        'total_correct': 0,
        'total_wrong': 0,
    }

if 'game_started' not in st.session_state:
    st.session_state.game_started = False

if 'current_words' not in st.session_state:
    st.session_state.current_words = []

if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

if 'last_result' not in st.session_state:
    st.session_state.last_result = None

if 'current_level' not in st.session_state:
    st.session_state.current_level = 1

# ==================== 页面 ====================
st.set_page_config(page_title="单词虾", page_icon="🪐")

st.title("🪐 单词虾记忆闯关")

# 侧边栏 - 统计
with st.sidebar:
    st.header("📊 你的进度")
    st.metric("正确", st.session_state.user_data['total_correct'])
    st.metric("错误", st.session_state.user_data['total_wrong'])
    if st.button("🔄 重置进度"):
        st.session_state.user_data = {
            'current_level': 1,
            'current_question': 0,
            'total_correct': 0,
            'total_wrong': 0,
        }
        st.session_state.game_started = False
        st.rerun()

# 主界面
if not st.session_state.game_started:
    st.header("🎮 选择关卡")
    
    level_names = {
        1: "Level 1: 单词性",
        2: "Level 2: 双词性", 
        3: "Level 3: 三词性",
        4: "Level 4: 多词性",
        5: "Level 5: 多选模式"
    }
    
    current_lvl = st.session_state.user_data['current_level']
    
    for level_num, name in level_names.items():
        unlocked = level_num <= current_lvl
        
        if unlocked:
            if st.button(name, use_container_width=True):
                words = st.session_state.parser.get_level_words(level_num)
                if words:
                    random.shuffle(words)
                    st.session_state.current_words = words
                    st.session_state.current_idx = 0
                    st.session_state.current_level = level_num
                    st.session_state.game_started = True
                    st.session_state.last_result = None
                    st.rerun()
        else:
            st.button(f"🔒 {name}", disabled=True, use_container_width=True)
    
    st.info("💡 提示: 答对所有题目即可解锁下一关")

else:
    # 游戏界面
    if st.session_state.current_idx >= len(st.session_state.current_words):
        st.success(f"🎉 Level {st.session_state.current_level} 通关!")
        
        if st.session_state.current_level < 5:
            st.session_state.user_data['current_level'] = max(
                st.session_state.user_data['current_level'],
                st.session_state.current_level + 1
            )
        
        if st.button("返回关卡选择"):
            st.session_state.game_started = False
            st.rerun()
    else:
        # 显示结果
        if st.session_state.last_result:
            if st.session_state.last_result['correct']:
                st.success("✅ 正确!")
            else:
                st.error(f"❌ 错误! 正确答案是: {st.session_state.last_result['correct_pos']}")
        
        # 当前题目
        word_data = st.session_state.current_words[st.session_state.current_idx]
        
        st.subheader(f"第 {st.session_state.current_idx + 1} / {len(st.session_state.current_words)} 题")
        st.markdown(f"## 📝 {word_data['word']}")
        
        # 选项
        if st.session_state.current_level < 5:
            # 选择题模式
            correct_meaning = word_data['meaning']
            all_meanings = [w['meaning'] for w in st.session_state.parser.all_words]
            all_meanings = [m for m in all_meanings if m != correct_meaning]
            
            wrong_options = random.sample(all_meanings, min(3, len(all_meanings)))
            options = [correct_meaning] + wrong_options
            random.shuffle(options)
            
            st.markdown("**选择词性:**")
            
            for i, option in enumerate(options):
                if st.button(f"{i+1}. {option}", use_container_width=True):
                    if option == correct_meaning:
                        st.session_state.user_data['total_correct'] += 1
                        st.session_state.last_result = {'correct': True}
                    else:
                        st.session_state.user_data['total_wrong'] += 1
                        st.session_state.last_result = {
                            'correct': False,
                            'correct_pos': ' / '.join(word_data['pos_list'])
                        }
                    
                    st.session_state.current_idx += 1
                    st.rerun()
        
        else:
            # 多选题模式
            correct_pos = word_data['pos_list']
            all_pos = []
            for w in st.session_state.parser.all_words:
                all_pos.extend(w['pos_list'])
            all_pos = list(set(all_pos))
            
            wrong_options = [p for p in all_pos if p not in correct_pos]
            wrong_options = random.sample(wrong_options, min(4, len(wrong_options)))
            
            options = correct_pos + wrong_options
            random.shuffle(options)
            
            st.markdown("**选择所有正确的词性(多选):**")
            
            if 'selected_options' not in st.session_state:
                st.session_state.selected_options = []
            
            # 显示选项
            for i, option in enumerate(options):
                checked = i in st.session_state.selected_options
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.checkbox("", value=checked, key=f"opt_{i}"):
                        if i not in st.session_state.selected_options:
                            st.session_state.selected_options.append(i)
                    else:
                        if i in st.session_state.selected_options:
                            st.session_state.selected_options.remove(i)
                with col2:
                    st.write(f"**{option}**")
            
            if st.button("✅ 确认答案"):
                correct_indices = [options.index(p) for p in correct_pos if p in options]
                
                if set(st.session_state.selected_options) == set(correct_indices):
                    st.session_state.user_data['total_correct'] += 1
                    st.session_state.last_result = {'correct': True}
                else:
                    st.session_state.user_data['total_wrong'] += 1
                    st.session_state.last_result = {
                        'correct': False,
                        'correct_pos': ' / '.join(correct_pos)
                    }
                
                st.session_state.selected_options = []
                st.session_state.current_idx += 1
                st.rerun()
        
        # 退出按钮
        if st.button("退出游戏"):
            st.session_state.game_started = False
            st.rerun()
