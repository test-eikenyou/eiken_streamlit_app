import streamlit as st
import random
import pandas as pd

# -------------------------
# 設定・初期化
# -------------------------
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
        "mode": "normal",
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

# --- メイン処理 ---
init_session()
st.title("🎮 英検準一級 単語テスト")

try:
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    sheet = st.selectbox("出題範囲を選択", ["全範囲"] + sheets)

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
        
        st.session_state.eiken_words = list(set(words))
        st.session_state.mode = "normal"
        reset_quiz()
except Exception as e:
    st.error(f"読み込み失敗: {e}")
    st.stop()

# -------------------------
# 画面表示
# -------------------------

if st.session_state.finished:
    if st.session_state.mode == "review" and not st.session_state.wrong_words:
        st.balloons()
        st.success("💯 パーフェクト！")
        if st.button("次の10問へ"):
            st.session_state.mode = "normal"
            reset_quiz()
            st.rerun()
    else:
        st.subheader("✅ テスト終了")
        if st.session_state.wrong_words:
            st.warning(f"あと {len(st.session_state.wrong_words)} 問 復習が必要です。")
            if st.button("🔥 復習テスト開始"):
                st.session_state.mode = "review"
                reset_quiz()
                st.rerun()
        else:
            st.success("🎉 全問正解！")
            if st.button("新しい10問に挑戦"):
                st.session_state.mode = "normal"
                reset_quiz()
                st.rerun()

elif st.session_state.question:
    word, correct_meaning, choices = st.session_state.question
    
    # モード表示
    mode_label = "通常モード" if st.session_state.mode == "normal" else "復習モード 🔁"
    current_num = st.session_state.count + 1 if st.session_state.mode == "normal" else "再送"
    st.write(f"### {mode_label}")
    if st.session_state.mode == "normal":
        st.write(f"問題: {st.session_state.count + 1} / {TOTAL_QUESTIONS}")

    st.markdown(f"次の単語の意味は？  \n<p style='font-size:40px; font-weight:bold; color:#1E88E5;'>{word}</p>", unsafe_allow_html=True)
    
    # 【重要】回答済みの場合は disabled=True にして操作不能にする
    ans = st.radio(
        "選択肢:", 
        choices, 
        key=f"radio_{st.session_state.count}_{len(st.session_state.remaining_words)}",
        disabled=st.session_state.show_result 
    )

    if st.session_state.show_result:
        # 結果表示
        if ans == correct_meaning:
            st.success("正解！✨")
        else:
            st.error(f"不正解... 正解は「 {correct_meaning} 」")

        # 辞書ボタン
        st.link_button(f"📖 「{word}」を調べる", f"https://ejje.weblio.jp/content/{word}")

        if st.button("次へ"):
            st.session_state.count += 1
            st.session_state.show_result = False
            next_q = generate_question()
            if next_q:
                st.session_state.question = next_q
            else:
                st.session_state.finished = True
            st.rerun()
    else:
        if st.button("回答を確定する"):
            # ボタンを押した瞬間の選択肢で合否を判定
            if ans == correct_meaning:
                st.session_state.score += 1
            else:
                # 間違っていたら復習リストへ
                if (word, correct_meaning) not in st.session_state.wrong_words:
                    st.session_state.wrong_words.append((word, correct_meaning))
            
            st.session_state.show_result = True
            st.rerun()
