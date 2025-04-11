import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
import re

# API Keys
SERP_API_KEY = "d117d85524c9f1e5bba5541adfd0511769a8a7af"
BING_API_KEY = st.secrets.get("BING_API_KEY")

@st.cache_data(show_spinner=False)
def search_gst_with_serpapi(name):
    query = f"{name} gst number"
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": 3
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        answers = []
        for result in data.get("organic_results", []):
            snippet = result.get("snippet", "")
            if "GST" in snippet.upper():
                answers.append(snippet)
        if answers:
            return answers[0]
    except:
        pass
    return None

@st.cache_data(show_spinner=False)
def search_gst_with_bing(name):
    query = f"{name} gst number"
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "mkt": "en-IN"}
    try:
        response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params, timeout=10)
        results = response.json()
        snippets = [v.get("snippet", "") for v in results.get("webPages", {}).get("value", [])]
        for snippet in snippets:
            if re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b", snippet):
                return snippet
    except:
        pass
    return None

@st.cache_data(show_spinner=False)
def google_scrape_fallback(name):
    query = f"{name} gst number"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get("https://www.google.com/search", params={"q": query}, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for span in soup.find_all("span"):
            text = span.get_text()
            if re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b", text):
                return text
    except:
        pass
    return "Not Found"

@st.cache_data(show_spinner=False)
def alt_format_web_search(name):
    # Split name into parts, replace space with underscore
    name_parts = name.strip().split()
    if len(name_parts) > 1:
        query_name = f"{name_parts[0]}_{name_parts[-1]}"
    else:
        query_name = name

    query = f"{query_name} gst number"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get("https://www.google.com/search", params={"q": query}, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for span in soup.find_all("span"):
            text = span.get_text()
            if re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b", text):
                return text
    except:
        pass
    return "Not Found"

# Recent searches
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []

def clear_recent():
    st.session_state.recent_searches = []

st.title("🔍 GST Lookup Tool (via SerpAPI, Bing & Google Fallback)")
st.markdown("Enter up to 1000 Legal Names below (one per line):")

names_input = st.text_area("Legal Names", height=300)

if st.button("Search GST Numbers") and names_input.strip():
    names = [n.strip() for n in names_input.splitlines() if n.strip()][:1000]
    output_data = []

    progress = st.progress(0)
    for i, name in enumerate(names):
        result = search_gst_with_serpapi(name)
        if not result:
            result = search_gst_with_bing(name)
        if not result:
            result = google_scrape_fallback(name)
        if not result or result == "Not Found":
            result = alt_format_web_search(name)

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
