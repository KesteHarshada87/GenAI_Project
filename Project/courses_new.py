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

# ================== GET COURSE URLs ==================
def get_course_urls(home_url):
    driver.get(home_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    urls = driver.execute_script("""
        return Array.from(document.querySelectorAll("a"))
            .filter(a => a.href && a.href.includes("/modular-courses/"))
            .map(a => a.href);
    """)

    return list(dict.fromkeys(urls))

# ================== SCRAPE COURSE PAGE ==================
def scrape_course(url):
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    sections = []

    # ========= SCRAPE TOP PAGE CONTENT =========
    try:
        top_section = driver.find_element(By.CSS_SELECTOR, "section")
        top_text = driver.execute_script(
            "return arguments[0].innerText;", top_section
        )

        top_text = re.sub(r'[^\x00-\x7F]+', ' ', top_text).strip()

        if top_text:
            sections.append({
                "title": "Course Overview",
                "content": top_text
            })
    except:
        pass

    # ========= SCRAPE SYLLABUS / OTHER PANELS =========
    panels = driver.find_elements(By.CSS_SELECTOR, ".panel.panel-default")

    for panel in panels:
        try:
            sec_title = panel.find_element(By.CSS_SELECTOR, "h4").text.strip()
            body = panel.find_element(By.CSS_SELECTOR, ".panel-body")

            content = driver.execute_script(
                "return arguments[0].innerText;", body
            )

            content = re.sub(r'[^\x00-\x7F]+', ' ', content).strip()

            if content:
                sections.append({
                    "title": sec_title,
                    "content": content
                })
        except:
            continue

    return {
        "title": title,
        "sections": sections
    }

# ================== PDF SETUP ==================
pdf_name = "Sunbeam_Modular_Courses_COMPLETE_INFO.pdf"
doc = SimpleDocTemplate(pdf_name, pagesize=A4)
styles = getSampleStyleSheet()

story = [
    Paragraph("Sunbeam Modular Courses – Full Course Information", styles["Title"]),
    Spacer(1, 25)
]

# ================== MAIN EXECUTION ==================
home_url = "https://www.sunbeaminfo.in/modular-courses-home"
course_urls = get_course_urls(home_url)

print(f"✅ Found {len(course_urls)} courses")

for idx, url in enumerate(course_urls, start=1):
    print(f"Scraping ({idx}/{len(course_urls)}): {url}")

    course = scrape_course(url)

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
