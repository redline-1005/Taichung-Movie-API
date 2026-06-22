# app.py
import streamlit as st
import requests
from datetime import datetime, date, timezone, timedelta

API_BASE = "https://taichung-movie-api.onrender.com/api"
TMDB_API_KEY = "7b09fa8c16707593322979703b11ec48"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
TW_TZ = timezone(timedelta(hours=8))

st.set_page_config(page_title="台中電影場次查詢", page_icon="🎬", layout="wide")

# --- 取得基礎資料 ---
@st.cache_data(ttl=3600)
def fetch_movies():
    try:
        r = requests.get(f"{API_BASE}/movies", timeout=30)
        return sorted(r.json()) if r.ok else []
    except Exception:
        return []

@st.cache_data(ttl=3600)
def fetch_theaters():
    try:
        r = requests.get(f"{API_BASE}/theaters", timeout=30)
        return r.json() if r.ok else []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_all_showtimes():
    for attempt in range(3):  # 最多重試 3 次
        try:
            r = requests.get(f"{API_BASE}/showtimes", params={"limit": 500}, timeout=30)
            if r.ok and r.json():
                return r.json()
        except Exception:
            pass
    return []

@st.cache_data(ttl=86400)
def fetch_tmdb_info(movie_name):
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": movie_name, "language": "zh-TW"},
            timeout=10
        )
        results = r.json().get("results", [])
        if results:
            m = results[0]
            return {
                "poster": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
                "overview": m.get("overview", ""),
                "vote_average": m.get("vote_average", 0),
                "release_date": m.get("release_date", ""),
            }
    except Exception:
        pass
    return None

# --- 計算熱門電影（出現影城數 >= 2 或場次數 >= 5）---
def get_popular_movies(all_showtimes):
    from collections import defaultdict
    theater_count = defaultdict(set)
    show_count = defaultdict(int)
    for s in all_showtimes:
        name = s["movie_name"]
        theater_count[name].add(s["theater_name"])
        show_count[name] += 1
    popular = [
        name for name in show_count
        if len(theater_count[name]) >= 2 or show_count[name] >= 5
    ]
    return sorted(popular)

movie_list = fetch_movies()
theater_data = fetch_theaters()
theater_names = ["全部"] + [t["name"] for t in theater_data]
all_showtimes_data = fetch_all_showtimes()
popular_movies = get_popular_movies(all_showtimes_data)
st.write(f"DEBUG: popular_movies 數量 = {len(popular_movies)}")

# --- Gallery ---
st.title("🎬 台中電影場次整合查詢")

if popular_movies:
    st.subheader("🎞 熱映中")

    gallery_html = """
    <style>
    .gallery-container {
        display: flex;
        overflow-x: auto;
        gap: 16px;
        padding: 12px 4px;
        scrollbar-width: thin;
        scrollbar-color: #555 #222;
    }
    .gallery-container::-webkit-scrollbar { height: 6px; }
    .gallery-container::-webkit-scrollbar-track { background: #222; }
    .gallery-container::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
    .gallery-card {
        flex: 0 0 140px;
        cursor: pointer;
        border-radius: 10px;
        overflow: hidden;
        background: #1e1e1e;
        border: 1px solid #333;
        transition: transform 0.2s, border-color 0.2s;
        text-align: center;
    }
    .gallery-card:hover { transform: scale(1.05); border-color: #888; }
    .gallery-card img { width: 140px; height: 200px; object-fit: cover; }
    .gallery-card .title {
        font-size: 0.75em;
        padding: 6px 4px;
        color: #ddd;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    <div class="gallery-container">
    """

    for movie in popular_movies:
        info = fetch_tmdb_info(movie)
        if info and info["poster"]:
            img_tag = f"<img src='{info['poster']}' alt='{movie}'>"
        else:
            img_tag = f"<div style='width:140px;height:200px;background:#333;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:0.8em;'>無海報</div>"
        gallery_html += f"""
        <div class="gallery-card" onclick="window.parent.document.querySelector('[data-testid=stSelectbox] select').value='{movie}'">
            {img_tag}
            <div class="title">{movie}</div>
        </div>
        """

    gallery_html += "</div>"
    st.markdown(gallery_html, unsafe_allow_html=True)

    # 點選 gallery 後顯示電影詳情
    selected_gallery_movie = st.selectbox(
        "點選電影查看詳情",
        options=[""] + popular_movies,
        format_func=lambda x: "請選擇電影" if x == "" else x,
        key="gallery_select"
    )

    if selected_gallery_movie:
        info = fetch_tmdb_info(selected_gallery_movie)
        col1, col2 = st.columns([1, 3])
        with col1:
            if info and info["poster"]:
                st.image(info["poster"], width=180)
        with col2:
            st.markdown(f"### {selected_gallery_movie}")
            if info:
                if info["release_date"]:
                    st.caption(f"上映日期：{info['release_date']}　⭐ {info['vote_average']:.1f}")
                if info["overview"]:
                    st.write(info["overview"])
            # 顯示今日場次數
            all_showtimes = all_showtimes_data
            today_tw = datetime.now(TW_TZ).date()
            today_shows = [
                s for s in all_showtimes
                if s["movie_name"] == selected_gallery_movie
                and datetime.fromisoformat(s["date_time"]).date() == today_tw
            ]
            theaters_showing = sorted(set(s["theater_name"] for s in today_shows))
            if theaters_showing:
                st.write(f"**今日上映影城：** {' / '.join(theaters_showing)}")
            else:
                st.write("今日無場次")

st.divider()

# --- 側邊欄篩選條件 ---
with st.sidebar:
    st.header("篩選條件")

    selected_movie = st.selectbox("電影名稱", options=["全部"] + movie_list)
    selected_theater = st.selectbox("影城", options=theater_names)

    today_tw = datetime.now(TW_TZ).date()
    selected_date = st.date_input("日期", value=today_tw, min_value=today_tw)

    selected_format = st.selectbox(
        "播放格式",
        options=["全部", "數位", "3D", "IMAX", "4DX", "MX4D", "LUXE", "SCREENX"]
    )

    selected_language = st.selectbox(
        "語言",
        options=["全部", "原文", "國語", "英語", "日語", "韓語", "粵語"]
    )

    search_btn = st.button("🔍 查詢", use_container_width=True)

# --- 查詢場次 ---
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

    now_tw = datetime.now(TW_TZ).replace(tzinfo=None)

    filtered = []
    for s in all_results:
        try:
            dt = datetime.fromisoformat(s["date_time"])
        except Exception:
            continue
        if dt.date() != selected_date:
            continue
        if selected_date == today_tw and dt < now_tw:
            continue
        if selected_format != "全部" and selected_format.upper() not in s["format_type"].upper():
            continue
        if selected_language != "全部" and selected_language not in s["language"]:
            continue
        filtered.append({**s, "_dt": dt})

    filtered.sort(key=lambda x: x["_dt"])
    st.session_state["results"] = filtered

results = st.session_state.get("results", [])
st.subheader(f"查詢結果：共 {len(results)} 筆場次")

if not results:
    st.info("目前沒有符合條件的場次")
else:
    theaters_in_results = sorted(set(r["theater_name"] for r in results))

    for theater in theaters_in_results:
        theater_results = [r for r in results if r["theater_name"] == theater]
        url = next((t["url"] for t in theater_data if t["name"] == theater), None)

        if url:
            st.markdown(f"### 🏟 [{theater}]({url})")
        else:
            st.markdown(f"### 🏟 {theater}")

        if "新光影城" in theater:
            st.caption("⚠️ 新光影城網站會有不穩定之現象，若無法開啟請稍後再試")

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