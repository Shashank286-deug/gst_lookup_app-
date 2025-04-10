import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from tempfile import NamedTemporaryFile
import os

# GST Lookup using the search bar from the KnowYourGST direct search page
def get_gst_from_knowyourgst(name):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(), options=options)

        driver.get("https://www.knowyourgst.com/gst-number-search/by-name-pan/")
        time.sleep(3)

        # Find the input field and submit the name
        search_box = driver.find_element(By.ID, "search_input")
        search_box.clear()
        search_box.send_keys(name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(4)

        # Look for table rows with results
        rows = driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) >= 2:
                gstin = columns[0].text.strip()
                legal_name = columns[1].text.strip()
                if name.lower() in legal_name.lower():
                    driver.quit()
                    return gstin, legal_name

        driver.quit()
        return "Not Found", "Not Found"
    except Exception as e:
        return "Error", str(e)

# Streamlit UI
st.title("🔎 GSTIN Finder (Using KnowYourGST Search)")
st.write("Paste up to 1000 legal names (one per line) below:")

input_text = st.text_area("Enter Legal Names", height=300, help="Paste legal names here, one per line")

if st.button("Find GSTINs"):
    legal_names_raw = [name.strip() for name in input_text.strip().split("\n") if name.strip()]
    legal_names = list(dict.fromkeys(legal_names_raw))  # remove duplicates

    if not legal_names:
        st.warning("Please enter at least one legal name.")
    elif len(legal_names) > 1000:
        st.warning("Limit is 1000 names. Please reduce the number of names.")
    else:
        st.info(f"Processing {len(legal_names)} unique names (removed {len(legal_names_raw) - len(legal_names)} duplicates).")
        result_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, name in enumerate(legal_names):
            gstin, official_name = get_gst_from_knowyourgst(name)
            result_data.append({
                "Input Legal Name": name,
                "Found GSTIN": gstin,
                "Matched Legal Name": official_name
            })
            progress_bar.progress((i + 1) / len(legal_names))
            status_text.text(f"{i + 1} of {len(legal_names)} processed")

        result_df = pd.DataFrame(result_data)

        # Highlight Not Found/Error
        def highlight_missing(val):
            if val in ["Not Found", "Error"]:
                return 'background-color: #fdd'
            return ''

        st.success("✅ Lookup complete!")
        st.dataframe(result_df.style.applymap(highlight_missing, subset=["Found GSTIN"]))

        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            result_df.to_excel(tmp.name, index=False)
            st.download_button(
                label="📥 Download Results as Excel",
                data=open(tmp.name, 'rb').read(),
                file_name="gst_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            os.unlink(tmp.name)
