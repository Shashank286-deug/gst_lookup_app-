import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import re

# Brave API Key
GOOGLE_API_KEY= "AIzaSyA8CgZ39m5oDOE8dqdNR45AYTGlX9_4cgY"

@st.cache_data(show_spinner=False)
def search_gst_with_brave(name):
    query = f"{name} gst number"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": GOOGLE_API_KEY
    }
    params = {"q": query, "count": 3}
    try:
        response = requests.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params, timeout=10)
        results = response.json()
        for item in results.get("web", {}).get("results", []):
            snippet = item.get("description", "")
            match = re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b", snippet)
            if match:
                return match.group(0)
    except:
        pass
    return "Not Found"

# Recent searches
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []

def clear_recent():
    st.session_state.recent_searches = []

st.title("🔍 GST Lookup Tool (via Brave API)")
st.markdown("Enter up to 1000 Legal Names below (one per line):")

names_input = st.text_area("Legal Names", height=300)

if st.button("Search GST Numbers") and names_input.strip():
    names = [n.strip() for n in names_input.splitlines() if n.strip()][:1000]
    output_data = []

    progress = st.progress(0)
    for i, name in enumerate(names):
        result = search_gst_with_brave(name)

        output_data.append({"Legal Name": name, "GST Number": result})

        # Store recent
        if name not in st.session_state.recent_searches:
            st.session_state.recent_searches.insert(0, name)
            st.session_state.recent_searches = st.session_state.recent_searches[:5]

        progress.progress((i + 1) / len(names))

    df = pd.DataFrame(output_data)
    st.dataframe(df)

    # Download
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button("📥 Download Results as Excel", output.getvalue(), file_name="gst_results.xlsx")

# Recent search list
st.subheader("🕘 Recent Searches")
for i, name in enumerate(st.session_state.recent_searches):
    cols = st.columns([4, 1, 1])
    with cols[0]:
        st.text_input(f"Recent {i+1}", name, key=f"recent_{i}")
    with cols[1]:
        if st.button("🔁 Re-search", key=f"re_{i}"):
            names_input = name
            st.rerun()
    with cols[2]:
        if st.button("❌ Remove", key=f"rm_{i}"):
            st.session_state.recent_searches.pop(i)
            st.rerun()

if st.button("🧹 Clear All Recent Searches"):
    clear_recent()
    st.success("Cleared all recent searches!")
