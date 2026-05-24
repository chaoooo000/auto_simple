from dataclasses import dataclass, field
from src.models.user import User


@dataclass
class Department:
    name: str
    description: str
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    required_majors: list[str] = field(default_factory=list)
    preferred_degrees: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    position_keywords: list[str] = field(default_factory=list)
    tech_keywords: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    department: Department
    score: float
    reasons: list[str] = field(default_factory=list)


SKILL_SYNONYMS: dict[str, list[str]] = {
    "python": ["python3", "py"],
    "javascript": ["js", "es6", "es2015"],
    "typescript": ["ts"],
    "kubernetes": ["k8s", "k3s"],
    "react": ["react.js", "reactjs"],
    "vue": ["vue.js", "vuejs"],
    "node.js": ["node", "nodejs"],
    "docker": ["container"],
    "机器学习": ["machine learning", "ml"],
    "深度学习": ["deep learning", "dl"],
    "自然语言处理": ["nlp", "自然语言"],
    "计算机视觉": ["cv", "视觉", "图像识别"],
    "pytorch": ["torch"],
    "tensorflow": ["tf"],
    "数据库": ["database", "db", "mysql", "postgresql", "mongodb"],
    "sql": ["mysql", "postgresql", "sqlite", "oracle"],
    "redis": ["缓存", "cache"],
    "linux": ["unix", "shell"],
    "微服务": ["microservice", "microservices"],
    "django": ["flask", "fastapi"],
    "spring": ["springboot", "spring boot"],
    "html": ["html5"],
    "css": ["css3", "sass", "less", "scss"],
    "webpack": ["vite", "rollup"],
    "小程序": ["微信小程序", "miniapp", "mini program"],
    "flutter": ["react native", "rn"],
    "selenium": ["webdriver"],
    "ci/cd": ["cicd", "jenkins", "github actions"],
    "tableau": ["power bi", "powerbi", "superset"],
    "spark": ["pyspark"],
    "hive": ["presto"],
    "数据仓库": ["data warehouse", "dw", "dwh"],
    "etl": ["数据管道", "data pipeline"],
}


DEGREE_HIERARCHY = {
    "博士": 3, "硕士": 2, "本科": 1, "大专": 0, "专科": 0,
    "phd": 3, "master": 2, "bachelor": 1, "associate": 0,
}


DEPARTMENTS = [
    Department(
        name="后端开发部",
        description="负责服务端架构设计、API开发、数据库管理与系统性能优化",
        required_skills=["Python", "Java", "Go", "C++", "数据库", "SQL", "Redis", "Linux"],
        preferred_skills=["Django", "Spring", "微服务", "Docker", "Kubernetes", "消息队列", "RESTful", "gRPC"],
        required_majors=["计算机科学", "软件工程", "计算机技术", "信息工程", "计算机"],
        keywords=["后端", "服务端", "API", "数据库", "服务器", "并发", "分布式", "高可用"],
        position_keywords=["后端", "服务端", "java开发", "python开发", "go开发", "架构师", "后台"],
        tech_keywords=["spring", "django", "mybatis", "redis", "kafka", "rabbitmq", "nginx", "mysql"],
    ),
    Department(
        name="前端开发部",
        description="负责Web前端、移动端界面开发，用户体验优化与前端工程化建设",
        required_skills=["JavaScript", "TypeScript", "HTML", "CSS", "React", "Vue"],
        preferred_skills=["Node.js", "Webpack", "小程序", "Flutter", "Electron", "Next.js", "Nuxt"],
        required_majors=["计算机科学", "软件工程", "数字媒体", "设计"],
        keywords=["前端", "UI", "页面", "H5", "小程序", "Web", "浏览器", "响应式", "组件"],
        position_keywords=["前端", "h5", "web前端", "小程序开发", "移动端", "flutter", "react native"],
        tech_keywords=["react", "vue", "angular", "webpack", "vite", "sass", "less", "css"],
    ),
    Department(
        name="算法与AI部",
        description="负责机器学习、深度学习算法研发，自然语言处理、计算机视觉等AI应用落地",
        required_skills=["Python", "机器学习", "深度学习", "PyTorch", "数学"],
        preferred_skills=["NLP", "CV", "推荐系统", "大模型", "数据挖掘", "强化学习", "TensorFlow", "CUDA"],
        required_majors=["计算机科学", "人工智能", "数学", "统计学", "电子信息", "自动化"],
        keywords=["算法", "AI", "模型", "神经网络", "训练", "预测", "分类", "识别", "transformer", "llm"],
        position_keywords=["算法", "ai", "机器学习", "深度学习", "nlp", "cv", "数据科学家"],
        tech_keywords=["pytorch", "tensorflow", "transformer", "bert", "gpt", "llama", "cuda"],
    ),
    Department(
        name="数据分析部",
        description="负责业务数据分析、数据仓库建设、BI报表开发与数据驱动决策支持",
        required_skills=["SQL", "Python", "Excel", "统计学"],
        preferred_skills=["Tableau", "Power BI", "Spark", "Hive", "数据仓库", "ETL", "Pandas", "NumPy"],
        required_majors=["统计学", "数学", "计算机科学", "经济学", "信息管理"],
        keywords=["数据", "分析", "报表", "统计", "BI", "指标", "看板", "建模"],
        position_keywords=["数据分析", "bi", "数据仓库", "etl", "数据开发", "商业分析"],
        tech_keywords=["tableau", "powerbi", "spark", "hadoop", "sql", "excel", "pandas", "numpy"],
    ),
    Department(
        name="产品部",
        description="负责产品规划、需求分析、竞品调研、产品设计与迭代管理",
        required_skills=["需求分析", "产品设计", "项目管理", "数据分析"],
        preferred_skills=["Axure", "Figma", "敏捷开发", "用户研究", "A/B测试", "JIRA"],
        required_majors=["计算机科学", "信息管理", "市场营销", "心理学", "工业设计"],
        keywords=["产品", "需求", "用户", "体验", "原型", "迭代", "PRD", "竞品"],
        position_keywords=["产品经理", "产品", "pm", "product"],
        tech_keywords=["axure", "figma", "sketch", "jira", "confluence"],
    ),
    Department(
        name="测试与质量保障部",
        description="负责软件测试、自动化测试框架搭建、质量保障体系建设",
        required_skills=["测试", "Python", "自动化测试"],
        preferred_skills=["Selenium", "JMeter", "CI/CD", "安全测试", "接口测试", "Appium", "性能测试", "Pytest"],
        required_majors=["计算机科学", "软件工程", "信息工程", "计算机"],
        keywords=["测试", "QA", "质量", "Bug", "用例", "回归", "自动化", "验收"],
        position_keywords=["测试", "qa", "质量", "测试开发", "自动化测试"],
        tech_keywords=["selenium", "jmeter", "pytest", "appium", "postman", "fiddler"],
    ),
    Department(
        name="市场与运营部",
        description="负责市场推广、品牌运营、用户增长与活动策划",
        required_skills=["市场营销", "数据分析", "内容运营", "活动策划"],
        preferred_skills=["SEO", "SEM", "新媒体", "社群运营", "品牌管理", "PS", "剪映"],
        required_majors=["市场营销", "广告学", "传媒", "工商管理", "经济学"],
        keywords=["市场", "运营", "推广", "品牌", "用户增长", "活动", "营销", "新媒体"],
        position_keywords=["运营", "市场", "营销", "新媒体", "品牌", "seo", "sem"],
        tech_keywords=["seo", "sem", "google analytics", "百度统计"],
    ),
    Department(
        name="人力资源部",
        description="负责招聘、培训、绩效管理、员工关系与企业文化建设",
        required_skills=["招聘", "人力资源", "沟通", "组织协调"],
        preferred_skills=["HRBP", "薪酬设计", "培训开发", "劳动法", "OKR", "KPI"],
        required_majors=["人力资源", "心理学", "管理学", "社会学"],
        keywords=["HR", "人力", "招聘", "培训", "员工", "绩效", "薪酬"],
        position_keywords=["hr", "人力资源", "招聘", "人事", "培训"],
        tech_keywords=[],
    ),
]


class DepartmentMatcher:
    def __init__(self, departments: list[Department] | None = None):
        self.departments = departments or DEPARTMENTS
        self._synonym_index = SKILL_SYNONYMS

    def _expand_skills(self, skills: list[str]) -> set[str]:
        result: set[str] = set()
        for s in skills:
            key = s.lower().strip()
            result.add(key)
            synonyms = self._synonym_index.get(key, [])
            result.update(synonyms)
            for sk, sv in self._synonym_index.items():
                if s.lower() in sv:
                    result.add(sk)
        return result

    def _collect_user_text(self, user: User) -> str:
        parts = [user.name or "", user.major or "", user.degree or "", user.school or ""]
        parts.extend(user.skills)
        for edu in user.education:
            parts.append(edu.major or "")
            parts.append(edu.school or "")
        for work in user.work_experience:
            parts.append(work.position or "")
            parts.append(work.description or "")
            parts.append(work.company or "")
        for proj in user.project_experience:
            parts.append(proj.name or "")
            parts.append(proj.description or "")
            parts.extend(proj.technologies)
        parts.extend(user.certifications)
        parts.extend(user.campus_experience)
        return " ".join(p for p in parts if p).lower()

    def _skill_match_score(self, user_skills: list[str], dept: Department) -> tuple[float, list[str]]:
        expanded = self._expand_skills(user_skills)
        required_lower = {s.lower() for s in dept.required_skills}
        preferred_lower = {s.lower() for s in dept.preferred_skills}

        matched_required = expanded & required_lower
        matched_preferred = expanded & preferred_lower

        required_ratio = len(matched_required) / max(len(required_lower), 1)
        preferred_ratio = len(matched_preferred) / max(len(preferred_lower), 1)

        if required_ratio >= 0.5:
            required_score = 0.20 + (required_ratio - 0.5) * 0.20
        else:
            required_score = required_ratio * 0.40

        preferred_score = preferred_ratio * 0.15

        reasons = []
        if matched_required:
            reasons.append(f"匹配必备技能({len(matched_required)}/{len(required_lower)}): {', '.join(sorted(matched_required))}")
        if matched_preferred:
            reasons.append(f"匹配加分技能({len(matched_preferred)}/{len(preferred_lower)}): {', '.join(sorted(matched_preferred))}")

        return required_score + preferred_score, reasons

    def _keyword_match_score(self, user_text: str, dept: Department) -> tuple[float, list[str]]:
        matched = [kw for kw in dept.keywords if kw.lower() in user_text]
        ratio = len(matched) / max(len(dept.keywords), 1)
        score = ratio * 0.10
        reasons = []
        if matched:
            reasons.append(f"关键词匹配: {', '.join(matched)}")
        return score, reasons

    def _major_match_score(self, user: User, dept: Department) -> tuple[float, list[str]]:
        reasons = []
        all_user_majors: list[str] = [user.major or ""]
        for edu in user.education:
            all_user_majors.append(edu.major or "")

        best_ratio = 0.0
        best_major = ""
        for um in all_user_majors:
            uml = um.lower()
            if not uml:
                continue
            for rm in dept.required_majors:
                rml = rm.lower()
                if rml in uml or uml in rml:
                    best_ratio = 1.0
                    best_major = um
                    break
                common = sum(1 for c in uml if c in rml)
                ratio = common / max(len(uml), len(rml))
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_major = um

        if best_ratio >= 0.6:
            score = 0.08 + (best_ratio - 0.6) * 0.175
            reasons.append(f"专业 '{best_major}' 与部门需求匹配度较高")
        elif best_ratio >= 0.3:
            score = best_ratio * 0.133
            reasons.append(f"专业 '{best_major}' 与部门需求部分相关")
        else:
            score = 0.0

        return score, reasons

    def _degree_match_score(self, user: User, dept: Department) -> tuple[float, list[str]]:
        user_deg = (user.degree or "").lower()
        reasons = []
        if not user_deg:
            return 0.0, reasons

        user_level = -1
        for k, v in DEGREE_HIERARCHY.items():
            if k in user_deg:
                user_level = max(user_level, v)

        if user_level >= 2:
            reasons.append(f"高学历 '{user.degree}' 有加分优势")
            return 0.05 if user_level == 2 else 0.08, reasons
        if user_level >= 0:
            reasons.append(f"学历 '{user.degree}' 符合基本要求")
            return 0.03, reasons

        if dept.preferred_degrees and any(d.lower() in user_deg for d in dept.preferred_degrees):
            reasons.append(f"学历 '{user.degree}' 符合部门偏好")
            return 0.05, reasons

        return 0.0, reasons

    def _work_experience_score(self, user: User, dept: Department) -> tuple[float, list[str]]:
        if not user.work_experience or not dept.position_keywords:
            return 0.0, []

        matched_count = 0
        matched_details: list[str] = []
        for w in user.work_experience:
            pos_text = f"{(w.position or '')} {(w.description or '')} {(w.company or '')}".lower()
            hits = [kw for kw in dept.position_keywords if kw.lower() in pos_text]
            if hits:
                matched_count += 1
                matched_details.append(f"{w.position or '未知职位'}@{w.company or '未知公司'}")

        if not user.work_experience:
            return 0.0, []

        ratio = matched_count / len(user.work_experience)
        score = min(ratio * 0.25, 0.15)
        reasons = []
        if matched_details:
            reasons.append(f"相关工作经历({matched_count}/{len(user.work_experience)}): {'; '.join(matched_details)}")
        return score, reasons

    def _project_experience_score(self, user: User, dept: Department) -> tuple[float, list[str]]:
        if not user.project_experience or not dept.tech_keywords:
            return 0.0, []

        matched_count = 0
        matched_details: list[str] = []
        for p in user.project_experience:
            proj_text = f"{(p.name or '')} {(p.description or '')} {' '.join(p.technologies)}".lower()
            hits = [kw for kw in dept.tech_keywords if kw.lower() in proj_text]
            if hits:
                matched_count += 1
                matched_details.append(p.name or "未命名项目")

        if not user.project_experience:
            return 0.0, []

        ratio = matched_count / len(user.project_experience)
        score = min(ratio * 0.25, 0.12)
        reasons = []
        if matched_details:
            reasons.append(f"相关项目经历({matched_count}/{len(user.project_experience)}): {'; '.join(matched_details)}")
        return score, reasons

    def _certifications_score(self, user: User, dept: Department) -> tuple[float, list[str]]:
        if not user.certifications:
            return 0.0, []

        cert_text = " ".join(c.lower() for c in user.certifications)
        dept_text = " ".join(dept.keywords + dept.required_skills).lower()
        matched = [c for c in user.certifications if c.lower() in dept_text or any(kw.lower() in cert_text for kw in dept.keywords)]

        if matched:
            return 0.03, [f"相关证书: {', '.join(matched)}"]
        return 0.0, []

    def match(self, user: User) -> list[MatchResult]:
        user_text = self._collect_user_text(user)

        results: list[MatchResult] = []
        for dept in self.departments:
            reasons: list[str] = []
            total_score = 0.0

            s_score, s_reasons = self._skill_match_score(user.skills, dept)
            total_score += s_score
            reasons.extend(s_reasons)

            k_score, k_reasons = self._keyword_match_score(user_text, dept)
            total_score += k_score
            reasons.extend(k_reasons)

            m_score, m_reasons = self._major_match_score(user, dept)
            total_score += m_score
            reasons.extend(m_reasons)

            d_score, d_reasons = self._degree_match_score(user, dept)
            total_score += d_score
            reasons.extend(d_reasons)

            w_score, w_reasons = self._work_experience_score(user, dept)
            total_score += w_score
            reasons.extend(w_reasons)

            p_score, p_reasons = self._project_experience_score(user, dept)
            total_score += p_score
            reasons.extend(p_reasons)

            c_score, c_reasons = self._certifications_score(user, dept)
            total_score += c_score
            reasons.extend(c_reasons)

            results.append(MatchResult(
                department=dept,
                score=round(min(total_score, 1.0), 2),
                reasons=reasons if total_score > 0 else ["暂无显著匹配项"],
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
