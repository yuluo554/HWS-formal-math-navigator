"""报告生成器：人读（HTML）+ 机读（JSON）双轨"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import date

from .orchestrator import OrchestrationResult


@dataclass
class ReportConfig:
    """报告配置"""
    include_retrieval: bool = True
    include_depgraph: bool = True
    include_kernel: bool = True
    human_readable: bool = True
    machine_readable: bool = True


class ReportGenerator:
    """报告生成器

    人读轨道：HTML（0 外链，断网可开）
    机读轨道：JSON（逐字节可复现）
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """
        初始化报告生成器

        Args:
            config: 报告配置
        """
        self.config = config or ReportConfig()

    def generate(self, result: OrchestrationResult, output_dir: Path) -> Dict[str, Path]:
        """
        生成报告

        Args:
            result: 编排结果
            output_dir: 输出目录

        Returns:
            生成的报告文件路径映射
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated = {}

        if self.config.human_readable:
            html_path = output_dir / "report.html"
            self._generate_html(result, html_path)
            generated["html"] = html_path

        if self.config.machine_readable:
            json_path = output_dir / "report.json"
            self._generate_json(result, json_path)
            generated["json"] = json_path

        return generated

    def _generate_html(self, result: OrchestrationResult, output_path: Path):
        """生成 HTML 报告（0 外链）

        K8 口径：HTML 0 外链
        """
        # 状态映射
        status_colors = {
            "PASS_NO_SORRY": "#2e7d32",
            "PASS_WITH_SORRY": "#f57c00",
            "FAIL": "#d32f2f",
            "SKIPPED": "#757575",
            "INDEX_GAP": "#7b1fa2",
        }

        status_labels = {
            "PASS_NO_SORRY": "✅ 验证通过（无 sorry）",
            "PASS_WITH_SORRY": "⚠️ 验证通过（含 sorry）",
            "FAIL": "❌ 验证失败",
            "SKIPPED": "⏭️ 跳过（Lean 不可用）",
            "INDEX_GAP": "⚠️ 索引缺口",
        }

        # 检索结果 HTML
        retrieval_html = ""
        if self.config.include_retrieval and result.retrieval_results:
            for r in result.retrieval_results[:10]:
                retrieval_html += f'''
                <div class="result-item">
                    <div class="result-name">{self._escape_html(r['theorem'])}</div>
                    <div class="result-meta">
                        <span class="module">{self._escape_html(r['module'])}</span>
                        <span class="score">分数: {r['score']:.4f}</span>
                        <span class="fields">匹配: {', '.join(r['match_fields'])}</span>
                    </div>
                    <div class="result-sig">{self._escape_html(r.get('signature', ''))}</div>
                </div>'''
        else:
            retrieval_html = '<div class="empty">无检索结果</div>'

        # 骨架代码 HTML
        skeleton_html = ""
        if result.skeleton:
            skeleton_html = f'<pre><code>{self._escape_html(result.skeleton)}</code></pre>'
        else:
            skeleton_html = '<div class="empty">未生成骨架</div>'

        # 内核验证 HTML
        kernel_html = ""
        if self.config.include_kernel and result.kernel_verification:
            kv = result.kernel_verification
            status = kv.get("status", "N/A")
            has_sorry = kv.get("has_sorry", False)
            sorry_count = kv.get("sorry_count", 0)
            errors = kv.get("errors", [])

            kernel_html = f'''
            <div class="kernel-status" style="color: {status_colors.get(status, '#333')}">
                {status_labels.get(status, status)}
            </div>
            <div class="kernel-details">
                <div>含 sorry: {'是' if has_sorry else '否'}</div>
                <div>sorry 数量: {sorry_count}</div>
            </div>'''

            if errors:
                kernel_html += '<div class="errors"><strong>错误:</strong><ul>'
                for e in errors:
                    kernel_html += f'<li>{self._escape_html(e)}</li>'
                kernel_html += '</ul></div>'
        else:
            kernel_html = '<div class="empty">未执行内核验证</div>'

        # 依赖图 HTML
        depgraph_html = ""
        if self.config.include_depgraph and result.depgraph_result:
            dg = result.depgraph_result
            depgraph_html = f'''
            <div class="depgraph-stats">
                <div>节点数: {len(dg.get('nodes', []))}</div>
                <div>边数: {len(dg.get('edges', []))}</div>
                <div class="broken">断链: {len(dg.get('broken_refs', []))}</div>
                <div class="gap">Index Gaps: {len(dg.get('index_gaps', []))}</div>
            </div>'''

            if dg.get('broken_refs'):
                depgraph_html += '<div class="broken-list"><strong>断链:</strong><ul>'
                for ref in dg['broken_refs'][:10]:
                    depgraph_html += f'<li>{self._escape_html(ref)}</li>'
                depgraph_html += '</ul></div>'

            if dg.get('index_gaps'):
                depgraph_html += '<div class="gap-list"><strong>Index Gaps:</strong><ul>'
                for gap in dg['index_gaps'][:10]:
                    depgraph_html += f'<li>{self._escape_html(gap)}</li>'
                depgraph_html += '</ul></div>'
        else:
            depgraph_html = '<div class="empty">未分析依赖图</div>'

        # 警告和错误
        warnings_html = ""
        if result.warnings:
            warnings_html = '<div class="warnings"><strong>警告:</strong><ul>'
            for w in result.warnings:
                warnings_html += f'<li>{self._escape_html(w)}</li>'
            warnings_html += '</ul></div>'

        errors_html = ""
        if result.errors:
            errors_html = '<div class="errors"><strong>错误:</strong><ul>'
            for e in result.errors:
                errors_html += f'<li>{self._escape_html(e)}</li>'
            errors_html += '</ul></div>'

        # 生成日期
        gen_date = result.generation_date or date.today().isoformat()

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>形式化数学导航报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .result-item {{
            border: 1px solid #eee;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .result-name {{ font-weight: bold; color: #1976d2; }}
        .result-meta {{ font-size: 14px; color: #666; margin: 5px 0; }}
        .result-meta span {{ margin-right: 15px; }}
        .result-sig {{ font-family: monospace; font-size: 13px; color: #333; background: #f9f9f9; padding: 5px; border-radius: 3px; }}
        .module {{ color: #7b1fa2; }}
        .score {{ color: #2e7d32; }}
        .fields {{ color: #f57c00; }}
        pre {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }}
        code {{ font-family: 'JetBrains Mono', 'Consolas', monospace; }}
        .kernel-status {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
        .kernel-details {{ color: #666; }}
        .depgraph-stats {{ display: flex; gap: 20px; margin: 10px 0; }}
        .depgraph-stats div {{ padding: 5px 10px; background: #f5f5f5; border-radius: 4px; }}
        .broken {{ color: #d32f2f; font-weight: bold; }}
        .gap {{ color: #f57c00; font-weight: bold; }}
        .warnings {{ background: #fff3e0; padding: 10px; border-radius: 4px; border-left: 4px solid #f57c00; }}
        .errors {{ background: #ffebee; padding: 10px; border-radius: 4px; border-left: 4px solid #d32f2f; }}
        .empty {{ color: #999; font-style: italic; }}
        .meta {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 12px;
        }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 3px 0; }}
    </style>
</head>
<body>
    <h1>形式化数学导航报告</h1>

    <div class="meta">
        生成日期: {gen_date} | 命题: {self._escape_html(result.proposition)}
    </div>

    <div class="section">
        <h2>检索结果</h2>
        {retrieval_html}
    </div>

    <div class="section">
        <h2>证明骨架</h2>
        {skeleton_html}
    </div>

    <div class="section">
        <h2>内核验证</h2>
        {kernel_html}
    </div>

    <div class="section">
        <h2>依赖图分析</h2>
        {depgraph_html}
    </div>

    {warnings_html}
    {errors_html}

    <div class="meta">
        本报告由 HWS-formal-math-navigator 自动生成 | 判定为辅助参考，以浏览器实际打开为准
    </div>
</body>
</html>'''

        output_path.write_text(html, encoding="utf-8")

    def _generate_json(self, result: OrchestrationResult, output_path: Path):
        """生成 JSON 报告（逐字节可复现）

        K11 口径：确定性写盘，无时间戳
        """
        data = {
            "generation_date": result.generation_date or date.today().isoformat(),
            "proposition": result.proposition,
            "status": result.status,
            "skeleton": result.skeleton,
            "retrieval_results": result.retrieval_results,
            "kernel_verification": result.kernel_verification,
            "depgraph_result": result.depgraph_result,
            "errors": result.errors,
            "warnings": result.warnings,
        }

        # 确定性输出：排序 keys，确保逐字节一致
        json_str = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
        output_path.write_text(json_str, encoding="utf-8")

    @staticmethod
    def _escape_html(text: str) -> str:
        """HTML 转义"""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;")
        )
