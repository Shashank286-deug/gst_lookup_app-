import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import BytesIO

# Bing Search API config
BING_API_KEY = st.secrets["BING_API_KEY"]
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

# Cache results
@st.cache_data

def get_gst_via_bing(name):
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    query = f"{name} GST number"
    params = {"q": query, "count": 5}

    try:
        response = requests.get(BING_ENDPOINT, headers=headers, params=params)
        results = []
        if response.status_code == 200:
            data = response.json()
            for result in data.get("webPages", {}).get("value", []):
                url = result["url"]
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                text = soup.get_text()
                matches = re.findall(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', text)
                for match in matches:
                    results.append((match, name))
            if not results:
                results.append(("Not Found", name))
        else:
            results.append(("Error", f"API error: {response.status_code}"))
    except Exception as e:
        results.append(("Error", str(e)))
    return results

# Recent searches memory
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []

def clear_recent():
    st.session_state.recent_searches = []

st.title("🔍 GST Lookup Tool (via Bing Search)")
st.markdown("Enter up to 1000 Legal Names below (one per line):")

names_input = st.text_area("Legal Names", height=300)

if st.button("Search GST Numbers") and names_input.strip():
    names = [n.strip() for n in names_input.splitlines() if n.strip()][:1000]
    output_data = []

    progress = st.progress(0)
    for i, name in enumerate(names):
        gst_results = get_gst_via_bing(name)
        found = gst_results[0][0] if gst_results else "Not Found"
        output_data.append({"Legal Name": name, "GST Number": found})

        # Save to recent searches (latest 5)
        if name not in st.session_state.recent_searches:
            st.session_state.recent_searches.insert(0, name)
            st.session_state.recent_searches = st.session_state.recent_searches[:5]

        progress.progress((i + 1) / len(names))

    df = pd.DataFrame(output_data)
    st.dataframe(df)

    # Download Excel
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button("📥 Download Results as Excel", output.getvalue(), file_name="gst_results.xlsx")

# Recent search section
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
