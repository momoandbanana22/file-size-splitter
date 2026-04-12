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


def test_library_import():
    """ライブラリとしてのimportをテスト"""
    # __init__.pyから主要な関数をimportできることを確認
    from file_size_splitter import parse_size, split_file, generate_bat_script, generate_ps1_script
    
    # 関数が正しくimportされていることを確認
    assert callable(parse_size)
    assert callable(split_file)
    assert callable(generate_bat_script)
    assert callable(generate_ps1_script)


def test_calculate_sha512(tmp_path):
    """sha512ハッシュ計算関数のテスト"""
    from file_size_splitter import calculate_sha512
    import hashlib
    
    # テスト用の一時ファイルを作成
    test_file = tmp_path / "test_hash.txt"
    test_file.write_text("test content")
    
    # sha512ハッシュを計算
    hash_value = calculate_sha512(str(test_file))
    
    # hashlibを使って期待値を計算
    with open(test_file, "rb") as f:
        expected_hash = hashlib.sha512(f.read()).hexdigest()
    
    # ハッシュ値が一致することを確認
    assert hash_value == expected_hash


def test_split_file_with_sha512(tmp_path):
    """sha512ハッシュ計算付きのファイル分割テスト"""
    from file_size_splitter import split_file
    
    # テスト用の入力ファイルを作成
    input_file = tmp_path / "test.txt"
    input_file.write_text("Hello, World! This is a test file.")
    
    # ファイルを分割
    metadata = split_file(str(input_file), "10")
    
    # メタデータにsha512ハッシュが含まれていることを確認
    assert "original_sha512" in metadata
    assert metadata["original_sha512"]  # 空でないことを確認
    
    # 各分割ファイルのsha512ハッシュが含まれていることを確認
    for part in metadata["parts"]:
        assert "sha512" in part
        assert part["sha512"]  # 空でないことを確認


def test_split_file_with_restore_verification(tmp_path):
    """復元確認付きのファイル分割テスト"""
    from file_size_splitter import split_file
    
    # テスト用の入力ファイルを作成
    input_file = tmp_path / "test.txt"
    input_file.write_text("Hello, World! This is a test file for restore verification.")
    
    # ファイルを分割（復元確認付き）
    metadata = split_file(str(input_file), "10")
    
    # 復元ファイルのパス
    restored_file = tmp_path / "restored_test.txt"
    
    # 分割ファイルを結合して復元
    with open(restored_file, "wb") as f:
        for part in metadata["parts"]:
            part_path = tmp_path / part["filename"]
            with open(part_path, "rb") as part_f:
                f.write(part_f.read())
    
    # 復元ファイルのsha512ハッシュを計算
    from file_size_splitter import calculate_sha512
    restored_sha512 = calculate_sha512(str(restored_file))
    
    # オリジナルファイルのsha512ハッシュと一致することを確認
    assert restored_sha512 == metadata["original_sha512"]
    
    # オリジナルファイルと復元ファイルの内容が一致することを確認
    assert restored_file.read_text() == input_file.read_text()


def test_generate_bat_script_with_hash_verification(tmp_path):
    """ハッシュ検証付きのBATファイル生成テスト"""
    from file_size_splitter import generate_bat_script
    
    # メタデータを作成
    metadata = {
        "original_file": "test.txt",
        "original_sha512": "abc123",
        "parts": [
            {"filename": "test.txt.001", "sha512": "def456"},
            {"filename": "test.txt.002", "sha512": "ghi789"},
        ]
    }
    
    # BATファイルを生成
    bat_path = tmp_path / "restore.bat"
    generate_bat_script(metadata, str(bat_path))
    
    # BATファイルが生成されていることを確認
    assert bat_path.exists()
    
    # BATファイルの内容を確認
    bat_content = bat_path.read_text(encoding="shift-jis")
    
    # ハッシュ検証コマンドが含まれていることを確認
    assert "sha512" in bat_content.lower() or "hash" in bat_content.lower()


def test_generate_ps1_script_with_hash_verification(tmp_path):
    """ハッシュ検証付きのPS1ファイル生成テスト"""
    from file_size_splitter import generate_ps1_script
    
    # メタデータを作成
    metadata = {
        "original_file": "test.txt",
        "original_sha512": "abc123",
        "parts": [
            {"filename": "test.txt.001", "sha512": "def456"},
            {"filename": "test.txt.002", "sha512": "ghi789"},
        ]
    }
    
    # PS1ファイルを生成
    ps1_path = tmp_path / "restore.ps1"
    generate_ps1_script(metadata, str(ps1_path))
    
    # PS1ファイルが生成されていることを確認
    assert ps1_path.exists()
    
    # PS1ファイルの内容を確認
    ps1_content = ps1_path.read_text(encoding="utf-8")
    
    # ハッシュ検証コマンドが含まれていることを確認
    assert "sha512" in ps1_content.lower() or "hash" in ps1_content.lower()
