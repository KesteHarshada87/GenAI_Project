from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- URL ----------------
URL = "https://www.sunbeaminfo.in/internship"

# ---------------- SELENIUM SETUP ----------------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)

driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(5)

all_data = []

# ---------------- SCRAPE WHOLE PAGE ----------------
try:
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        title = "Sunbeam Internship Program"

    body = driver.find_element(By.TAG_NAME, "body").text
    body = re.sub(r'[^\x00-\x7F]+', ' ', body)  # remove unsupported chars

    all_data.append({
        "title": title + " (Full Page Content)",
        "content": body
    })

    print(f"✔ Scraped full page content: {title}")

except Exception as e:
    print("❌ Failed to scrape full page content")
    print(e)

# ---------------- SCRAPE ACCORDION BOXES ----------------
try:
    panels = driver.find_elements(By.CSS_SELECTOR, ".panel.panel-default")

    for panel in panels:
        try:
            # Title
            title_el = panel.find_element(By.CSS_SELECTOR, "h4.panel-title a")
            title = title_el.text.strip()

            # Click to open
            driver.execute_script("arguments[0].click();", title_el)
            time.sleep(1)

            # Content
            content_el = panel.find_element(By.CSS_SELECTOR, ".panel-collapse")
            content = content_el.text.strip()
            content = re.sub(r'[^\x00-\x7F]+', ' ', content)

            all_data.append({
                "title": title + " (Accordion Box)",
                "content": content
            })

            print(f"✔ Scraped accordion box: {title}")

        except Exception as e:
            print("❌ Error scraping a box", e)

except Exception as e:
    print("❌ Error finding accordion boxes", e)

driver.quit()

# ---------------- PDF CREATION ----------------
pdf_name = "Sunbeam_Internship_Complete_Full_Data.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = []
story.append(Paragraph("<b>Sunbeam Internship – Complete Details</b>", styles["Title"]))
story.append(Spacer(1, 20))

for item in all_data:
    story.append(Paragraph(item["title"], styles["Heading1"]))
    story.append(Spacer(1, 10))

    for line in item["content"].split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 4))

    story.append(PageBreak())

doc.build(story)

print(f"\n✅ PDF CREATED SUCCESSFULLY: {pdf_name}")
