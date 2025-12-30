from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# ================== SELENIUM SETUP ==================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 20)

# ================== GET ALL COURSE URLS (SAFE) ==================
def get_course_urls(home_url):
    driver.get(home_url)

    # wait for page to load
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # extract links via JavaScript to avoid stale elements
    urls = driver.execute_script("""
        return Array.from(document.querySelectorAll('a'))
            .map(a => a.href)
            .filter(href =>
                href &&
                href.includes('/modular-courses/') &&
                !href.includes('home')
            );
    """)

    # remove duplicates while preserving order
    unique_urls = list(dict.fromkeys(urls))
    return unique_urls

# ================== SCRAPE COURSE PAGE ==================
def scrape_course(url):
    driver.get(url)

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        return None

    sections = []

    # primary syllabus panels
    panels = driver.find_elements(By.CSS_SELECTOR, ".panel.panel-default")
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

    # fallback if panels not found
    if not sections:
        try:
            main = driver.find_element(By.TAG_NAME, "section")
            content = driver.execute_script(
                "return arguments[0].innerText;", main
            )

            content = re.sub(r'[^\x00-\x7F]+', ' ', content).strip()

            if content:
                sections.append({
                    "title": "Course Content",
                    "content": content
                })
        except:
            pass

    return {
        "title": title,
        "sections": sections
    }

# ================== PDF SETUP ==================
pdf_name = "Sunbeam_Modular_Courses.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = [
    Paragraph("Sunbeam Modular Courses – Complete Syllabus", styles["Title"]),
    Spacer(1, 30)
]

# ================== MAIN EXECUTION ==================
home_url = "https://www.sunbeaminfo.in/modular-courses-home"

course_urls = get_course_urls(home_url)
print(f"Found {len(course_urls)} courses")

for course_url in course_urls:
    print(f"Scraping: {course_url}")

    course = scrape_course(course_url)
    if not course:
        print("⚠️ Skipping course")
        continue

    story.append(Paragraph(course["title"], styles["Heading1"]))
    story.append(Spacer(1, 12))

    for sec in course["sections"]:
        story.append(Paragraph(sec["title"], styles["Heading2"]))
        story.append(Spacer(1, 6))

        for line in sec["content"].split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Normal"]))
                story.append(Spacer(1, 4))

    story.append(PageBreak())

driver.quit()
doc.build(story)

print("✅ PDF GENERATED SUCCESSFULLY")
