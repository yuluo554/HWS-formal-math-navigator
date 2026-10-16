"""命题生成器测试"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.gen_proposals import (
    generate_proposals,
    generate_easy_proposition,
    generate_medium_proposition,
    generate_hard_proposition
)


class TestGenerateProposals:
    """命题生成测试"""
    
    def test_generate_proposals_basic(self):
        """基本命题生成"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            manifest = generate_proposals(tmp_path, num_cases=10)
            
            assert manifest["proposal_count"] == 10
            assert "seed" in manifest
            assert "generation_date" in manifest
            assert "difficulty_distribution" in manifest
            assert (tmp_path / "proposals.json").exists()
            assert (tmp_path / "manifest.json").exists()
    
    def test_generate_proposals_difficulty_distribution(self):
        """难度分布测试"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            manifest = generate_proposals(tmp_path, num_cases=50)
            
            dist = manifest["difficulty_distribution"]
            # 简单 40%，中等 40%，困难 20%
            assert dist["easy"] == 20
            assert dist["medium"] == 20
            assert dist["hard"] == 10
    
    def test_generate_proposals_deterministic(self):
        """同输入同结果（K4 确定性）"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            output1 = tmp_path / "output1"
            output2 = tmp_path / "output2"
            
            manifest1 = generate_proposals(output1, num_cases=10)
            manifest2 = generate_proposals(output2, num_cases=10)
            
            # 命题数量应该相同
            assert manifest1["proposal_count"] == manifest2["proposal_count"]
            
            # 读取命题文件并比较（排除 generated_at 时间戳）
            with open(output1 / "proposals.json", 'r') as f:
                proposals1 = json.load(f)
            with open(output2 / "proposals.json", 'r') as f:
                proposals2 = json.load(f)
            
            # 排除 generated_at 字段进行比较
            proposals1_clean = [
                {k: v for k, v in p.items() if k != "generated_at"}
                for p in proposals1
            ]
            proposals2_clean = [
                {k: v for k, v in p.items() if k != "generated_at"}
                for p in proposals2
            ]
            
            # 内容应该完全相同（除时间戳外）
            assert proposals1_clean == proposals2_clean
    
    def test_generate_proposals_domains(self):
        """领域覆盖测试"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            manifest = generate_proposals(tmp_path, num_cases=50)
            
            domains = manifest["domains"]
            assert "algebra" in domains
            assert "number_theory" in domains
            assert "combinatorics" in domains
    
    def test_generate_proposals_zero_cases(self):
        """零用例测试"""
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            manifest = generate_proposals(tmp_path, num_cases=0)
            
            assert manifest["proposal_count"] == 0


class TestGenerateEasyProposition:
    """简单命题生成测试"""
    
    def test_generate_easy_proposition_structure(self):
        """简单命题结构测试"""
        proposal = generate_easy_proposition(0)
        
        assert "id" in proposal
        assert "statement" in proposal
        assert "domain" in proposal
        assert "difficulty" in proposal
        assert "ground_truth" in proposal
        assert proposal["difficulty"] == "easy"
        assert proposal["id"].startswith("prop_easy_")
    
    def test_generate_easy_proposition_deterministic(self):
        """简单命题确定性测试"""
        proposal1 = generate_easy_proposition(0)
        proposal2 = generate_easy_proposition(0)
        
        # 相同 index 应该生成相同命题
        assert proposal1 == proposal2
    
    def test_generate_easy_proposition_different_index(self):
        """不同 index 生成不同命题"""
        proposal1 = generate_easy_proposition(0)
        proposal2 = generate_easy_proposition(1)
        
        assert proposal1["id"] != proposal2["id"]
    
    def test_generate_easy_proposition_ground_truth(self):
        """简单命题 ground truth 测试"""
        for i in range(10):
            proposal = generate_easy_proposition(i)
            assert isinstance(proposal["ground_truth"], list)
            assert len(proposal["ground_truth"]) > 0
            assert all(isinstance(gt, str) for gt in proposal["ground_truth"])


class TestGenerateMediumProposition:
    """中等命题生成测试"""
    
    def test_generate_medium_proposition_structure(self):
        """中等命题结构测试"""
        proposal = generate_medium_proposition(0)
        
        assert "id" in proposal
        assert "statement" in proposal
        assert "domain" in proposal
        assert "difficulty" in proposal
        assert "ground_truth" in proposal
        assert proposal["difficulty"] == "medium"
        assert proposal["id"].startswith("prop_medium_")
    
    def test_generate_medium_proposition_deterministic(self):
        """中等命题确定性测试"""
        proposal1 = generate_medium_proposition(0)
        proposal2 = generate_medium_proposition(0)
        
        assert proposal1 == proposal2


class TestGenerateHardProposition:
    """困难命题生成测试"""
    
    def test_generate_hard_proposition_structure(self):
        """困难命题结构测试"""
        proposal = generate_hard_proposition(0)
        
        assert "id" in proposal
        assert "statement" in proposal
        assert "domain" in proposal
        assert "difficulty" in proposal
        assert "ground_truth" in proposal
        assert proposal["difficulty"] == "hard"
        assert proposal["id"].startswith("prop_hard_")
    
    def test_generate_hard_proposition_deterministic(self):
        """困难命题确定性测试"""
        proposal1 = generate_hard_proposition(0)
        proposal2 = generate_hard_proposition(0)
        
        assert proposal1 == proposal2
    
    def test_generate_hard_proposition_multi_ground_truth(self):
        """困难命题可能有多个 ground truth"""
        for i in range(10):
            proposal = generate_hard_proposition(i)
            assert isinstance(proposal["ground_truth"], list)
            # 困难命题可能有多个 ground truth
            assert len(proposal["ground_truth"]) >= 1


class TestProposalDomains:
    """命题领域测试"""
    
    def test_easy_proposition_domains(self):
        """简单命题领域分布"""
        domains = set()
        for i in range(20):
            proposal = generate_easy_proposition(i)
            domains.add(proposal["domain"])
        
        assert "algebra" in domains
        assert "number_theory" in domains
    
    def test_medium_proposition_domains(self):
        """中等命题领域分布"""
        domains = set()
        for i in range(20):
            proposal = generate_medium_proposition(i)
            domains.add(proposal["domain"])
        
        assert "algebra" in domains
        assert "number_theory" in domains
        assert "combinatorics" in domains
    
    def test_hard_proposition_domains(self):
        """困难命题领域分布"""
        domains = set()
        for i in range(10):
            proposal = generate_hard_proposition(i)
            domains.add(proposal["domain"])
        
        assert "algebra" in domains
        assert "combinatorics" in domains


class TestProposalStatementFormat:
    """命题陈述格式测试"""
    
    def test_statement_not_empty(self):
        """命题陈述不为空"""
        for i in range(10):
            proposal = generate_easy_proposition(i)
            assert len(proposal["statement"]) > 0
    
    def test_statement_starts_with_prove(self):
        """命题陈述以"证明"开头"""
        for i in range(10):
            proposal = generate_easy_proposition(i)
            assert proposal["statement"].startswith("证明")


class TestMutationValidation:
    """变异验证测试：故意弄坏被测行为 → 门必须变红"""
    
    def test_proposals_mutation_validation(self):
        """变异验证：修改 seed 后结果应不同"""
        from tools.gen_proposals import generate_easy_proposition, SEED
        
        # 正常情况
        proposal1 = generate_easy_proposition(0)
        
        # 变异：临时修改 seed
        original_seed = SEED
        try:
            # monkey-patch SEED
            import tools.gen_proposals as gp
            original_seed_value = gp.SEED
            gp.SEED = 999  # 不同的 seed
            
            proposal2 = generate_easy_proposition(0)
            
            # 结果应该不同（证明门能检测到变化）
            assert proposal1 != proposal2
        finally:
            gp.SEED = original_seed_value
    
    def test_proposals_deterministic_with_fixed_date(self):
        """确定性测试：固定日期应确保 generated_at 一致"""
        proposal1 = generate_easy_proposition(0)
        proposal2 = generate_easy_proposition(0)
        
        # generated_at 应该相同（固定日期）
        assert proposal1["generated_at"] == proposal2["generated_at"]
        # 整个对象应该相同
        assert proposal1 == proposal2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
