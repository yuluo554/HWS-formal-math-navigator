"""解析层测试（M2）

测试统一中间表示 + 规则优先解析器。
遵循 K4（同输入同结果）和 K10（UTF-8 输出）口径。
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from hws_formal_math.parser import (
    LeanDeclaration,
    TheoremDecl,
    Definition,
    InductiveDecl,
    StructureDecl,
    ClassDecl,
    InstanceDecl,
    ModuleRef,
    ParseResult,
    DeclarationType,
    LeanParser,
    parse_lean_file,
    parse_theorem_declaration,
    extract_dependencies
)


class TestModuleRef:
    """模块引用测试"""

    def test_module_ref_str(self):
        """模块引用字符串表示"""
        ref = ModuleRef(module="Mathlib.Algebra.Group", name="add_assoc")
        assert str(ref) == "Mathlib.Algebra.Group.add_assoc"

    def test_module_ref_no_module(self):
        """无模块名"""
        ref = ModuleRef(module="", name="add_assoc")
        assert str(ref) == "add_assoc"

    def test_module_ref_to_dict(self):
        """转换为字典"""
        ref = ModuleRef(module="Mathlib.Algebra.Group", name="add_assoc")
        assert ref.to_dict() == {"module": "Mathlib.Algebra.Group", "name": "add_assoc"}


class TestLeanDeclaration:
    """声明基类测试"""

    def test_theorem_decl_to_dict(self):
        """定理声明转换为字典"""
        decl = TheoremDecl(
            name="add_assoc",
            module="Mathlib.Algebra.Group.Defs",
            signature="∀ {α : Type u_1} [Add α] [AddSemigroup α] (a b c : α), a + b + c = a + (b + c)",
            line=42,
            deps=["Mathlib.Init", "Mathlib.Algebra.Group.Defs"]
        )
        
        d = decl.to_dict()
        assert d["name"] == "add_assoc"
        assert d["decl_type"] == "theorem"
        assert d["deps"] == ["Mathlib.Algebra.Group.Defs", "Mathlib.Init"]  # 已排序

    def test_declaration_immutable(self):
        """声明不可变（frozen dataclass）"""
        decl = TheoremDecl(
            name="add_assoc",
            module="Mathlib.Algebra.Group.Defs",
            signature="test",
            line=1
        )
        with pytest.raises(AttributeError):
            decl.name = "other"


class TestParseResult:
    """解析结果测试"""

    def test_parse_result_to_dict(self):
        """解析结果转换为字典"""
        decl = TheoremDecl(
            name="add_assoc",
            module="Mathlib.Algebra.Group.Defs",
            signature="test",
            line=1
        )
        
        result = ParseResult(
            declarations=[decl],
            dependencies=["Mathlib.Init"],
            module="Mathlib.Algebra.Group.Defs",
            source_file="test.lean"
        )
        
        d = result.to_dict()
        assert d["module"] == "Mathlib.Algebra.Group.Defs"
        assert d["declaration_count"] == 1
        assert d["dependencies"] == ["Mathlib.Init"]

    def test_parse_result_equality(self):
        """解析结果相等性"""
        decl1 = TheoremDecl(name="add_assoc", module="M", signature="test", line=1)
        decl2 = TheoremDecl(name="add_assoc", module="M", signature="test", line=1)
        
        result1 = ParseResult(
            declarations=[decl1],
            dependencies=["M"],
            module="M",
            source_file="test.lean"
        )
        result2 = ParseResult(
            declarations=[decl2],
            dependencies=["M"],
            module="M",
            source_file="test.lean"
        )
        
        assert result1 == result2


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

    def test_extract_deduplicated(self):
        """依赖去重"""
        content = """
import Mathlib.Init
import Mathlib.Init
import Mathlib.Algebra.Group.Defs
"""
        deps = extract_dependencies(content)
        assert len(deps) == 2
        assert "Mathlib.Init" in deps


class TestParseTheoremDeclaration:
    """定理声明解析测试（兼容旧接口）"""

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
        assert "Nat.choose (n + 1) (k + 1)" in theorems[0]["signature"]


class TestParseLeanFile:
    """文件解析测试"""

    def test_parse_theorem_file(self):
        """解析定理文件"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
import Mathlib.Init

theorem add_assoc {α : Type u_1} [Add α] [AddSemigroup α] (a b c : α) :
    a + b + c = a + (b + c) := by
  sorry
""", encoding='utf-8')
            
            result = parse_lean_file(lean_file, "Mathlib.Test")
            
            assert result.module == "Mathlib.Test"
            assert len(result.dependencies) == 1
            assert "Mathlib.Init" in result.dependencies
            assert len(result.declarations) == 1
            assert result.declarations[0].name == "add_assoc"

    def test_parse_lemma_file(self):
        """解析引理文件"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
lemma add_comm (a b : Nat) : a + b = b + a := by
  sorry
""", encoding='utf-8')
            
            result = parse_lean_file(lean_file, "Mathlib.Test")
            
            assert len(result.declarations) == 1
            assert result.declarations[0].name == "add_comm"
            assert result.declarations[0].decl_type == DeclarationType.THEOREM

    def test_parse_definition_file(self):
        """解析定义文件"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
def add_one (n : Nat) : Nat :=
  n + 1
""", encoding='utf-8')
            
            result = parse_lean_file(lean_file, "Mathlib.Test")
            
            assert len(result.declarations) == 1
            assert result.declarations[0].name == "add_one"
            assert isinstance(result.declarations[0], Definition)

    def test_parse_empty_file(self):
        """解析空文件"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Empty.lean"
            lean_file.write_text("-- 只有注释", encoding='utf-8')
            
            result = parse_lean_file(lean_file, "Mathlib.Empty")
            
            assert len(result.declarations) == 0
            assert len(result.dependencies) == 0


class TestLeanParser:
    """Lean 解析器测试"""

    def test_parse_file_cached(self):
        """解析文件缓存"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("theorem test : True := by sorry", encoding='utf-8')
            
            parser = LeanParser()
            result1 = parser.parse_file(lean_file, "Mathlib.Test")
            result2 = parser.parse_file(lean_file, "Mathlib.Test")
            
            # 缓存命中，返回相同对象
            assert result1 is result2

    def test_parse_directory(self):
        """解析目录"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 创建多个 .lean 文件
            (tmp_path / "Test1.lean").write_text("theorem test1 : True := by sorry", encoding='utf-8')
            (tmp_path / "Test2.lean").write_text("theorem test2 : True := by sorry", encoding='utf-8')
            
            parser = LeanParser()
            results = parser.parse_directory(tmp_path)
            
            assert len(results) == 2

    def test_clear_cache(self):
        """清空缓存"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("theorem test : True := by sorry", encoding='utf-8')
            
            parser = LeanParser()
            parser.parse_file(lean_file, "Mathlib.Test")
            
            assert len(parser._cache) > 0
            
            parser.clear_cache()
            assert len(parser._cache) == 0


class TestDeterministicParsing:
    """确定性解析测试（K4 同输入同结果）"""

    def test_same_file_same_result(self):
        """同文件同结果"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
import Mathlib.Z
import Mathlib.A
import Mathlib.M

theorem add_assoc : a + b + c = a + (b + c) := by sorry
theorem add_comm : a + b = b + a := by sorry
""", encoding='utf-8')
            
            result1 = parse_lean_file(lean_file, "Mathlib.Test")
            result2 = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 结果应该完全相同
            assert result1 == result2
            assert result1.to_dict() == result2.to_dict()

    def test_dependencies_sorted(self):
        """依赖已排序"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
import Mathlib.Z
import Mathlib.A
import Mathlib.M
""", encoding='utf-8')
            
            result = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 依赖应该已排序
            assert result.dependencies == ["Mathlib.A", "Mathlib.M", "Mathlib.Z"]

    def test_declarations_sorted(self):
        """声明已排序"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
theorem zebra : True := by sorry
theorem apple : True := by sorry
theorem monkey : True := by sorry
""", encoding='utf-8')
            
            result = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 声明应该按名字排序
            names = [d.name for d in result.declarations]
            assert names == ["apple", "monkey", "zebra"]


class TestDualRunDeterministic:
    """双跑确定性测试（M2 DoD）"""

    def test_dual_run_same_result(self):
        """双跑结果相同"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("""
import Mathlib.Init
import Mathlib.Algebra.Group.Defs

theorem add_assoc {α : Type u_1} [Add α] [AddSemigroup α] (a b c : α) :
    a + b + c = a + (b + c) := by
  sorry

lemma add_comm (a b : Nat) : a + b = b + a := by
  sorry
""", encoding='utf-8')
            
            # 第一次运行
            result1 = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 第二次运行（模拟重新加载）
            result2 = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 两次结果应该完全相同
            assert result1.to_dict() == result2.to_dict()

    def test_dual_run_json_serialization(self):
        """双跑 JSON 序列化一致"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("theorem test : True := by sorry", encoding='utf-8')
            
            # 第一次运行
            result1 = parse_lean_file(lean_file, "Mathlib.Test")
            json1 = json.dumps(result1.to_dict(), sort_keys=True, ensure_ascii=False)
            
            # 第二次运行
            result2 = parse_lean_file(lean_file, "Mathlib.Test")
            json2 = json.dumps(result2.to_dict(), sort_keys=True, ensure_ascii=False)
            
            # JSON 应该完全相同
            assert json1 == json2


class TestMutationValidation:
    """变异验证测试"""

    def test_mutation_detection(self):
        """变异检测：修改文件内容后结果应不同"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            lean_file = tmp_path / "Test.lean"
            lean_file.write_text("theorem test : True := by sorry", encoding='utf-8')
            
            result1 = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 变异：修改文件内容
            lean_file.write_text("theorem test : False := by sorry", encoding='utf-8')
            
            result2 = parse_lean_file(lean_file, "Mathlib.Test")
            
            # 结果应该不同
            assert result1 != result2
            assert result1.to_dict() != result2.to_dict()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
