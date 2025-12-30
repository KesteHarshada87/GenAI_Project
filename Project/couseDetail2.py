from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- COURSE URLS (FIXED) ----------------
course_urls = [
    "https://sunbeaminfo.in/modular-courses/machine-learning-classes",
    "https://sunbeaminfo.in/modular-courses/mastering-generative-ai",
    "https://sunbeaminfo.in/modular-courses.php?mdid=57",
    "https://sunbeaminfo.in/modular-courses/mern-full-stack-developer-course",
    "https://sunbeaminfo.in/modular-courses/mlops-llmops-training-institute-pune",
    "https://sunbeaminfo.in/modular-courses/python-classes-in-pune"
]

# ---------------- SELENIUM SETUP ----------------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)

driver = webdriver.Chrome(options=options)

all_courses = []

# ---------------- SCRAPING ----------------
for url in course_urls:
    try:
        print(f"\n🔎 Opening: {url}")
        driver.get(url)
        time.sleep(4)

        try:
            title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            title = "Course Title Not Found"

        body = driver.find_element(By.TAG_NAME, "body").text
        body = re.sub(r'[^\x00-\x7F]+', ' ', body)

        all_courses.append({
            "title": title,
            "content": body
        })

        print(f"✔ Scraped: {title}")

    except Exception as e:
        print(f"❌ Failed to scrape {url}")
        print(e)

driver.quit()

# ---------------- PDF CREATION ----------------
pdf_name = "Sunbeam_All_Modular_Courses1.pdf"
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
