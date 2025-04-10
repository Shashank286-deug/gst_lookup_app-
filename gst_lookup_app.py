import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tempfile import NamedTemporaryFile
import os

# Initialize session state for recent searches
if 'last_searches' not in st.session_state:
    st.session_state.last_searches = []

# GST Lookup Function (Updated with search click)
def get_gst_from_knowyourgst(name):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(), options=options)

        driver.get("https://www.knowyourgst.com/gst-number-search/by-name-pan/")
        time.sleep(2)

        search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Type Name or PAN or GST Number']")
        search_box.clear()
        search_box.send_keys(name)

        search_button = driver.find_element(By.XPATH, "//button[contains(text(), 'SEARCH GST NUMBER')]")
        search_button.click()
        time.sleep(5)

        results = []
        try:
            table = driver.find_element(By.CSS_SELECTOR, "table.table")
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 2:
                    gstin = cols[0].text.strip()
                    legal_name = cols[1].text.strip()
                    results.append((gstin, legal_name))
        except:
            results.append(("Not Found", "Not Found"))

        driver.quit()
        return results
    except Exception as e:
        return [("Error", str(e))]

# UI Section
st.title("🔎 GSTIN Finder (KnowYourGST)")
st.markdown("Paste up to 1000 legal names (one per line):")

input_text = st.text_area("Enter Legal Names", height=300, help="Paste legal names here, one per line")

if st.button("Find GSTINs"):
    legal_names_raw = [name.strip() for name in input_text.strip().split("\n") if name.strip()]
    legal_names = list(dict.fromkeys(legal_names_raw))

    if not legal_names:
        st.warning("Please enter at least one legal name.")
    elif len(legal_names) > 1000:
        st.warning("Limit is 1000 names. Please reduce the number of names.")
    else:
        result_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, name in enumerate(legal_names):
            all_results = get_gst_from_knowyourgst(name)
            if name not in st.session_state.last_searches:
                st.session_state.last_searches.insert(0, name)
                st.session_state.last_searches = st.session_state.last_searches[:5]

            for gstin, matched_name in all_results:
                result_data.append({
                    "Input Legal Name": name,
                    "Found GSTIN": gstin,
                    "Matched Legal Name": matched_name,
                    "Manual Link": f"https://www.knowyourgst.com/search/?q={name.replace(' ', '+')}"
                })

            progress_bar.progress((i + 1) / len(legal_names))
            status_text.text(f"{i + 1} of {len(legal_names)} processed")

        result_df = pd.DataFrame(result_data)

        def highlight_missing(val):
            return 'background-color: #fdd' if val in ["Not Found", "Error"] else ''

        st.success("✅ Lookup complete!")
        st.markdown("### 💾 Results")
        st.write(result_df.drop(columns=["Manual Link"]).style.applymap(highlight_missing, subset=["Found GSTIN"]))

        st.markdown("### 🔗 Manual Lookup Links")
        st.write(result_df[["Input Legal Name", "Manual Link"]].to_html(escape=False, index=False), unsafe_allow_html=True)

        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            result_df.drop(columns=["Manual Link"]).to_excel(tmp.name, index=False)
            st.download_button(
                label="📥 Download Results as Excel",
                data=open(tmp.name, 'rb').read(),
                file_name="gst_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            os.unlink(tmp.name)

# =========================
# Show recent search history
# =========================
st.markdown("### 🕒 Recent Legal Names Searched")

if st.session_state.last_searches:
    cols = st.columns([3, 1, 1])
    for name in st.session_state.last_searches:
        with cols[0]:
            st.markdown(f"- **{name}**")
        with cols[1]:
            if st.button(f"✏️ Edit", key=f"edit_{name}"):
                st.session_state.input_text = name
                st.experimental_rerun()
        with cols[2]:
            if st.button(f"🔁 Search Again", key=f"retry_{name}"):
                st.session_state.input_text = name
                st.session_state.trigger_single_search = True
                st.experimental_rerun()
else:
    st.write("No recent searches yet.")

if st.button("🧹 Clear Recent Searches"):
    st.session_state.last_searches = []
    st.success("Cleared search history!")

if 'trigger_single_search' in st.session_state and st.session_state.get('trigger_single_search'):
    st.session_state.trigger_single_search = False
    name = st.session_state.input_text
    if name:
        st.info(f"Reprocessing single name: {name}")
        all_results = get_gst_from_knowyourgst(name)
        result_df = pd.DataFrame([{
            "Input Legal Name": name,
            "Found GSTIN": gstin,
            "Matched Legal Name": matched_name,
            "Manual Link": f"https://www.knowyourgst.com/search/?q={name.replace(' ', '+')}"
        } for gstin, matched_name in all_results])

        def highlight_missing(val):
            return 'background-color: #fdd' if val in ["Not Found", "Error"] else ''

        st.dataframe(result_df.drop(columns=["Manual Link"]).style.applymap(highlight_missing, subset=["Found GSTIN"]))
        st.markdown("### 🔗 Manual Lookup Link")
        st.write(result_df[["Input Legal Name", "Manual Link"]].to_html(escape=False, index=False), unsafe_allow_html=True)
