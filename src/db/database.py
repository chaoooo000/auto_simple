import json
import aiosqlite
from pathlib import Path

from src.models.user import User
from src.recommendation.matcher import MatchResult

DB_PATH = Path(__file__).parent.parent.parent / "data" / "resumes.db"


def _ensure_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


async def init_db():
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS batch_sessions (
                sid TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                file_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES batch_sessions(sid),
                file_name TEXT NOT NULL,
                raw_text TEXT,
                name TEXT, gender TEXT, age TEXT,
                phone TEXT, email TEXT, address TEXT,
                degree TEXT, major TEXT, school TEXT, graduation_year TEXT,
                skills TEXT, certifications TEXT, languages TEXT,
                campus_experience TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS educations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                school TEXT, degree TEXT, major TEXT,
                start_date TEXT, end_date TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS work_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                company TEXT, position TEXT,
                start_date TEXT, end_date TEXT,
                description TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS project_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                name TEXT, role TEXT, description TEXT,
                technologies TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                department TEXT NOT NULL,
                score REAL NOT NULL,
                description TEXT,
                reasons TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS master_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, gender TEXT, age TEXT,
                phone TEXT, email TEXT, address TEXT,
                degree TEXT, major TEXT, school TEXT, graduation_year TEXT,
                skills TEXT,
                work_history TEXT,
                project_history TEXT,
                campus_experience TEXT,
                certifications TEXT,
                languages TEXT,
                top_department TEXT,
                match_score REAL,
                recommend_details TEXT,
                file_name TEXT,
                raw_text TEXT,
                interview_status TEXT NOT NULL DEFAULT '未面试',
                import_time TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        try:
            await db.execute("ALTER TABLE master_summary ADD COLUMN interview_status TEXT NOT NULL DEFAULT '未面试'")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE master_summary ADD COLUMN interview_time TEXT")
        except Exception:
            pass
        await db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_master_dedup
            ON master_summary(name, phone, email)
            WHERE name IS NOT NULL AND (phone IS NOT NULL OR email IS NOT NULL)
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_resumes_session ON resumes(session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_resume ON recommendations(resume_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_master_name ON master_summary(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_master_dept ON master_summary(top_department)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_master_status ON master_summary(interview_status)")
        await db.commit()


async def save_batch_session(sid: str, results: list, file_names: list[str]) -> None:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute("INSERT OR REPLACE INTO batch_sessions (sid, file_count) VALUES (?, ?)", (sid, len(file_names)))
        for i, pr in enumerate(results):
            user = pr.user
            recs = pr.recommendations
            file_name = file_names[i] if i < len(file_names) else pr.file_name

            cursor = await db.execute(
                """INSERT INTO resumes (session_id, file_name, raw_text, name, gender, age, phone, email, address,
                   degree, major, school, graduation_year, skills, certifications, languages, campus_experience)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sid, file_name, user.raw_text,
                    user.name, user.gender, user.age,
                    user.phone, user.email, user.address,
                    user.degree, user.major, user.school, user.graduation_year,
                    json.dumps(user.skills, ensure_ascii=False),
                    json.dumps(user.certifications, ensure_ascii=False),
                    json.dumps(user.languages, ensure_ascii=False),
                    json.dumps(user.campus_experience, ensure_ascii=False),
                ),
            )
            resume_id = cursor.lastrowid

            for edu in user.education:
                await db.execute(
                    "INSERT INTO educations (resume_id, school, degree, major, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (resume_id, edu.school, edu.degree, edu.major, edu.start_date, edu.end_date),
                )
            for w in user.work_experience:
                await db.execute(
                    "INSERT INTO work_experiences (resume_id, company, position, start_date, end_date, description) VALUES (?, ?, ?, ?, ?, ?)",
                    (resume_id, w.company, w.position, w.start_date, w.end_date, w.description),
                )
            for p in user.project_experience:
                await db.execute(
                    "INSERT INTO project_experiences (resume_id, name, role, description, technologies) VALUES (?, ?, ?, ?, ?)",
                    (resume_id, p.name, p.role, p.description, json.dumps(p.technologies, ensure_ascii=False)),
                )
            for r in recs:
                await db.execute(
                    "INSERT INTO recommendations (resume_id, department, score, description, reasons) VALUES (?, ?, ?, ?, ?)",
                    (resume_id, r.department.name, r.score, r.department.description, json.dumps(r.reasons, ensure_ascii=False)),
                )

            await _upsert_master_in_tx(db, user, recs, file_name)

        await db.commit()


async def _upsert_master_in_tx(db: aiosqlite.Connection, user: User, recs: list[MatchResult], file_name: str) -> dict:
    name = user.name
    phone = user.phone
    email = user.email

    dedup_key = None
    dedup_value = None
    if name and phone:
        dedup_key = "name = ? AND phone = ?"
        dedup_value = (name, phone)
    elif name and email:
        dedup_key = "name = ? AND email = ?"
        dedup_value = (name, email)

    top_rec = recs[0] if recs else None

    skills_text = "、".join(user.skills) if user.skills else ""
    work_history = "；".join(
        f"{w.position or ''}@{w.company or ''}"
        for w in (user.work_experience or [])
        if w.position or w.company
    )
    project_history = "；".join(
        f"{p.name or ''}({p.role or ''})"
        for p in (user.project_experience or [])
        if p.name
    )
    campus_text = "；".join(user.campus_experience) if user.campus_experience else ""
    certs_text = "、".join(user.certifications) if user.certifications else ""
    langs_text = "、".join(user.languages) if user.languages else ""

    recommend_json = json.dumps(
        [{"department": r.department.name, "score": r.score, "reasons": r.reasons} for r in recs],
        ensure_ascii=False,
    ) if recs else ""

    action = "inserted"
    if dedup_key and dedup_value:
        rows = await db.execute_fetchall(
            f"SELECT id FROM master_summary WHERE {dedup_key}", dedup_value,
        )
        if rows:
            await db.execute(
                """UPDATE master_summary SET
                    gender = ?, age = ?, address = ?, degree = ?, major = ?, school = ?,
                    graduation_year = ?, skills = ?, work_history = ?, project_history = ?,
                    campus_experience = ?, certifications = ?, languages = ?,
                    top_department = ?, match_score = ?, recommend_details = ?,
                    file_name = ?, raw_text = ?, updated_at = datetime('now','localtime')
                   WHERE id = ?""",
                (
                    user.gender, user.age, user.address,
                    user.degree, user.major, user.school, user.graduation_year,
                    skills_text, work_history, project_history,
                    campus_text, certs_text, langs_text,
                    top_rec.department.name if top_rec else None,
                    top_rec.score if top_rec else None,
                    recommend_json,
                    file_name, user.raw_text, rows[0][0],
                ),
            )
            action = "updated"
            return {"action": action, "name": name, "dedup": True}

    await db.execute(
        """INSERT INTO master_summary
           (name, gender, age, phone, email, address, degree, major, school, graduation_year,
            skills, work_history, project_history, campus_experience, certifications, languages,
            top_department, match_score, recommend_details, file_name, raw_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user.name, user.gender, user.age, user.phone, user.email, user.address,
            user.degree, user.major, user.school, user.graduation_year,
            skills_text, work_history, project_history,
            campus_text, certs_text, langs_text,
            top_rec.department.name if top_rec else None,
            top_rec.score if top_rec else None,
            recommend_json,
            file_name, user.raw_text,
        ),
    )
    return {"action": action, "name": name, "dedup": False}


async def get_session_results(sid: str) -> list[dict] | None:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, file_name, name, degree, major, skills, session_id FROM resumes WHERE session_id = ? ORDER BY id",
            (sid,),
        )
        if not rows:
            return None
        results = []
        for row in rows:
            recs = await db.execute_fetchall(
                "SELECT department, score, description, reasons FROM recommendations WHERE resume_id = ? ORDER BY score DESC",
                (row["id"],),
            )
            top_rec = recs[0] if recs else None
            results.append({
                "file_name": row["file_name"],
                "status": "completed",
                "name": row["name"] or "-",
                "degree": row["degree"] or "-",
                "major": row["major"] or "-",
                "department": top_rec["department"] if top_rec else "-",
                "match_score": f"{int(top_rec['score'] * 100)}%" if top_rec else "-",
                "error": "",
            })
        return results


async def get_resume_detail(sid: str, index: int) -> dict | None:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, file_name, raw_text, name, gender, age, phone, email, address, degree, major, school, graduation_year, skills, certifications, languages, campus_experience FROM resumes WHERE session_id = ? ORDER BY id",
            (sid,),
        )
        if index < 0 or index >= len(rows):
            return None
        row = rows[index]

        educations = await db.execute_fetchall("SELECT school, degree, major, start_date, end_date FROM educations WHERE resume_id = ?", (row["id"],))
        works = await db.execute_fetchall("SELECT company, position, start_date, end_date, description FROM work_experiences WHERE resume_id = ?", (row["id"],))
        projects = await db.execute_fetchall("SELECT name, role, description, technologies FROM project_experiences WHERE resume_id = ?", (row["id"],))
        recs = await db.execute_fetchall("SELECT department, score, description, reasons FROM recommendations WHERE resume_id = ? ORDER BY score DESC", (row["id"],))

        user = {
            "name": row["name"], "gender": row["gender"], "age": row["age"],
            "phone": row["phone"], "email": row["email"], "address": row["address"],
            "degree": row["degree"], "major": row["major"], "school": row["school"],
            "graduation_year": row["graduation_year"],
            "education": [dict(e) for e in educations],
            "skills": json.loads(row["skills"] or "[]"),
            "work_experience": [dict(w) for w in works],
            "project_experience": [
                {**dict(p), "technologies": json.loads(p["technologies"] or "[]")}
                for p in projects
            ],
            "campus_experience": json.loads(row["campus_experience"] or "[]"),
            "certifications": json.loads(row["certifications"] or "[]"),
            "languages": json.loads(row["languages"] or "[]"),
            "raw_text": row["raw_text"],
        }
        recommendations = [
            {"department": r["department"], "score": r["score"], "description": r["description"], "reasons": json.loads(r["reasons"] or "[]")}
            for r in recs
        ]
        return {"user": user, "recommendations": recommendations}


async def get_master_summary(order_by: str = "import_time", desc: bool = True, status_filter: str = "") -> list[dict]:
    _ensure_dir()
    allowed = {"import_time", "name", "degree", "match_score", "top_department"}
    col = order_by if order_by in allowed else "import_time"
    direction = "DESC" if desc else "ASC"
    where = ""
    params: list = []
    if status_filter in ("已面试", "未面试"):
        where = "WHERE interview_status = ?"
        params.append(status_filter)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            f"SELECT id, name, gender, age, phone, email, address, degree, major, school, graduation_year, "
            f"skills, work_history, project_history, campus_experience, certifications, languages, "
            f"top_department, match_score, recommend_details, file_name, interview_status, interview_time, import_time, updated_at "
            f"FROM master_summary {where} ORDER BY {col} {direction}",
            params,
        )
        return [dict(r) for r in rows]


async def update_master_field(record_id: int, field: str, value: str) -> bool:
    _ensure_dir()
    allowed_fields = {"name", "degree", "major", "school", "phone", "email", "gender", "age", "graduation_year", "address"}
    if field not in allowed_fields:
        return False
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cursor = await db.execute(
            f"UPDATE master_summary SET {field} = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (value, record_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_master_status(record_id: int, status: str) -> bool:
    _ensure_dir()
    if status not in ("已面试", "未面试"):
        return False
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cursor = await db.execute(
            "UPDATE master_summary SET interview_status = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (status, record_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_master_record(record_id: int) -> dict | None:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM master_summary WHERE id = ?",
            (record_id,),
        )
        return dict(rows[0]) if rows else None


async def get_master_stats() -> dict:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        total = await db.execute_fetchall("SELECT COUNT(*) as c FROM master_summary")
        depts = await db.execute_fetchall(
            "SELECT top_department, COUNT(*) as cnt FROM master_summary WHERE top_department IS NOT NULL GROUP BY top_department ORDER BY cnt DESC"
        )
        degrees = await db.execute_fetchall(
            "SELECT degree, COUNT(*) as cnt FROM master_summary WHERE degree IS NOT NULL GROUP BY degree ORDER BY cnt DESC"
        )
        interviewed = await db.execute_fetchall("SELECT COUNT(*) FROM master_summary WHERE interview_status = '已面试'")
        not_interviewed = await db.execute_fetchall("SELECT COUNT(*) FROM master_summary WHERE interview_status = '未面试'")
        return {
            "total": total[0][0] if total else 0,
            "by_department": [{"dept": d[0], "count": d[1]} for d in depts],
            "by_degree": [{"degree": d[0], "count": d[1]} for d in degrees],
            "interviewed": interviewed[0][0] if interviewed else 0,
            "not_interviewed": not_interviewed[0][0] if not_interviewed else 0,
        }


async def delete_master_record(record_id: int) -> bool:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cursor = await db.execute("DELETE FROM master_summary WHERE id = ?", (record_id,))
        await db.commit()
        return cursor.rowcount > 0


async def update_master_batch(record_id: int, fields: dict) -> bool:
    _ensure_dir()
    allowed = {"name", "degree", "major", "school", "phone", "email", "gender", "age", "graduation_year", "address", "interview_status", "interview_time"}
    updates = {}
    for k, v in fields.items():
        if k in allowed and v is not None:
            updates[k] = v
    if not updates:
        return False
    set_clauses = [f"{k} = ?" for k in updates]
    set_clauses.append("updated_at = datetime('now','localtime')")
    values = list(updates.values())
    values.append(record_id)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cursor = await db.execute(
            f"UPDATE master_summary SET {', '.join(set_clauses)} WHERE id = ?",
            values,
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_interview_schedule() -> list[dict]:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, name, interview_time, interview_status, top_department FROM master_summary WHERE interview_time IS NOT NULL ORDER BY interview_time"
        )
        return [dict(r) for r in rows]


async def update_interview_time(record_id: int, interview_time: str | None) -> bool:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cursor = await db.execute(
            "UPDATE master_summary SET interview_time = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (interview_time, record_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def clear_master() -> int:
    _ensure_dir()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cursor = await db.execute("DELETE FROM master_summary")
        await db.commit()
        return cursor.rowcount
