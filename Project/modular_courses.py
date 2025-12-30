from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, re

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# ================== SELENIUM ==================
options = Options()
# COMMENT HEADLESS FOR DEBUG
# options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ================== STEP 1: MANUAL VERIFIED COURSE LIST ==================
# 🔥 THIS IS NECESSARY BECAUSE SUNBEAM DOES NOT MARK LINKS PROPERLY

driver.get("https://sunbeaminfo.in/modular-courses")
time.sleep(5)

course_urls = []

cards = driver.find_elements(By.CSS_SELECTOR, "div.course-card a")

for card in cards:
    url = card.get_attribute("href")
    if url and url.startswith("https://sunbeaminfo.in/modular-courses/"):
        course_urls.append(url)

course_urls = list(set(course_urls))
print("COURSE URLS FOUND:")
for u in course_urls:
    print(u)

# ================== STEP 2: SCRAPE ==================
all_courses = []

for url in course_urls:
    print(f"\n🔍 Opening: {url}")
    driver.get(url)
    time.sleep(5)

    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        print("❌ No title found, skipping")
        continue

    print(f"✅ Title: {title}")

    sections = []

    panels = driver.find_elements(By.CSS_SELECTOR, ".panel.panel-default")

    print(f"   Panels found: {len(panels)}")

    for panel in panels:
        try:
            section_title = panel.find_element(By.CSS_SELECTOR, "h4").text.strip()
            body = panel.find_element(By.CSS_SELECTOR, ".panel-body")

            content = driver.execute_script(
                "return arguments[0].innerText;", body
            )

            content = re.sub(r'[^\x00-\x7F]+', ' ', content).strip()

            if content:
                sections.append({
                    "title": section_title,
                    "content": content
                })
        except:
            continue

    if not sections:
        print("⚠️ No syllabus content found")

    all_courses.append({
        "title": title,
        "sections": sections
    })

print(f"\n🔥 TOTAL COURSES SCRAPED: {len(all_courses)}")
driver.quit()

# ================== STEP 3: PDF ==================
pdf_name = "Sunbeam_Modular_Courses_FINAL.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = []
story.append(Paragraph("Sunbeam Modular Courses – Complete Syllabus", styles["Title"]))
story.append(Spacer(1, 30))

for course in all_courses:
    story.append(Paragraph(course["title"], styles["Heading1"]))
    story.append(Spacer(1, 12))

    for sec in course["sections"]:
        story.append(Paragraph(sec["title"], styles["Heading2"]))
        story.append(Spacer(1, 6))

        for line in sec["content"].split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 4))

    story.append(PageBreak())

doc.build(story)

print("\n✅ PDF GENERATED SUCCESSFULLY")
