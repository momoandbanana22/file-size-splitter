"""ファイル分割機能のテスト"""

import pytest
from pathlib import Path


def test_parse_size_bytes():
    """数値のみ（バイト）のパース"""
    from file_size_splitter.splitter import parse_size
    
    assert parse_size("1024") == 1024
    assert parse_size("100") == 100


def test_parse_size_with_unit():
    """単位付きのパース"""
    from file_size_splitter.splitter import parse_size
    
    assert parse_size("1K") == 1024
    assert parse_size("1M") == 1024 * 1024
    assert parse_size("1G") == 1024 * 1024 * 1024
    assert parse_size("10K") == 10 * 1024
    assert parse_size("5M") == 5 * 1024 * 1024


def test_parse_size_invalid():
    """無効なサイズ指定"""
    from file_size_splitter.splitter import parse_size
    
    with pytest.raises(ValueError):
        parse_size("invalid")
    
    with pytest.raises(ValueError):
        parse_size("")


def test_split_file(tmp_path):
    """ファイル分割機能"""
    from file_size_splitter.splitter import split_file
    
    # テスト用ファイルを作成
    test_file = tmp_path / "test.txt"
    test_content = b"a" * 100  # 100バイト
    test_file.write_bytes(test_content)
    
    # 50バイトごとに分割
    output_dir = tmp_path / "output"
    metadata = split_file(str(test_file), "50", str(output_dir))
    
    # 分割ファイルが2つ作成されていることを確認
    assert (output_dir / "test.txt.001").exists()
    assert (output_dir / "test.txt.002").exists()
    
    # メタデータが生成されていることを確認
    assert metadata["original_file"] == "test.txt"
    assert metadata["original_size"] == 100
    assert metadata["split_size"] == 50
    assert metadata["part_count"] == 2
    assert len(metadata["parts"]) == 2


def test_generate_bat_script(tmp_path):
    """BATファイル生成機能"""
    from file_size_splitter.splitter import generate_bat_script
    
    metadata = {
        "original_file": "test.txt",
        "original_size": 100,
        "split_size": 50,
        "part_count": 2,
        "parts": [
            {"filename": "test.txt.001", "size": 50},
            {"filename": "test.txt.002", "size": 50},
        ],
    }
    
    bat_path = tmp_path / "restore.bat"
    generate_bat_script(metadata, str(bat_path))
    
    # BATファイルが生成されていることを確認
    assert bat_path.exists()
    
    # BATファイルの内容を確認
    bat_content = bat_path.read_text(encoding="shift-jis")
    assert "@echo off" in bat_content
    assert "test.txt.001" in bat_content
    assert "test.txt.002" in bat_content
    assert "copy" in bat_content


def test_generate_ps1_script(tmp_path):
    """PS1ファイル生成機能"""
    from file_size_splitter.splitter import generate_ps1_script
    
    metadata = {
        "original_file": "test.txt",
        "original_size": 100,
        "split_size": 50,
        "part_count": 2,
        "parts": [
            {"filename": "test.txt.001", "size": 50},
            {"filename": "test.txt.002", "size": 50},
        ],
    }
    
    ps1_path = tmp_path / "restore.ps1"
    generate_ps1_script(metadata, str(ps1_path))
    
    # PS1ファイルが生成されていることを確認
    assert ps1_path.exists()
    
    # PS1ファイルの内容を確認
    ps1_content = ps1_path.read_text(encoding="utf-8")
    assert "Write-Host" in ps1_content
    assert "test.txt.001" in ps1_content
    assert "test.txt.002" in ps1_content
    assert "Get-Content" in ps1_content
