"""ファイル分割機能"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional


def calculate_sha512(file_path: str) -> str:
    """ファイルのsha512ハッシュを計算する
    
    Args:
        file_path: ファイルパス
    
    Returns:
        sha512ハッシュ値（16進数文字列）
    """
    sha512_hash = hashlib.sha512()
    with open(file_path, "rb") as f:
        # ファイルをチャンクで読み込んでハッシュ計算（メモリ効率）
        for chunk in iter(lambda: f.read(8192), b""):
            sha512_hash.update(chunk)
    return sha512_hash.hexdigest()


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


def split_file(input_file: str, size_str: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
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
        "original_sha512": calculate_sha512(str(input_path)),
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
            
            # 分割ファイルのsha512ハッシュを計算
            part_sha512 = calculate_sha512(str(part_path))
            
            # メタデータに追加
            metadata["parts"].append({
                "filename": part_filename,
                "size": len(chunk),
                "sha512": part_sha512,
            })
            
            part_number += 1
    
    metadata["part_count"] = part_number - 1
    
    # 全ての分割ファイルの作成後に復元確認を行う
    # 分割ファイルを結合して復元
    restored_path = output_path / f"{input_path.name}.restored.tmp"
    with open(restored_path, "wb") as f:
        for p in metadata["parts"]:
            p_path = output_path / p["filename"]
            with open(p_path, "rb") as p_f:
                f.write(p_f.read())
    
    # 復元ファイルのsha512ハッシュを計算
    restored_sha512 = calculate_sha512(str(restored_path))
    
    # オリジナルファイルのsha512ハッシュと一致することを確認
    if restored_sha512 != metadata["original_sha512"]:
        raise ValueError(f"復元確認に失敗しました: sha512ハッシュが一致しません")
    
    # 復元ファイルを削除
    restored_path.unlink()
    
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
    
    # BATファイルの内容を生成（PS1スクリプトを起動するだけ）
    lines = [
        "@echo off",
        "chcp 65001 > nul",
        f"echo 復元中: {original_file}",
        "",
        "powershell -ExecutionPolicy Bypass -File restore.ps1",
        "",
        f"echo 復元完了: {original_file}",
        "pause",
    ]
    
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
    original_sha512 = metadata.get("original_sha512", "")
    parts = metadata["parts"]
    
    # PS1ファイルの内容を生成
    lines = [
        "# 復元用スクリプト",
        f"Write-Host '復元中: {original_file}'",
        "",
    ]
    
    # 各分割ファイルのsha512ハッシュ検証
    for part in parts:
        filename = part["filename"]
        expected_sha512 = part.get("sha512", "")
        if expected_sha512:
            lines.append(f"Write-Host '検証中: {filename}'")
            lines.append(f"$hash = (Get-FileHash -Path '{filename}' -Algorithm SHA512).Hash.ToString()")
            lines.append(f"if ($hash -ne '{expected_sha512}') {{ Write-Host 'エラー: {filename} のハッシュが一致しません'; exit 1 }}")
            lines.append(f"Write-Host 'OK: {filename}'")
            lines.append("")
    
    # .NETのバイナリモードでファイルを結合
    part_files = [f'"{p["filename"]}"' for p in parts]
    lines.append(f"$parts = {', '.join(part_files)}")
    lines.append("$output = \"" + original_file + "\"")
    lines.append("")
    lines.append("$stream = [System.IO.File]::OpenWrite($output)")
    lines.append("$parts | ForEach-Object {")
    lines.append("    $bytes = [System.IO.File]::ReadAllBytes($_)")
    lines.append("    $stream.Write($bytes, 0, $bytes.Length)")
    lines.append("}")
    lines.append("$stream.Close()")
    lines.append("")
    
    # 復元ファイルのsha512ハッシュ検証
    if original_sha512:
        lines.append(f"Write-Host '検証中: {original_file}'")
        lines.append(f"$hash = (Get-FileHash -Path '{original_file}' -Algorithm SHA512).Hash.ToString()")
        lines.append(f"if ($hash -ne '{original_sha512}') {{ Write-Host 'エラー: {original_file} のハッシュが一致しません'; exit 1 }}")
        lines.append(f"Write-Host 'OK: {original_file}'")
        lines.append("")
    
    lines.append(f"Write-Host '復元完了: {original_file}'")
    lines.append("Read-Host 'Enterキーを押してください'")
    
    # PS1ファイルを書き込み
    ps1_content = "\r\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ps1_content)
