import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Gemini API config
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Query Gemini API for GST info
@st.cache_data
def get_gst_via_gemini(name):
    prompt = f"Search for the GST number of the company '{name}' in India. Return only the GST number if available, or say 'Not Found'."
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return [(content, name)]
        else:
            return [("Error", f"API {response.status_code}")]
    except Exception as e:
        return [("Error", str(e))]

# Recent searches memory
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []

def clear_recent():
    st.session_state.recent_searches = []

st.title("🔍 GST Lookup Tool (via Gemini AI)")
st.markdown("Enter up to 1000 Legal Names below (one per line):")

names_input = st.text_area("Legal Names", height=300)

if st.button("Search GST Numbers") and names_input.strip():
    names = [n.strip() for n in names_input.splitlines() if n.strip()][:1000]
    output_data = []

    progress = st.progress(0)
    for i, name in enumerate(names):
        gst_results = get_gst_via_gemini(name)
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
