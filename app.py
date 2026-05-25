# app.py
import streamlit as st
import requests
from datetime import datetime, date

API_BASE = "https://taichung-movie-api.onrender.com/api"

st.set_page_config(page_title="台中電影場次查詢", page_icon="🎬", layout="wide")
st.title("🎬 台中電影場次整合查詢")

# --- 側邊欄篩選條件 ---
with st.sidebar:
    st.header("篩選條件")

    # 取得電影清單
    try:
        movies_res = requests.get(f"{API_BASE}/movies", timeout=10)
        movie_list = sorted(movies_res.json()) if movies_res.ok else []
    except Exception:
        movie_list = []

    # 取得影城清單
    try:
        theaters_res = requests.get(f"{API_BASE}/theaters", timeout=10)
        theater_data = theaters_res.json() if theaters_res.ok else []
        theater_names = ["全部"] + [t["name"] for t in theater_data]
    except Exception:
        theater_names = ["全部"]

    selected_movie = st.selectbox(
        "電影名稱",
        options=["全部"] + movie_list
    )

    selected_theater = st.selectbox(
        "影城",
        options=theater_names
    )

    selected_date = st.date_input(
        "日期",
        value=date.today(),
        min_value=date.today()
    )

    selected_format = st.selectbox(
        "播放格式",
        options=["全部", "數位", "3D", "IMAX", "4DX", "MX4D", "LUXE", "SCREENX"]
    )

    selected_language = st.selectbox(
        "語言",
        options=["全部", "原文", "國語", "英語", "日語", "韓語", "粵語"]
    )

    search_btn = st.button("🔍 查詢", use_container_width=True)

# --- 查詢 API ---
if search_btn or "results" not in st.session_state:
    params = {"limit": 500}
    if selected_movie != "全部":
        params["movie_name"] = selected_movie
    if selected_theater != "全部":
        params["theater_name"] = selected_theater

    try:
        res = requests.get(f"{API_BASE}/showtimes", params=params, timeout=15)
        all_results = res.json() if res.ok else []
    except Exception:
        all_results = []
        st.error("無法連線到 API，請稍後再試")

    # 在 Python 端過濾日期、格式、語言
    filtered = []
    for s in all_results:
        try:
            dt = datetime.fromisoformat(s["date_time"])
        except Exception:
            continue

        if dt.date() != selected_date:
            continue
        if selected_format != "全部" and selected_format.upper() not in s["format_type"].upper():
            continue
        if selected_language != "全部" and selected_language not in s["language"]:
            continue

        filtered.append({**s, "_dt": dt})

    filtered.sort(key=lambda x: x["_dt"])
    st.session_state["results"] = filtered

results = st.session_state.get("results", [])

# --- 顯示結果 ---
st.subheader(f"查詢結果：共 {len(results)} 筆場次")

if not results:
    st.info("目前沒有符合條件的場次")
else:
    # 依影城分組顯示
    theaters_in_results = sorted(set(r["theater_name"] for r in results))

    for theater in theaters_in_results:
        theater_results = [r for r in results if r["theater_name"] == theater]

        # 取得影城訂票網址
        url = next(
            (t["url"] for t in theater_data if t["name"] == theater),
            None
        ) if "theater_data" in dir() else None

        if url:
            st.markdown(f"### 🏟 [{theater}]({url})")
        else:
            st.markdown(f"### 🏟 {theater}")

        # 依電影分組
        movies_in_theater = sorted(set(r["movie_name"] for r in theater_results))
        for movie in movies_in_theater:
            movie_results = [r for r in theater_results if r["movie_name"] == movie]
            st.markdown(f"**🎞 {movie}**")

            cols = st.columns(6)
            for i, s in enumerate(movie_results):
                dt = s["_dt"]
                time_str = dt.strftime("%H:%M")
                fmt = s["format_type"]
                lang = s["language"]
                price = s["price"]
                seat = s["seat_status"]

                with cols[i % 6]:
                    st.markdown(
                        f"""
                        <div style='
                            border: 1px solid #444;
                            border-radius: 8px;
                            padding: 8px;
                            margin: 4px 0;
                            text-align: center;
                            background-color: #1e1e1e;
                        '>
                            <div style='font-size: 1.2em; font-weight: bold;'>{time_str}</div>
                            <div style='font-size: 0.8em; color: #aaa;'>{fmt} | {lang}</div>
                            <div style='font-size: 0.8em; color: #f0a500;'>💰 {price} 元</div>
                            <div style='font-size: 0.75em; color: #88cc88;'>{seat}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.divider()