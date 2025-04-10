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
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)

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

# Streamlit App UI
st.title("🔎 GSTIN Finder from Legal Name")
st.write("Upload an Excel file with a column named `Legal Name`.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if 'Legal Name' not in df.columns:
            st.error("Please make sure your Excel file has a column named 'Legal Name'")
        else:
            if st.button("Start GSTIN Lookup"):
                result_data = []

                with st.spinner("Fetching GSTINs..."):
                    for name in df['Legal Name']:
                        gstin, official_name = get_gst_from_knowyourgst(name)
                        result_data.append({
                            "Input Legal Name": name,
                            "Found GSTIN": gstin,
                            "Matched Legal Name": official_name
                        })

                result_df = pd.DataFrame(result_data)
                st.success("Lookup complete!")
                st.dataframe(result_df)

                # Merge results with original file
                output_df = pd.concat([df, result_df.drop(columns=["Input Legal Name"])], axis=1)

                with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    output_df.to_excel(tmp.name, index=False)
                    st.download_button(
                        label="📥 Download Results as Excel",
                        data=open(tmp.name, 'rb').read(),
                        file_name="gst_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    os.unlink(tmp.name)

    except Exception as e:
        st.error(f"Error processing file: {e}")
