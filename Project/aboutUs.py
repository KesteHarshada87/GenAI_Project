from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- Chrome Options ----------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

def scrape_page_text(url):
    driver.get(url)
    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = body_text.split("\n")

    # Keep only meaningful lines
    filtered = [
        line.strip() for line in lines
        if len(line.strip()) > 40
    ]
    return "\n\n".join(filtered)

try:
    # -------- Scrape Pages --------
    about_text = scrape_page_text("https://sunbeaminfo.in/about-us.php")
    branches_home_text = scrape_page_text("https://sunbeaminfo.in/sunbeam-branches-home")

    branch_details_1 = scrape_page_text(
        "https://sunbeaminfo.in/branch-details.php?bdid=1"
    )

    branch_details_5 = scrape_page_text(
        "https://sunbeaminfo.in/branch-details.php?bdid=5"
    )

finally:
    driver.quit()

# ---------------- Create PDF ----------------
pdf_file = "Sunbeam_Information.pdf"

doc = SimpleDocTemplate(
    pdf_file,
    pagesize=A4,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40
)

styles = getSampleStyleSheet()
story = []

# -------- About Us --------
story.append(Paragraph("<b>About Sunbeam</b>", styles["Title"]))
story.append(Spacer(1, 20))

for para in about_text.split("\n\n"):
    story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 12))

story.append(PageBreak())

# -------- Branches Home --------
story.append(Paragraph("<b>Sunbeam Branches</b>", styles["Title"]))
story.append(Spacer(1, 20))

for para in branches_home_text.split("\n\n"):
    story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 12))

story.append(PageBreak())

# -------- Branch Details (bdid=1) --------
story.append(Paragraph("<b>Sunbeam Branch Details – ID 1</b>", styles["Title"]))
story.append(Spacer(1, 20))

for para in branch_details_1.split("\n\n"):
    story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 12))

story.append(PageBreak())

# -------- Branch Details (bdid=5) --------
story.append(Paragraph("<b>Sunbeam Branch Details – ID 5</b>", styles["Title"]))
story.append(Spacer(1, 20))

for para in branch_details_5.split("\n\n"):
    story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 12))

doc.build(story)

print("✅ PDF created successfully: Sunbeam_Information.pdf")