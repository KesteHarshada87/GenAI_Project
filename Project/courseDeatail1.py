from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- COURSE URLS ----------------
course_urls = [
    "https://sunbeaminfo.in/modular-courses/apache-spark-mastery-data-engineering-pyspark",
    "https://sunbeaminfo.in/modular-courses/aptitude-course-in-pune",
    "https://sunbeaminfo.in/modular-courses/core-java-classes",
    "https://sunbeaminfo.in/modular-courses/data-structure-algorithms-using-java",
    "https://sunbeaminfo.in/modular-courses/Devops-training-institute",
    "https://sunbeaminfo.in/modular-courses/dreamllm-training-institute-pune"
]

# ---------------- SELENIUM SETUP ----------------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

all_courses = []

# ---------------- SCRAPING ----------------
for url in course_urls:
    driver.get(url)
    time.sleep(5)

    # -------- Course Title --------
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        title = "Course Title Not Found"

    # -------- Course Info Box --------
    course_info = []
    try:
        info_elements = driver.find_elements(By.CSS_SELECTOR, "div.course_info p")
        for el in info_elements:
            course_info.append(el.text.strip())
    except:
        pass

    # -------- Accordion Sections (IMPORTANT FIX) --------
    sections_data = []

    try:
        panels = driver.find_elements(By.CSS_SELECTOR, ".panel.panel-default")

        for panel in panels:
            try:
                header = panel.find_element(By.CSS_SELECTOR, "h4.panel-title a")
                section_title = header.text.strip()

                # Open accordion
                driver.execute_script("arguments[0].click();", header)
                time.sleep(1)

                body = panel.find_element(By.CSS_SELECTOR, ".panel-collapse")
                section_text = body.text.strip()

                section_text = re.sub(r'[^\x00-\x7F]+', ' ', section_text)

                sections_data.append({
                    "title": section_title,
                    "content": section_text
                })

            except:
                continue

    except:
        sections_data.append({
            "title": "Course Content",
            "content": "No accordion data found"
        })

    all_courses.append({
        "title": title,
        "info": course_info,
        "sections": sections_data
    })

    print(f"✔ Scraped full data: {title}")

driver.quit()

# ---------------- PDF CREATION ----------------
pdf_name = "Sunbeam_Modular_Courses_Full_Content.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = []
story.append(Paragraph("<b>Sunbeam Modular Courses – Complete Syllabus & Details</b>", styles["Title"]))
story.append(Spacer(1, 20))

for course in all_courses:
    story.append(Paragraph(course["title"], styles["Heading1"]))
    story.append(Spacer(1, 10))

    # Course Info
    if course["info"]:
        story.append(Paragraph("<b>Course Information</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for info in course["info"]:
            story.append(Paragraph(info, styles["Normal"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

    # Accordion Sections
    for section in course["sections"]:
        story.append(Paragraph(section["title"], styles["Heading2"]))
        story.append(Spacer(1, 6))

        for line in section["content"].split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 4))

        story.append(Spacer(1, 10))

    story.append(PageBreak())

doc.build(story)

print(f"\n✅ PDF CREATED SUCCESSFULLY: {pdf_name}")
