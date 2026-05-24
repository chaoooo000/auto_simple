from pydantic import BaseModel, Field
from typing import Optional


class Education(BaseModel):
    school: Optional[str] = Field(default=None, description="学校名称")
    degree: Optional[str] = Field(default=None, description="学位，如本科、硕士、博士")
    major: Optional[str] = Field(default=None, description="专业名称")
    start_date: Optional[str] = Field(default=None, description="入学时间")
    end_date: Optional[str] = Field(default=None, description="毕业时间")


class WorkExperience(BaseModel):
    company: Optional[str] = Field(default=None, description="公司名称")
    position: Optional[str] = Field(default=None, description="职位")
    start_date: Optional[str] = Field(default=None, description="入职时间")
    end_date: Optional[str] = Field(default=None, description="离职时间")
    description: Optional[str] = Field(default=None, description="工作描述")


class ProjectExperience(BaseModel):
    name: Optional[str] = Field(default=None, description="项目名称")
    role: Optional[str] = Field(default=None, description="担任角色")
    description: Optional[str] = Field(default=None, description="项目描述")
    technologies: list[str] = Field(default_factory=list, description="使用的技术栈")


class User(BaseModel):
    name: Optional[str] = Field(default=None, description="姓名")
    gender: Optional[str] = Field(default=None, description="性别")
    age: Optional[str] = Field(default=None, description="年龄")
    phone: Optional[str] = Field(default=None, description="联系电话")
    email: Optional[str] = Field(default=None, description="电子邮箱")
    address: Optional[str] = Field(default=None, description="居住地址")
    degree: Optional[str] = Field(default=None, description="最高学历")
    major: Optional[str] = Field(default=None, description="专业")
    school: Optional[str] = Field(default=None, description="毕业院校")
    graduation_year: Optional[str] = Field(default=None, description="毕业年份")
    education: list[Education] = Field(default_factory=list, description="教育经历")
    skills: list[str] = Field(default_factory=list, description="专业技能")
    work_experience: list[WorkExperience] = Field(default_factory=list, description="工作经历")
    project_experience: list[ProjectExperience] = Field(default_factory=list, description="项目经历")
    campus_experience: list[str] = Field(default_factory=list, description="校园经历")
    certifications: list[str] = Field(default_factory=list, description="证书/资质")
    languages: list[str] = Field(default_factory=list, description="语言能力")
    raw_text: Optional[str] = Field(default=None, description="原始解析文本")

    def to_summary_dict(self) -> dict:
        return {
            "姓名": self.name or "",
            "性别": self.gender or "",
            "年龄": self.age or "",
            "电话": self.phone or "",
            "邮箱": self.email or "",
            "地址": self.address or "",
            "最高学历": self.degree or "",
            "专业": self.major or "",
            "毕业院校": self.school or "",
            "毕业年份": self.graduation_year or "",
            "专业技能": "、".join(self.skills) if self.skills else "",
            "工作经历": "；".join(
                f"{w.company or ''}-{w.position or ''}" for w in self.work_experience
            ) if self.work_experience else "",
            "项目经历": "；".join(
                p.name or "" for p in self.project_experience
            ) if self.project_experience else "",
            "校园经历": "；".join(self.campus_experience) if self.campus_experience else "",
            "证书资质": "、".join(self.certifications) if self.certifications else "",
            "语言能力": "、".join(self.languages) if self.languages else "",
        }
