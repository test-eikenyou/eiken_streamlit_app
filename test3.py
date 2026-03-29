import streamlit as st
import random
import pandas as pd

# Excelファイルのパス
file_path = "単語一覧.xlsx"

# セッションステート初期化
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'count' not in st.session_state:
    st.session_state.count = 0
if 'finished' not in st.session_state:
    st.session_state.finished = False
if 'question' not in st.session_state:
    st.session_state.question = None
if 'answer' not in st.session_state:
    st.session_state.answer = None
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'selected_sheet' not in st.session_state:
    st.session_state.selected_sheet = None
if 'eiken_words' not in st.session_state:
    st.session_state.eiken_words = []

TOTAL_QUESTIONS = 10

st.title("英検準一級 単語テスト（4択）")

# Excelファイルからシート一覧取得
try:
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    sheet = st.selectbox("シートを選択してください", sheets)

    # シートが選ばれたらその単語を読み込む
    if st.session_state.selected_sheet != sheet:
        st.session_state.selected_sheet = sheet
        df = pd.read_excel(file_path, sheet_name=sheet)
        if '単語' not in df.columns or '意味' not in df.columns:
            st.error("選択したシートに「単語」または「意味」列が見つかりません。")
            st.stop()
        st.session_state.eiken_words = list(zip(df['単語'], df['意味']))
        st.session_state.question = None  # 新しいシートなので問題をリセット
        st.session_state.count = 0
        st.session_state.score = 0
        st.session_state.finished = False
except Exception as e:
    st.error(f"ファイル読み込みエラー: {e}")
    st.stop()

eiken_words = st.session_state.eiken_words

def generate_question():
    if not eiken_words:
        return None
    correct_word = random.choice(eiken_words)
    correct_meaning = correct_word[1]

    incorrect_meanings = [m for w, m in eiken_words if m != correct_meaning]
    # 選択肢が足りない場合の対策
    sample_size = min(len(set(incorrect_meanings)), 3)
    choices = random.sample(list(set(incorrect_meanings)), sample_size)
    choices.append(correct_meaning)
    random.shuffle(choices)

    return correct_word[0], correct_meaning, choices

def start_new_quiz():
    st.session_state.score = 0
    st.session_state.count = 0
    st.session_state.finished = False
    st.session_state.show_result = False
    st.session_state.answer = None
    st.session_state.question = generate_question()

# 最初の問題生成
if st.session_state.question is None and eiken_words:
    start_new_quiz()

# テスト終了画面
if st.session_state.finished:
    st.subheader("✅ テスト終了！")
    st.write(f"あなたのスコア: **{st.session_state.score} / {TOTAL_QUESTIONS}**")
    accuracy = st.session_state.score / TOTAL_QUESTIONS * 100
    st.write(f"正解率: **{accuracy:.1f}%**")

    if st.session_state.score == TOTAL_QUESTIONS:
        st.success("🌟 天才！全問正解です！おめでとう！")
    elif accuracy >= 80:
        st.success("🎉 合格です！よくできました！")
    else:
        st.error("残念、不合格です。もっとがんばりましょう！")

    if st.button("もう一度チャレンジする"):
        start_new_quiz()
        st.rerun()

    if st.button("終了する"):
        st.write("お疲れ様でした！またチャレンジしてね！")
        st.stop()

# テスト中
elif st.session_state.count < TOTAL_QUESTIONS and st.session_state.question:
    word, correct_meaning, choices = st.session_state.question
    st.write(f"### 問題 {st.session_state.count + 1} / {TOTAL_QUESTIONS}")
    st.write(f"次の単語の意味はどれ？ → <span style='font-size:36px; font-weight:bold;'>{word}</span>", unsafe_allow_html=True)

    # ラジオボタン
    st.session_state.answer = st.radio("意味を選んでください", choices, key=f"q_{st.session_state.count}")

    if st.session_state.show_result:
        if st.session_state.answer == correct_meaning:
            st.success("正解！🎉")
        else:
            st.error(f"不正解... 正しい意味は「{correct_meaning}」です。")

        st.write(f"現在のスコア: {st.session_state.score} / {TOTAL_QUESTIONS}")

        if st.button("次の問題へ"):
            st.session_state.count += 1
            st.session_state.show_result = False
            if st.session_state.count < TOTAL_QUESTIONS:
                st.session_state.question = generate_question()
            else:
                st.session_state.finished = True
            st.rerun()

    else:
        if st.button("回答を確認"):
            if st.session_state.answer == correct_meaning:
                st.session_state.score += 1
            st.session_state.show_result = True
            st.rerun()
