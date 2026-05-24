import asyncio
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.graph.workflow import build_resume_workflow
from src.models.user import User
from src.recommendation.matcher import DepartmentMatcher, MatchResult


@dataclass
class ProcessResult:
    file_name: str
    file_path: str
    user: User
    recommendations: list[MatchResult] = field(default_factory=list)
    error: str | None = None
    status: str = "pending"


def _process_single_file(file_path: str) -> ProcessResult:
    workflow = build_resume_workflow()
    matcher = DepartmentMatcher()

    try:
        initial_state = {
            "file_path": file_path,
            "raw_text": None,
            "user": None,
            "error": None,
            "status": "pending",
        }
        result = workflow.invoke(initial_state)

        if result.get("error"):
            return ProcessResult(
                file_name=Path(file_path).name,
                file_path=file_path,
                user=User(),
                error=result["error"],
                status="error",
            )

        user = result.get("user", User())
        recommendations = matcher.match(user)

        return ProcessResult(
            file_name=Path(file_path).name,
            file_path=file_path,
            user=user,
            recommendations=recommendations,
            status="completed",
        )
    except Exception as e:
        return ProcessResult(
            file_name=Path(file_path).name,
            file_path=file_path,
            user=User(),
            error=str(e),
            status="error",
        )


class BatchProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results: list[ProcessResult] = []

    async def process_files(self, file_paths: list[str]) -> list[ProcessResult]:
        self.results = []

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(_process_single_file, fp): fp
                for fp in file_paths
            }

            completed_count = 0
            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
                completed_count += 1

        self.results.sort(key=lambda r: r.file_name)
        return self.results

    def process_files_sync(self, file_paths: list[str]) -> list[ProcessResult]:
        return asyncio.run(self.process_files(file_paths))

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for r in self.results:
            if r.status == "error" or not r.user:
                rows.append({
                    "文件名": r.file_name,
                    "状态": "处理失败",
                    "错误信息": r.error or "未知错误",
                })
                continue

            summary = r.user.to_summary_dict()
            top_dept = r.recommendations[0].department.name if r.recommendations else ""
            summary["文件名"] = r.file_name
            summary["状态"] = "已完成"
            summary["推荐部门"] = top_dept
            rows.append(summary)

        return pd.DataFrame(rows)

    def export_excel(self) -> bytes:
        df = self.to_dataframe()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="简历汇总")
        return output.getvalue()

    def export_csv(self) -> str:
        df = self.to_dataframe()
        return df.to_csv(index=False)
