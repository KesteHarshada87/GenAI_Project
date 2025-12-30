from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Setup Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=chrome_options)

# Open the *correct* modular courses page
url = "https://sunbeaminfo.in/modular-courses-home"
driver.get(url)
time.sleep(3)  # give time for page to fully load

# Scrape visible course blocks
course_blocks = driver.find_elements(By.XPATH,
    "//div[contains(., 'Duration') and .//text()]")

courses = []
for block in course_blocks:
    text = block.text.strip()
    if text and "Duration" in text:
        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        courses.append("\n".join(lines))

driver.quit()

# Create PDF
pdf_filename = "modular_courses_list.pdf"
c = canvas.Canvas(pdf_filename, pagesize=letter)
width, height = letter

y = height - 50
c.setFont("Helvetica-Bold", 14)
c.drawString(50, y, "Sunbeam Modular Courses List")
c.setFont("Helvetica", 10)
y -= 30

for course in courses:
    for line in course.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.drawString(50, y, line)
        y -= 16
    y -= 12  # space between courses

c.save()
print(f"PDF saved as: {pdf_filename}")
