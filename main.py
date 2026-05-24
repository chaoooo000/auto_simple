from __future__ import annotations

import os
import json
import uuid
import tempfile
import asyncio
import io
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, UploadFile, File, Body, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import aiofiles
import pandas as pd

from src.graph.workflow import build_resume_workflow
from src.recommendation.matcher import DepartmentMatcher
from src.batch.processor import BatchProcessor, ProcessResult
from src.db import init_db, save_batch_session, get_session_results, get_resume_detail, get_master_summary, get_master_stats, delete_master_record, clear_master, update_master_field, update_master_status, get_master_record, update_master_batch, get_interview_schedule, update_interview_time

load_dotenv()

app = FastAPI(title="简历智能解析系统")
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_DIR = Path(__file__).parent
_batch_storage: dict[str, list[ProcessResult]] = {}

@app.on_event("startup")
async def startup_event():
    await init_db()


async def _render(template_name: str, **kwargs) -> HTMLResponse:
    path = BASE_DIR / "templates" / template_name
    async with aiofiles.open(path, encoding="utf-8") as f:
        html = await f.read()
    for key, val in kwargs.items():
        html = html.replace("{{ " + key + " }}", str(val))
    return HTMLResponse(html)


def _process_single(file_path: str) -> dict:
    workflow = build_resume_workflow()
    matcher = DepartmentMatcher()
    state = workflow.invoke({
        "file_path": file_path,
        "raw_text": None,
        "user": None,
        "error": None,
        "status": "pending",
    })
    if state.get("error"):
        return {"error": state["error"]}
    user = state.get("user")
    recommendations = matcher.match(user)
    return {
        "user": user.model_dump() if user else None,
        "recommendations": [
            {"department": r.department.name, "score": r.score, "description": r.department.description, "reasons": r.reasons}
            for r in recommendations
        ],
        "raw_text": state.get("raw_text", ""),
    }


def _build_summary_rows(results: list[ProcessResult]) -> list[dict]:
    rows = []
    for r in results:
        if r.status == "error":
            rows.append({"file_name": r.file_name, "status": "error", "name": "-", "degree": "-", "major": "-", "department": "-", "match_score": "-", "error": r.error or ""})
            continue
        user = r.user
        top_dept = r.recommendations[0].department.name if r.recommendations else "-"
        top_score = f"{int(r.recommendations[0].score * 100)}%" if r.recommendations else "-"
        rows.append({"file_name": r.file_name, "status": "completed", "name": user.name or "-", "degree": user.degree or "-", "major": user.major or "-", "department": top_dept, "match_score": top_score, "error": ""})
    return rows


@app.get("/", response_class=HTMLResponse)
async def page_upload():
    return await _render("upload.html", active_upload="active", active_batch="", active_summary="")


@app.get("/batch", response_class=HTMLResponse)
async def page_batch():
    return await _render("batch.html", active_upload="", active_batch="active", active_summary="")


@app.get("/summary", response_class=HTMLResponse)
async def page_summary(sid: str = ""):
    rows = await get_master_summary()
    if not rows:
        return await _render("summary.html", table_html="", count="0",
                             active_upload="", active_batch="", active_summary="active",
                             empty_style="", table_style="display:none")

    table_html = _build_master_table_html(rows)
    count = len(rows)
    return await _render("summary.html", table_html=table_html, count=str(count),
                         active_upload="", active_batch="", active_summary="active",
                         empty_style="display:none", table_style="")


def _build_master_table_html(rows: list[dict]) -> str:
    head = '<table><thead><tr><th>#</th><th>姓名</th><th>学历</th><th>专业</th><th>毕业院校</th><th>推荐部门</th><th>匹配度</th><th>面试状态</th><th>面试时间</th><th>导入时间</th><th>操作</th></tr></thead><tbody>'
    parts = [head]
    for i, r in enumerate(rows):
        score = f"{int(r['match_score'] * 100)}%" if r.get("match_score") else "-"
        time_str = str(r.get("import_time", "-"))[:16]
        interview_time = r.get("interview_time") or "-"
        if interview_time != "-" and len(interview_time) >= 16:
            interview_time = interview_time[:16]
        status = r.get("interview_status") or "未面试"
        status_class = "status-tag success" if status == "已面试" else "status-tag error"
        parts.append(
            f'<tr>'
            f'<td>{i + 1}</td>'
            f'<td>{_esc_html(r.get("name") or "-")}</td>'
            f'<td>{_esc_html(r.get("degree") or "-")}</td>'
            f'<td>{_esc_html(r.get("major") or "-")}</td>'
            f'<td>{_esc_html(r.get("school") or "-")}</td>'
            f'<td>{_esc_html(r.get("top_department") or "-")}</td>'
            f'<td>{score}</td>'
            f'<td><span class="{status_class}">{status}</span></td>'
            f'<td>{interview_time}</td>'
            f'<td>{time_str}</td>'
            f'<td class="actions-cell">'
            f'<button class="btn-table btn-view" data-id="{r["id"]}"><span class="btn-spinner"></span><span class="btn-label">查看</span></button> '
            f'<button class="btn-table btn-edit" data-id="{r["id"]}"><span class="btn-spinner"></span><span class="btn-label">编辑</span></button> '
            f'<button class="btn-table btn-delete" data-id="{r["id"]}"><span class="btn-spinner"></span><span class="btn-label">删除</span></button>'
            f'</td>'
            f'</tr>'
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def _esc_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


@app.post("/api/parse")
async def api_parse(file: UploadFile = File(...)):
    suffix = Path(file.filename or "resume").suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = await asyncio.to_thread(_process_single, tmp_path)
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.post("/api/batch")
async def api_batch(files: list[UploadFile] = File(...)):
    tmp_paths: list[str] = []
    file_names_list: list[str] = []
    for f in files:
        suffix = Path(f.filename or "resume").suffix.lower()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        content = await f.read()
        tmp.write(content)
        tmp_paths.append(tmp.name)
        file_names_list.append(f.filename or "unknown")
    try:
        processor = BatchProcessor(max_workers=min(4, len(files)))
        results = await processor.process_files(tmp_paths)
        sid = uuid.uuid4().hex[:12]
        _batch_storage[sid] = results
        asyncio.create_task(save_batch_session(sid, results, file_names_list))
        summary_rows = _build_summary_rows(results)
        return {"sid": sid, "summary_rows": summary_rows}
    finally:
        for tp in tmp_paths:
            try:
                os.unlink(tp)
            except OSError:
                pass


@app.get("/api/detail/{sid}/{index}")
async def api_detail(sid: str, index: int):
    results = _batch_storage.get(sid, [])
    if results:
        if index < 0 or index >= len(results):
            return {"error": "索引越界"}
        r = results[index]
        if r.status == "error":
            return {"error": r.error}
        return {
            "user": r.user.model_dump(),
            "recommendations": [
                {"department": m.department.name, "score": m.score, "description": m.department.description, "reasons": m.reasons}
                for m in r.recommendations
            ],
        }
    db_result = await get_resume_detail(sid, index)
    if db_result is None:
        return {"error": "数据不存在"}
    return db_result


async def _load_results_from_db(sid: str) -> list[ProcessResult]:
    from src.models.user import User

    db_rows = await get_session_results(sid)
    if not db_rows:
        return []
    results: list[ProcessResult] = []
    for i, dr in enumerate(db_rows):
        db_detail = await get_resume_detail(sid, i)
        if db_detail:
            user = User(**db_detail["user"])
            results.append(ProcessResult(
                file_name=dr.get("file_name", "unknown"),
                file_path="",
                user=user,
                recommendations=[],
                status="completed",
            ))
    return results


def _attachment_header(filename_ascii: str, filename_utf8: str) -> dict:
    encoded = quote(filename_utf8)
    return {
        "Content-Disposition": (
            f"attachment; filename=\"{filename_ascii}\"; "
            f"filename*=UTF-8''{encoded}"
        ),
    }


@app.get("/api/export/excel")
async def api_export_excel(sid: str = ""):
    bp = BatchProcessor()
    bp.results = _batch_storage.get(sid, [])
    if not bp.results:
        bp.results = await _load_results_from_db(sid)
    data = bp.export_excel()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=_attachment_header("resume_summary.xlsx", "简历汇总.xlsx"),
    )


@app.get("/api/export/csv")
async def api_export_csv(sid: str = ""):
    bp = BatchProcessor()
    bp.results = _batch_storage.get(sid, [])
    if not bp.results:
        bp.results = await _load_results_from_db(sid)
    data = bp.export_csv()
    return StreamingResponse(
        io.StringIO(data),
        media_type="text/csv",
        headers=_attachment_header("resume_summary.csv", "简历汇总.csv"),
    )


@app.get("/api/master")
async def api_master_list():
    rows = await get_master_summary()
    return {"total": len(rows), "rows": rows}


@app.get("/api/master/stats")
async def api_master_stats():
    return await get_master_stats()


@app.get("/api/master/detail/{record_id}")
async def api_master_detail(record_id: int):
    rows = await get_master_summary()
    for r in rows:
        if r["id"] == record_id:
            return {
                "user": r,
                "recommendations": json.loads(r.get("recommend_details") or "[]"),
            }
    return {"error": "记录不存在"}


@app.delete("/api/master/{record_id}")
async def api_master_delete(record_id: int):
    ok = await delete_master_record(record_id)
    return {"success": ok, "message": f"记录 #{record_id} 已{'删除' if ok else '不存在'}"}


@app.put("/api/master/{record_id}/field")
async def api_master_edit_field(record_id: int, field: str = "", value: str = ""):
    if not field or field not in {"name", "degree", "major", "school", "phone", "email", "gender", "age", "graduation_year", "address"}:
        return {"success": False, "message": "不允许的字段"}
    ok = await update_master_field(record_id, field, value)
    return {"success": ok, "message": f"字段 {field} 已{'更新' if ok else '更新失败'}"}


@app.patch("/api/master/{record_id}/status")
async def api_master_toggle_status(record_id: int, status: str = ""):
    if status not in ("已面试", "未面试"):
        return {"success": False, "message": "无效状态值，应为 已面试 或 未面试"}
    ok = await update_master_status(record_id, status)
    return {"success": ok, "message": f"面试状态已更新为「{status}」"}


@app.get("/api/master/filter")
async def api_master_filtered(status: str = ""):
    rows = await get_master_summary(status_filter=status)
    return {"total": len(rows), "rows": rows}


@app.put("/api/master/{record_id}/update")
async def api_master_batch_update(record_id: int, request: Request):
    payload = await request.json()
    ok = await update_master_batch(record_id, payload)
    return {"success": ok, "message": f"记录 #{record_id} 已{'更新' if ok else '更新失败'}"}


@app.get("/api/interview/schedule")
async def api_interview_schedule():
    rows = await get_interview_schedule()
    return {"total": len(rows), "events": rows}


@app.put("/api/interview/{record_id}/time")
async def api_interview_set_time(record_id: int, interview_time: str = Body(..., embed=True)):
    ok = await update_interview_time(record_id, interview_time)
    return {"success": ok, "message": "面试时间已更新" if ok else "更新失败"}


@app.delete("/api/interview/{record_id}/time")
async def api_interview_clear_time(record_id: int):
    ok = await update_interview_time(record_id, None)
    return {"success": ok, "message": "面试时间已清除" if ok else "操作失败"}


@app.get("/api/export/master/excel")
async def api_export_master_excel(status: str = ""):
    rows = await get_master_summary(status_filter=status)
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    output = io.BytesIO()
    exclude_cols = {"id", "raw_text", "file_name", "recommend_details"}
    display_cols = [c for c in df.columns if c not in exclude_cols]
    col_labels = {
        "name": "姓名", "gender": "性别", "age": "年龄",
        "phone": "手机", "email": "邮箱", "address": "地址",
        "degree": "学历", "major": "专业", "school": "毕业院校",
        "graduation_year": "毕业年份", "skills": "专业技能",
        "work_history": "工作经历", "project_history": "项目经历",
        "campus_experience": "校园经历", "certifications": "证书资质",
        "languages": "语言能力", "top_department": "推荐部门",
        "match_score": "匹配度", "interview_status": "面试状态",
        "interview_time": "面试时间", "import_time": "导入时间",
        "updated_at": "更新时间",
    }
    if display_cols:
        out_df = df[display_cols].rename(columns=col_labels)
        out_df.to_excel(output, index=False, sheet_name="简历汇总表")
    else:
        df.to_excel(output, index=False, sheet_name="简历汇总表")
    suffix = "_interviewed" if status == "已面试" else ("_not_interviewed" if status == "未面试" else "")
    suffix_cn = "_已面试" if status == "已面试" else ("_未面试" if status == "未面试" else "")
    filename_ascii = f"master_summary{suffix}.xlsx"
    filename_utf8 = f"简历汇总表{suffix_cn}.xlsx"
    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=_attachment_header(filename_ascii, filename_utf8),
    )


@app.get("/api/export/master/csv")
async def api_export_master_csv(status: str = ""):
    rows = await get_master_summary(status_filter=status)
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    exclude_cols = {"id", "raw_text", "file_name", "recommend_details"}
    display_cols = [c for c in df.columns if c not in exclude_cols]
    col_labels = {
        "name": "姓名", "gender": "性别", "age": "年龄",
        "phone": "手机", "email": "邮箱", "address": "地址",
        "degree": "学历", "major": "专业", "school": "毕业院校",
        "graduation_year": "毕业年份", "skills": "专业技能",
        "work_history": "工作经历", "project_history": "项目经历",
        "campus_experience": "校园经历", "certifications": "证书资质",
        "languages": "语言能力", "top_department": "推荐部门",
        "match_score": "匹配度", "interview_status": "面试状态",
        "interview_time": "面试时间", "import_time": "导入时间",
        "updated_at": "更新时间",
    }
    out_df = df[display_cols].rename(columns=col_labels) if display_cols else df
    csv_data = out_df.to_csv(index=False)
    suffix = "_interviewed" if status == "已面试" else ("_not_interviewed" if status == "未面试" else "")
    suffix_cn = "_已面试" if status == "已面试" else ("_未面试" if status == "未面试" else "")
    filename_ascii = f"master_summary{suffix}.csv"
    filename_utf8 = f"简历汇总表{suffix_cn}.csv"
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers=_attachment_header(filename_ascii, filename_utf8),
    )
