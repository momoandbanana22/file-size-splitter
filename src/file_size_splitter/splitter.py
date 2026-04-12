"""ファイル分割機能"""

import json
from pathlib import Path
from typing import Dict, Any


def parse_size(size_str: str) -> int:
    """サイズ文字列をバイト数に変換する
    
    Args:
        size_str: サイズ文字列（例: "1024", "1K", "1M", "1G"）
    
    Returns:
        バイト数
    
    Raises:
        ValueError: 無効なサイズ文字列の場合
    """
    if not size_str:
        raise ValueError("サイズ文字列が空です")
    
    size_str = size_str.strip().upper()
    
    # 単位のチェック
    units = {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
    }
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                num = float(size_str[:-1])
                return int(num * multiplier)
            except ValueError:
                raise ValueError(f"無効なサイズ指定: {size_str}")
    
    # 単位なし（バイト）
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"無効なサイズ指定: {size_str}")


def split_file(input_file: str, size_str: str, output_dir: str = None) -> Dict[str, Any]:
    """ファイルを指定されたサイズで分割する
    
    Args:
        input_file: 入力ファイルパス
        size_str: 分割サイズ（例: "1024", "1K", "1M"）
        output_dir: 出力ディレクトリ（省略時は入力ファイルと同じディレクトリ）
    
    Returns:
        メタデータ辞書
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {input_file}")
    
    # 分割サイズをパース
    split_size = parse_size(size_str)
    
    # 出力ディレクトリの決定
    if output_dir is None:
        output_path = input_path.parent
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # メタデータの初期化
    metadata: Dict[str, Any] = {
        "original_file": input_path.name,
        "original_size": input_path.stat().st_size,
        "split_size": split_size,
        "part_count": 0,
        "parts": [],
    }
    
    # ストリーミングでファイルを分割
    part_number = 1
    with open(input_path, "rb") as f:
        while True:
            chunk = f.read(split_size)
            if not chunk:
                break
            
            # 分割ファイルのパス
            part_filename = f"{input_path.name}.{part_number:03d}"
            part_path = output_path / part_filename
            
            # 分割ファイルを書き込み
            with open(part_path, "wb") as part_f:
                part_f.write(chunk)
            
            # メタデータに追加
            metadata["parts"].append({
                "filename": part_filename,
                "size": len(chunk),
            })
            
            part_number += 1
    
    metadata["part_count"] = part_number - 1
    
    # メタデータファイルを保存
    metadata_path = output_path / f"{input_path.name}.metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata


def generate_bat_script(metadata: Dict[str, Any], output_path: str) -> None:
    """復元用BATファイルを生成する
    
    Args:
        metadata: メタデータ辞書
        output_path: 出力ファイルパス
    """
    original_file = metadata["original_file"]
    parts = metadata["parts"]
    
    # BATファイルの内容を生成
    lines = [
        "@echo off",
        "chcp 65001 > nul",
        f"echo 復元中: {original_file}",
        "",
    ]
    
    # copyコマンドでファイルを結合
    part_files = " + ".join([f'"{p["filename"]}"' for p in parts])
    lines.append(f"copy /B {part_files} \"{original_file}\"")
    lines.append("")
    lines.append(f"echo 復元完了: {original_file}")
    lines.append("pause")
    
    # BATファイルを書き込み
    bat_content = "\r\n".join(lines)
    with open(output_path, "w", encoding="shift-jis") as f:
        f.write(bat_content)


def generate_ps1_script(metadata: Dict[str, Any], output_path: str) -> None:
    """復元用PS1ファイルを生成する
    
    Args:
        metadata: メタデータ辞書
        output_path: 出力ファイルパス
    """
    original_file = metadata["original_file"]
    parts = metadata["parts"]
    
    # PS1ファイルの内容を生成
    lines = [
        "# 復元用スクリプト",
        f"Write-Host '復元中: {original_file}'",
        "",
    ]
    
    # Get-ContentとSet-Contentでファイルを結合
    part_files = [f'"{p["filename"]}"' for p in parts]
    lines.append(f"$parts = {', '.join(part_files)}")
    lines.append("$output = \"" + original_file + "\"")
    lines.append("")
    lines.append("$parts | ForEach-Object { Get-Content -Path $_ -Raw } | Set-Content -Path $output")
    lines.append("")
    lines.append(f"Write-Host '復元完了: {original_file}'")
    lines.append("Read-Host 'Enterキーを押してください'")
    
    # PS1ファイルを書き込み
    ps1_content = "\r\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ps1_content)
