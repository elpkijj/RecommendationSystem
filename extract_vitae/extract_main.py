import re
import PyPDF2

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)

        text = ""
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

    return text

def match_titles_and_extract_skills(resume_file, unique_titles_file):
    resume_text = extract_text_from_pdf(resume_file)


    # 读取unique_title.txt中的职称列表
    with open(unique_titles_file, 'r', encoding='utf-8') as file:
        unique_titles = [line.strip() for line in file.readlines()]

    title = None
    skills = ""

    # 匹配专业技能
    keywords = [
        r"数据分析软件",
        r"pytorch深度学习框架",
        r"sklearn机器学习框架",
        r"数据挖掘",
        r"机器学习",
        r"概率论统计基础理论知识"
    ]

    for keyword in keywords:
        matches = re.findall(keyword, resume_text)
        if matches:
            skills += matches[0] + "\n"

    if skills:
        title = "算法工程师"

    return title, skills.strip()

# 示例用法
resume_file = '曹锦的简历.pdf'
unique_titles_file = 'unique_title.txt'

title, skills = match_titles_and_extract_skills(resume_file, unique_titles_file)
print("匹配的职称：", title)
print("提取的专业技能：", skills)
