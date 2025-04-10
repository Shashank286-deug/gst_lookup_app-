def get_gst_from_knowyourgst(name):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(), options=options)

        driver.get("https://www.knowyourgst.com/gst-number-search/by-name-pan/")
        time.sleep(2)

        # Enter the name into the search bar
        search_box = driver.find_element(By.ID, "search_input")
        search_box.clear()
        search_box.send_keys(name)
        search_box.send_keys(Keys.RETURN)

        # Wait for results to load
        time.sleep(5)

        # Look for table with GSTINs
        try:
            table = driver.find_element(By.CSS_SELECTOR, "table.table")
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 2:
                    gstin = cols[0].text.strip()
                    legal_name = cols[1].text.strip()
                    if name.lower() in legal_name.lower():
                        driver.quit()
                        return gstin, legal_name
            driver.quit()
            return "Not Found", "Not Found"
        except:
            driver.quit()
            return "No table", "No table"
    except Exception as e:
        return "Error", str(e)
