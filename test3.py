import streamlit as st
import random
import pandas as pd

# -------------------------
# 設定・初期化
# -------------------------
# ウェブアプリ版のパス（リポジトリ内のファイル名）
file_path = "単語一覧.xlsx"
TOTAL_QUESTIONS = 10

def init_session():
    defaults = {
        "score": 0,
        "count": 0,
        "finished": False,
        "question": None,
        "answer": None,
        "show_result": False,
        "selected_sheet": None,
        "eiken_words": [],
        "remaining_words": [],
        "wrong_words": [],
        "mode": "normal", # "normal" or "review"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def generate_question():
    if st.session_state.mode == "normal" and st.session_state.count >= TOTAL_QUESTIONS:
        return None
    if not st.session_state.remaining_words:
        return None

    word, correct_meaning = st.session_state.remaining_words.pop()

    all_meanings = [m for w, m in st.session_state.eiken_words if m != correct_meaning]
    choices = random.sample(list(set(all_meanings)), min(3, len(set(all_meanings))))
    choices.append(correct_meaning)
    random.shuffle(choices)

    return word, correct_meaning, choices

def reset_quiz():
    st.session_state.show_result = False
    st.session_state.finished = False
    st.session_state.score = 0
    st.session_state.count = 0
    
    if st.session_state.mode == "normal":
        sample_size = min(len(st.session_state.eiken_words), TOTAL_QUESTIONS)
        st.session_state.remaining_words = random.sample(st.session_state.eiken_words, sample_size)
        st.session_state.wrong_words = []
    
    elif st.session_state.mode == "review":
        st.session_state.remaining_words = st.session_state.wrong_words.copy()
        st.session_state.wrong_words = []
        random.shuffle(st.session_state.remaining_words)

    st.session_state.question = generate_question()

# --- アプリメイン処理 ---
init_session()
st.title("🎮 英検準一級 単語テスト")

# Excel読み込み
try:
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    # 「全範囲」の選択肢を追加
    sheet = st.selectbox("出題範囲を選択してください", ["全範囲"] + sheets)

    if st.session_state.selected_sheet != sheet:
        st.session_state.selected_sheet = sheet
        words = []
        if sheet == "全範囲":
            for s in sheets:
                df = pd.read_excel(file_path, sheet_name=s)
                if '単語' in df.columns and '意味' in df.columns:
                    words.extend(list(zip(df['単語'], df['意味'])))
        else:
            df = pd.read_excel(file_path, sheet_name=sheet)
            words = list(zip(df['単語'], df['意味']))
        
        # 重複削除してセット
        st.session_state.eiken_words = list(set(words))
        st.session_state.mode = "normal"
        reset_quiz()
except Exception as e:
    st.error(f"Excelファイルの読み込みに失敗しました。ファイル名が「単語一覧.xlsx」であること、列名が「単語」と「意味」であることを確認してください。 エラー: {e}")
    st.stop()

# -------------------------
# 画面表示ロジック
# -------------------------

# 終了画面
if st.session_state.finished:
    if st.session_state.mode == "review" and not st.session_state.wrong_words:
        st.balloons()
        st.success("💯 このセットは完璧です！素晴らしい！")
        if st.button("次の10問へ（通常モード）"):
            st.session_state.mode = "normal"
            reset_quiz()
            st.rerun()
    else:
        st.subheader("✅ テスト終了")
        if st.session_state.wrong_words:
            st.warning(f"あと {len(st.session_state.wrong_words)} 問の復習が必要です。")
            if st.button("🔥 間違えた問題だけを復習する"):
                st.session_state.mode = "review"
                reset_quiz()
                st.rerun()
        else:
            st.success("🎉 全問正解！")
            if st.button("もう一度（新しい10問）"):
                st.session_state.mode = "normal"
                reset_quiz()
                st.rerun()

# 問題表示
elif st.session_state.question:
    word, correct_meaning, choices = st.session_state.question
    
    if st.session_state.mode == "normal":
        st.write(f"### 通常モード: {st.session_state.count + 1} / {TOTAL_QUESTIONS}")
    else:
        st.write(f"### 復習モード 🔁 残り: {len(st.session_state.remaining_words) + 1}問")

    # 単語を大きく表示
    st.markdown(f"次の単語の意味は？  \n<p style='font-size:40px; font-weight:bold; color:#1E88E5;'>{word}</p>", unsafe_allow_html=True)
    
    ans = st.radio("選択肢:", choices, key=f"radio_{st.session_state.count}_{len(st.session_state.remaining_words)}")

    if st.session_state.show_result:
        if ans == correct_meaning:
            st.success("正解！✨")
        else:
            st.error(f"不正解... 正解は「 {correct_meaning} 」")
            if (word, correct_meaning) not in st.session_state.wrong_words:
                st.session_state.wrong_words.append((word, correct_meaning))

        # Weblioボタン
        weblio_url = f"https://ejje.weblio.jp/content/{word}"
        st.link_button(f"📖 「{word}」の意味を詳しく確認する", weblio_url)

        if st.button("次へ"):
            if ans == correct_meaning:
                st.session_state.score += 1
            st.session_state.count += 1
            st.session_state.show_result = False
            next_q = generate_question()
            if next_q:
                st.session_state.question = next_q
            else:
                st.session_state.finished = True
            st.rerun()
    else:
        if st.button("回答を送信"):
            st.session_state.show_result = True
            st.rerun()
