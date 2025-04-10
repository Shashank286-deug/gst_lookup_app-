import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tempfile import NamedTemporaryFile
import os

# Function to search GSTIN based on Legal Name from KnowYourGST
def get_gst_from_knowyourgst(name):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(), options=options)

        search_url = f"https://www.knowyourgst.com/search/?q={name.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(3)

        rows = driver.find_elements(By.CSS_SELECTOR, 'table tr')
        for row in rows[1:]:
            columns = row.find_elements(By.TAG_NAME, 'td')
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
st.title("🔎 GSTIN Finder from Legal Names")
st.write("Paste up to 1000 legal names (one per line) below:")

input_text = st.text_area("Enter Legal Names", height=300, help="Paste legal names here, one per line")

if st.button("Find GSTINs"):
    legal_names = [name.strip() for name in input_text.strip().split("\n") if name.strip()]

    if not legal_names:
        st.warning("Please enter at least one legal name.")
    elif len(legal_names) > 1000:
        st.warning("Limit is 1000 names. Please reduce the number of names.")
    else:
        result_data = []
        with st.spinner("Fetching GSTINs..."):
            for name in legal_names:
                gstin, official_name = get_gst_from_knowyourgst(name)
                result_data.append({
                    "Input Legal Name": name,
                    "Found GSTIN": gstin,
                    "Matched Legal Name": official_name
                })

        result_df = pd.DataFrame(result_data)
        st.success("Lookup complete!")
        st.dataframe(result_df)

        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            result_df.to_excel(tmp.name, index=False)
            st.download_button(
                label="📥 Download Results as Excel",
                data=open(tmp.name, 'rb').read(),
                file_name="gst_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            os.unlink(tmp.name)
