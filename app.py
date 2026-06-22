# app.py
import streamlit as st
import requests
from datetime import datetime, date, timezone, timedelta

API_BASE = "https://taichung-movie-api.onrender.com/api"
TMDB_API_KEY = "7b09fa8c16707593322979703b11ec48"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
TW_TZ = timezone(timedelta(hours=8))

st.set_page_config(page_title="台中電影場次查詢", page_icon="🎬", layout="wide")

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
    for attempt in range(3):
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

st.title("🎬 台中電影場次整合查詢")

if popular_movies:
    st.subheader("🎞 熱映中")

    if "selected_gallery_movie" not in st.session_state:
        st.session_state["selected_gallery_movie"] = None

    cols_per_row = 6
    for i in range(0, len(popular_movies), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, movie in enumerate(popular_movies[i:i+cols_per_row]):
            info = fetch_tmdb_info(movie)
            with cols[j]:
                if info and info["poster"]:
                    st.image(info["poster"], use_container_width=True)
                else:
                    st.markdown(
                        "<div style='height:180px;background:#333;display:flex;align-items:center;justify-content:center;color:#aaa;border-radius:8px;'>無海報</div>",
                        unsafe_allow_html=True
                    )
                if st.button(movie, key=f"gallery_{movie}", use_container_width=True):
                    st.session_state["selected_gallery_movie"] = movie
                    st.rerun()

    selected = st.session_state.get("selected_gallery_movie")
    if selected:
        info = fetch_tmdb_info(selected)
        st.divider()
        col1, col2 = st.columns([1, 3])
        with col1:
            if info and info["poster"]:
                st.image(info["poster"], width=180)
        with col2:
            st.markdown(f"## {selected}")
            if info:
                if info["release_date"]:
                    st.caption(f"上映日期：{info['release_date']}　⭐ {info['vote_average']:.1f}")
                if info["overview"]:
                    st.write(info["overview"])

        today_tw = datetime.now(TW_TZ).date()
        movie_shows = [
            s for s in all_showtimes_data
            if s["movie_name"] == selected
            and datetime.fromisoformat(s["date_time"]).date() >= today_tw
        ]
        movie_shows.sort(key=lambda x: x["date_time"])

        if movie_shows:
            theaters_showing = sorted(set(s["theater_name"] for s in movie_shows))
            for theater in theaters_showing:
                theater_shows = [s for s in movie_shows if s["theater_name"] == theater]
                url = next((t["url"] for t in theater_data if t["name"] == theater), None)
                if url:
                    st.markdown(f"### 🏟 [{theater}]({url})")
                else:
                    st.markdown(f"### 🏟 {theater}")

                cols = st.columns(6)
                for idx, s in enumerate(theater_shows):
                    dt = datetime.fromisoformat(s["date_time"])
                    with cols[idx % 6]:
                        st.markdown(
                            f"""
                            <div style='border:1px solid #444;border-radius:8px;padding:8px;margin:4px 0;text-align:center;background:#1e1e1e;'>
                                <div style='font-size:1.1em;font-weight:bold;'>{dt.strftime('%m/%d %H:%M')}</div>
                                <div style='font-size:0.8em;color:#aaa;'>{s['format_type']} | {s['language']}</div>
                                <div style='font-size:0.8em;color:#f0a500;'>💰 {s['price']} 元</div>
                                <div style='font-size:0.75em;color:#88cc88;'>{s['seat_status']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.info("目前無近期場次")

        if st.button("✕ 關閉", key="close_gallery"):
            st.session_state["selected_gallery_movie"] = None
            st.rerun()

st.divider()

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
                with cols[i % 6]:
                    st.markdown(
                        f"""
                        <div style='border:1px solid #444;border-radius:8px;padding:8px;margin:4px 0;text-align:center;background:#1e1e1e;'>
                            <div style='font-size:1.2em;font-weight:bold;'>{dt.strftime('%H:%M')}</div>
                            <div style='font-size:0.8em;color:#aaa;'>{s['format_type']} | {s['language']}</div>
                            <div style='font-size:0.8em;color:#f0a500;'>💰 {s['price']} 元</div>
                            <div style='font-size:0.75em;color:#88cc88;'>{s['seat_status']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.divider()