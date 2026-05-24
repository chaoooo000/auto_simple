import json
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.models.user import User, Education, WorkExperience, ProjectExperience

load_dotenv()

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的简历信息提取专家。请从以下简历文本中提取所有关键信息。

提取规则：
1. 如果某个字段在简历中找不到对应信息，请留空（null 或空列表）
2. 教育经历请按时间倒序排列
3. 工作经历请按时间倒序排列
4. 专业技能请提取为列表，每个技能一项
5. 校园经历提取为字符串列表，每条经历一项
6. 项目经历中的 technologies 字段提取该项目使用的技术栈
7. 尽量保持原始文本中的信息，不要臆造

返回格式为 JSON，结构如下：
{{
  "name": "姓名",
  "gender": "性别",
  "age": "年龄",
  "phone": "电话",
  "email": "邮箱",
  "address": "地址",
  "degree": "最高学历",
  "major": "专业",
  "school": "毕业院校",
  "graduation_year": "毕业年份",
  "education": [
    {{
      "school": "学校名称",
      "degree": "学位",
      "major": "专业",
      "start_date": "入学时间",
      "end_date": "毕业时间"
    }}
  ],
  "skills": ["技能1", "技能2"],
  "work_experience": [
    {{
      "company": "公司名称",
      "position": "职位",
      "start_date": "入职时间",
      "end_date": "离职时间",
      "description": "工作描述"
    }}
  ],
  "project_experience": [
    {{
      "name": "项目名称",
      "role": "角色",
      "description": "项目描述",
      "technologies": ["技术1", "技术2"]
    }}
  ],
  "campus_experience": ["校园经历1", "校园经历2"],
  "certifications": ["证书1", "证书2"],
  "languages": ["语言1", "语言2"]
}}
"""),
    ("human", "请从以下简历文本中提取信息：\n\n{text}"),
])


def _build_llm() -> ChatOpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    os.environ["OPENAI_API_KEY"] = api_key if api_key else "placeholder"
    return ChatOpenAI(
        model=os.getenv("DASHSCOPE_MODEL", "qwen-max"),
        base_url=os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        temperature=0,
    )


def _parse_response_to_user(data: dict) -> User:
    education_list = [
        Education(
            school=e.get("school"),
            degree=e.get("degree"),
            major=e.get("major"),
            start_date=e.get("start_date"),
            end_date=e.get("end_date"),
        )
        for e in data.get("education", []) or []
    ]

    work_list = [
        WorkExperience(
            company=w.get("company"),
            position=w.get("position"),
            start_date=w.get("start_date"),
            end_date=w.get("end_date"),
            description=w.get("description"),
        )
        for w in data.get("work_experience", []) or []
    ]

    project_list = [
        ProjectExperience(
            name=p.get("name"),
            role=p.get("role"),
            description=p.get("description"),
            technologies=p.get("technologies", []) or [],
        )
        for p in data.get("project_experience", []) or []
    ]

    return User(
        name=data.get("name"),
        gender=data.get("gender"),
        age=data.get("age"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        degree=data.get("degree"),
        major=data.get("major"),
        school=data.get("school"),
        graduation_year=data.get("graduation_year"),
        education=education_list,
        skills=data.get("skills", []) or [],
        work_experience=work_list,
        project_experience=project_list,
        campus_experience=data.get("campus_experience", []) or [],
        certifications=data.get("certifications", []) or [],
        languages=data.get("languages", []) or [],
    )


def extract_resume_info(text: str) -> User:
    if not text or not text.strip():
        return User()

    llm = _build_llm()
    chain = EXTRACTION_PROMPT | llm

    result = chain.invoke({"text": text[:12000]})

    content = result.content if hasattr(result, "content") else str(result)

    if content.startswith("```json"):
        content = content.removeprefix("```json").removesuffix("```").strip()
    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()

    data = json.loads(content)
    user = _parse_response_to_user(data)
    user.raw_text = text
    return user
