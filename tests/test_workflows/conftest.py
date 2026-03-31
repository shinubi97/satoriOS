"""工作流测试配置和 fixtures."""
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_vault_for_workflow():
    """创建用于工作流测试的临时 Vault."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "vault"
        vault_path.mkdir(parents=True)

        # 创建 PARA 目录结构
        (vault_path / "00_收件箱").mkdir()
        (vault_path / "10_项目").mkdir()
        (vault_path / "10_项目" / "编程").mkdir()
        (vault_path / "20_领域").mkdir()
        (vault_path / "30_研究").mkdir()
        (vault_path / "30_研究" / "编程").mkdir()
        (vault_path / "40_知识库").mkdir()
        (vault_path / "40_知识库" / "moc").mkdir()
        (vault_path / "50_归档").mkdir()
        (vault_path / "99_模板").mkdir()
        (vault_path / "Daily").mkdir()
        (vault_path / "metadata").mkdir()

        yield vault_path