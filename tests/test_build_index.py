"""索引构建器测试"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.build_index import (
    build_index,
    build_index_with_commit,
    scan_lean_files,
    parse_theorem_declaration,
    extract_dependencies,
    _lean_file_to_module,
    _compute_domain_coverage
)


class TestScanLeanFiles:
    """扫描 .lean 文件测试"""
    
    def test_scan_lean_files_recursive(self):
        """递归扫描 .lean 文件"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 创建测试文件结构
            (tmp_path / "Mathlib").mkdir()
            (tmp_path / "Mathlib" / "Algebra").mkdir()
            (tmp_path / "Mathlib" / "Algebra" / "Group").mkdir()
            
            # 创建 .lean 文件
            (tmp_path / "Mathlib" / "Algebra" / "Group" / "Defs.lean").write_text(
                "theorem test : True := by sorry"
            )
            (tmp_path / "Mathlib" / "Algebra" / "Ring").mkdir()
            (tmp_path / "Mathlib" / "Algebra" / "Ring" / "Defs.lean").write_text(
                "theorem test2 : True := by sorry"
            )
            
            lean_files = scan_lean_files(tmp_path)
            assert len(lean_files) == 2
            assert all(f.suffix == ".lean" for f in lean_files)
    
    def test_scan_lean_files_no_duplicates(self):
        """Windows 文件系统不区分大小写，不应有重复"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 创建测试文件
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            
            lean_files = scan_lean_files(tmp_path)
            # 应该只有 1 个文件，不是 2 个
            assert len(lean_files) == 1
    
    def test_scan_lean_files_filter_hidden(self):
        """过滤隐藏目录"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 创建 .git 目录
            (tmp_path / ".git").mkdir()
            (tmp_path / ".git" / "config").write_text("test")
            
            # 创建正常文件
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            
            lean_files = scan_lean_files(tmp_path)
            # 应该只找到正常文件
            assert len(lean_files) == 1


class TestLeanFileToModule:
    """模块路径转换测试"""
    
    def test_relative_to_mathlib4(self):
        """相对于 mathlib4 路径"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Mathlib" / "Algebra" / "Group" / "Defs.lean"
            lean_file.parent.mkdir(parents=True)
            lean_file.write_text("test")
            
            module = _lean_file_to_module(lean_file, tmp_path)
            assert module == "Mathlib.Algebra.Group.Defs"
    
    def test_with_src_subdirectory(self):
        """有 src 子目录"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            src_path = tmp_path / "src"
            src_path.mkdir()
            
            lean_file = src_path / "Mathlib" / "Algebra" / "Group" / "Defs.lean"
            lean_file.parent.mkdir(parents=True)
            lean_file.write_text("test")
            
            module = _lean_file_to_module(lean_file, tmp_path)
            assert module == "Mathlib.Algebra.Group.Defs"


class TestParseTheoremDeclaration:
    """定理声明解析测试"""
    
    def test_parse_single_theorem(self):
        """解析单个定理"""
        content = """
theorem add_assoc {α : Type u_1} [Add α] [AddSemigroup α] (a b c : α) :
    a + b + c = a + (b + c) := by
  sorry
"""
        theorems = parse_theorem_declaration(content, "Mathlib.Algebra.Group.Defs", [])
        
        assert len(theorems) == 1
        assert theorems[0]["name"] == "add_assoc"
        assert "signature" in theorems[0]
        assert "deps" in theorems[0]
    
    def test_parse_multiple_theorems(self):
        """解析多个定理"""
        content = """
theorem add_assoc : a + b + c = a + (b + c) := by sorry

theorem add_comm : a + b = b + a := by sorry

theorem add_zero : a + 0 = a := by sorry
"""
        theorems = parse_theorem_declaration(content, "Mathlib.Algebra.Group.Defs", [])
        
        assert len(theorems) == 3
        names = [t["name"] for t in theorems]
        assert "add_assoc" in names
        assert "add_comm" in names
        assert "add_zero" in names
    
    def test_parse_with_import_deps(self):
        """解析带依赖的定理"""
        content = """
import Mathlib.Init
import Mathlib.Algebra.Group.Defs

theorem add_assoc : a + b + c = a + (b + c) := by sorry
"""
        deps = extract_dependencies(content)
        theorems = parse_theorem_declaration(content, "Mathlib.Algebra.Group.Defs", deps)
        
        assert len(theorems) == 1
        assert "Mathlib.Init" in theorems[0]["deps"]
        assert "Mathlib.Algebra.Group.Defs" in theorems[0]["deps"]
    
    def test_parse_multiline_signature(self):
        """解析多行签名"""
        content = """
theorem choose_succ_succ (n k : ℕ) :
    Nat.choose (n + 1) (k + 1) = Nat.choose n k + Nat.choose n (k + 1) := by
  sorry
"""
        theorems = parse_theorem_declaration(content, "Mathlib.Combinatorics.Defs", [])
        
        assert len(theorems) == 1
        assert theorems[0]["name"] == "choose_succ_succ"
        # 签名应该包含完整内容
        assert "Nat.choose (n + 1) (k + 1)" in theorems[0]["signature"]


class TestExtractDependencies:
    """依赖提取测试"""
    
    def test_extract_single_import(self):
        """提取单个 import"""
        content = "import Mathlib.Init"
        deps = extract_dependencies(content)
        assert deps == ["Mathlib.Init"]
    
    def test_extract_multiple_imports(self):
        """提取多个 import"""
        content = """
import Mathlib.Init
import Mathlib.Algebra.Group.Defs
import Mathlib.Data.Nat.Init
"""
        deps = extract_dependencies(content)
        assert len(deps) == 3
        assert "Mathlib.Init" in deps
        assert "Mathlib.Algebra.Group.Defs" in deps
    
    def test_extract_import_on_same_line(self):
        """同一行多个 import"""
        content = "import Mathlib.Init Mathlib.Algebra.Group.Defs"
        deps = extract_dependencies(content)
        assert len(deps) == 2
        assert "Mathlib.Init" in deps
        assert "Mathlib.Algebra.Group.Defs" in deps
    
    def test_extract_sorted(self):
        """依赖已排序（K4 确定性）"""
        content = """
import Mathlib.Z
import Mathlib.A
import Mathlib.M
"""
        deps = extract_dependencies(content)
        assert deps == ["Mathlib.A", "Mathlib.M", "Mathlib.Z"]


class TestComputeDomainCoverage:
    """领域覆盖度测试"""
    
    def test_algebra_coverage(self):
        """代数领域覆盖"""
        theorems = [
            {"module": "Mathlib.Algebra.Group.Defs", "name": "add_assoc"},
            {"module": "Mathlib.Algebra.Ring.Defs", "name": "mul_assoc"},
        ]
        coverage = _compute_domain_coverage(theorems)
        assert coverage["algebra"] == 2
    
    def test_analysis_coverage(self):
        """分析领域覆盖"""
        theorems = [
            {"module": "Mathlib.Analysis.Calculus.Defs", "name": "deriv_pow"},
        ]
        coverage = _compute_domain_coverage(theorems)
        assert coverage["analysis"] == 1
    
    def test_number_theory_coverage(self):
        """数论领域覆盖"""
        theorems = [
            {"module": "Mathlib.Data.Nat.Defs", "name": "add_zero"},
            {"module": "Mathlib.Data.Int.Defs", "name": "mul_one"},
        ]
        coverage = _compute_domain_coverage(theorems)
        assert coverage["number_theory"] == 2
    
    def test_combinatorics_coverage(self):
        """组合数学领域覆盖"""
        theorems = [
            {"module": "Mathlib.Combinatorics.Defs", "name": "choose_zero"},
        ]
        coverage = _compute_domain_coverage(theorems)
        assert coverage["combinatorics"] == 1
    
    def test_logic_coverage(self):
        """逻辑领域覆盖"""
        theorems = [
            {"module": "Mathlib.Tactic.Defs", "name": "suggest_example"},
        ]
        coverage = _compute_domain_coverage(theorems)
        assert coverage["logic"] == 1


class TestBuildIndex:
    """索引构建测试"""
    
    def test_build_index_basic(self):
        """基本索引构建"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 创建测试文件
            (tmp_path / "Mathlib").mkdir()
            (tmp_path / "Mathlib" / "Algebra").mkdir()
            (tmp_path / "Mathlib" / "Algebra" / "Group").mkdir()
            
            lean_file = tmp_path / "Mathlib" / "Algebra" / "Group" / "Defs.lean"
            lean_file.write_text("""
import Mathlib.Init

theorem add_assoc {α : Type u_1} [Add α] [AddSemigroup α] (a b c : α) :
    a + b + c = a + (b + c) := by
  sorry
""")
            
            output_path = tmp_path / "output"
            manifest = build_index(tmp_path, output_path)
            
            assert manifest["theorem_count"] == 1
            assert "sha256" in manifest
            assert "generation_date" in manifest
            assert (output_path / "theorems.jsonl").exists()
            assert (output_path / "manifest.json").exists()
    
    def test_build_index_with_commit(self):
        """带 commit hash 的索引构建"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            
            output_path = tmp_path / "output"
            manifest = build_index_with_commit(tmp_path, output_path, "abc123def")

            # v0.1.1：溯源字段改为 upstream_commit，且拒绝 unknown
            assert manifest["upstream_commit"] == "abc123def"
            assert "unknown" not in str(manifest.get("upstream_commit", "")).lower()

    def test_build_index_rejects_unknown_commit(self):
        """拒绝 unknown 作为上游 commit（preflight ㉗：溯源不得造假）"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            with pytest.raises(ValueError):
                build_index_with_commit(tmp_path, tmp_path / "out", "unknown")

    def test_sample_index_manifest_is_honest(self):
        """随包样例索引必须声明 kind 与规模，且不写 unknown commit"""
        import json
        manifest = json.loads(
            (Path(__file__).resolve().parents[1] / "data" / "index" / "manifest.json")
            .read_text(encoding="utf-8"))
        assert manifest["index_kind"] == "curated-sample"
        assert manifest["theorem_count"] == 35
        assert manifest.get("upstream_commit") is None
        assert "unknown" not in json.dumps(manifest, ensure_ascii=False).lower()
        assert "provenance_note" in manifest
    
    def test_build_index_nonexistent_path(self):
        """不存在的路径抛出异常"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "output"
            
            with pytest.raises(FileNotFoundError):
                build_index(tmp_path / "nonexistent", output_path)
    
    def test_build_index_deterministic(self):
        """同输入同结果（K4 确定性）"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            
            output_path1 = tmp_path / "output1"
            output_path2 = tmp_path / "output2"
            
            manifest1 = build_index(tmp_path, output_path1)
            manifest2 = build_index(tmp_path, output_path2)
            
            # sha256 应该相同
            assert manifest1["sha256"] == manifest2["sha256"]
            # theorem_count 应该相同
            assert manifest1["theorem_count"] == manifest2["theorem_count"]
    
    def test_build_index_no_src_subdirectory(self):
        """没有 src 子目录时扫描根目录"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 直接在根目录创建文件
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            
            output_path = tmp_path / "output"
            manifest = build_index(tmp_path, output_path)
            
            assert manifest["theorem_count"] == 1
    
    def test_build_index_mutation_validation(self):
        """变异验证：故意弄坏被测行为 → 门必须变红"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 创建测试文件
            (tmp_path / "Test.lean").write_text("theorem test : True := by sorry")
            
            output_path = tmp_path / "output"
            manifest1 = build_index(tmp_path, output_path)
            
            # 变异：修改文件内容
            (tmp_path / "Test.lean").write_text("theorem test : False := by sorry")
            
            output_path2 = tmp_path / "output2"
            manifest2 = build_index(tmp_path, output_path2)
            
            # sha256 应该不同（证明门能检测到变化）
            assert manifest1["sha256"] != manifest2["sha256"]
            # theorem_count 应该相同（内容变了但定理数没变）
            assert manifest1["theorem_count"] == manifest2["theorem_count"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
