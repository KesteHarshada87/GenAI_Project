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
    time.sleep(4)  # IMPORTANT

    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        title = "Course Title"

    body = driver.find_element(By.TAG_NAME, "body").text

    # Clean bad characters (IMPORTANT for PDF)
    body = re.sub(r'[^\x00-\x7F]+', ' ', body)

    all_courses.append({
        "title": title,
        "content": body
    })

    print(f"✔ Scraped: {title}")

driver.quit()

# ---------------- PDF CREATION ----------------
pdf_name = "Sunbeam_All_Modular_Courses.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = []
story.append(Paragraph("<b>Sunbeam Modular Courses – Complete Details</b>", styles["Title"]))
story.append(Spacer(1, 20))

for course in all_courses:
    story.append(Paragraph(course["title"], styles["Heading1"]))
    story.append(Spacer(1, 10))

    for line in course["content"].split("\n"):
        line = line.strip()
        if line:
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 4))

    story.append(PageBreak())

doc.build(story)

print(f"\n✅ PDF SUCCESSFULLY CREATED: {pdf_name}")
