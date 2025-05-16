import streamlit as st
from scraping import scrape_website, extract_video_data

st.set_page_config(page_title="Not YouTube", page_icon="./blast.png", layout="wide")
st.logo(
    image="./blast.png",
    size="large", 
    link=None, 
    icon_image=None
    )
st.title("Not YouTube – Channel Scraper")

channel_url = st.text_input(
    "Paste a YouTube *channel* /videos URL",
    value="",
)

if st.button("Fetch Videos"):
    with st.spinner("Scraping… this can take a few seconds ⏳"):
        html          = scrape_website(channel_url)
        video_cards   = extract_video_data(html, channel_url)
        st.session_state["videos"] = video_cards
        st.session_state.pop("current", None)  # reset current video

# ────────────────────────────────────────────────────────────────

with st.container(border=True):
    videos = st.session_state.get("videos", [])
    if videos:
        st.subheader(f"Found {len(videos)} videos")
        cols = st.columns(4)

        for idx, video in enumerate(videos):
            col = cols[idx % 4]  # 4-across grid
            with col:
                st.image(video["thumbnail"], use_container_width=True)
                st.markdown(
                    f"**{video['title']}**\n\n"
                    f"{video['views']} • {video['date']}",
                    help=video["video_url"],
                )
                if st.button("▶ Watch", key=f"watch_{idx}"):
                    st.session_state["current"] = video["video_url"]

# ────────────────────────────────────────────────────────────────
if "current" in st.session_state:
    st.divider()
    st.subheader("Now Playing")
    st.video(st.session_state["current"])
