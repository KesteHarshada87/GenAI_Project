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

        # -------- Accordion Sections --------
        sections = []

        try:
            panels = driver.find_elements(By.CSS_SELECTOR, ".panel.panel-default")

            for panel in panels:
                try:
                    header = panel.find_element(By.CSS_SELECTOR, "h4.panel-title a")
                    section_title = header.text.strip()

                    # Expand accordion
                    driver.execute_script("arguments[0].click();", header)
                    time.sleep(1)

                    body = panel.find_element(By.CSS_SELECTOR, ".panel-collapse")
                    section_content = body.text.strip()
                    section_content = re.sub(r'[^\x00-\x7F]+', ' ', section_content)

                    sections.append({
                        "title": section_title,
                        "content": section_content
                    })

                except:
                    continue

        except:
            sections.append({
                "title": "Course Content",
                "content": "No accordion data found"
            })

        all_courses.append({
            "title": title,
            "info": course_info,
            "sections": sections
        })

        print(f"✔ Scraped full content: {title}")

    except Exception as e:
        print(f"❌ Failed to scrape {url}")
        print(e)

driver.quit()

# ---------------- PDF CREATION ----------------
pdf_name = "Sunbeam_All_Modular_Courses_Full_Content.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = []
story.append(Paragraph("<b>Sunbeam Modular Courses – Complete Details</b>", styles["Title"]))
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

    # Accordion Content
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

print(f"\n✅ PDF SUCCESSFULLY CREATED: {pdf_name}")
