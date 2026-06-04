import fitz

doc = fitz.open("student_profiles/synthetic_student_001.pdf")

for page in doc:
    print(page.get_text())