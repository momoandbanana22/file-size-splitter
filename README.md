# File Size Splitter

[![PyPI version](https://badge.fury.io/py/file-size-splitter.svg)](https://badge.fury.io/py/file-size-splitter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

ファイルを指定されたサイズで分割し、分割したファイルを復元するツール。

## ライセンス

MIT License

## リポジトリ

https://github.com/momoandbanana22/file-size-splitter

## 仕様

### 機能1: ファイル分割
- 指定されたファイルを、指定のサイズで分割する
  - 分割サイズの指定方法：数値のみ（例: `10485760`）または単位付き（例: `10M`, `1G`）の両方に対応
  - 単位: K（キロバイト）、M（メガバイト）、G（ギガバイト）
- 分割されたファイルには連番を付与する（例: `file.001`, `file.002`, ...）
- 分割情報を記録したメタデータファイルをJSON形式で生成する
  - オリジナルファイルと各分割ファイルのsha512ハッシュを含む
- 出力先ディレクトリを指定可能（指定なしの場合は入力ファイルと同じディレクトリ）
- ストリーミング処理でメモリ効率よく分割する（大きなファイルでも対応）
- 分割時に自動的に復元確認を行い、ファイルの整合性を保証

### 機能2: 復元用スクリプト生成
- 分割時にBATファイル（Windows用）とPS1ファイル（PowerShell用）の両方を自動生成
- 生成されたスクリプトを使用して、分割されたファイルを元のファイルに復元する
- 復元時のファイル名はメタデータファイルから自動取得
- 復元時にsha512ハッシュ検証を行い、ファイルの整合性を確認
  - 各分割ファイルのハッシュを検証
  - 復元後のファイルのハッシュを検証

## 使用方法

### ファイル分割
```bash
file-size-splitter <入力ファイル> <分割サイズ> [-o 出力ディレクトリ]
```

**例:**
```bash
# 10MBごとに分割
file-size-splitter largefile.zip 10M

# 出力ディレクトリを指定
file-size-splitter largefile.zip 10M -o output

# バイト数で指定
file-size-splitter largefile.zip 10485760
```

### ファイル復元
分割されたファイル（*.001, *.002, ...）とメタデータファイル（*.metadata.json）を同じディレクトリに配置し、生成された `restore.bat` または `restore.ps1` を実行します。

```bash
# BATファイルを使用（Windows）
restore.bat

# PS1ファイルを使用（PowerShell）
powershell -ExecutionPolicy Bypass -File restore.ps1
```

## インストール

### PyPIからインストール
```bash
pip install file-size-splitter
```

### ソースコードからインストール（開発環境）
```bash
git clone https://github.com/momoandbanana22/file-size-splitter.git
cd file-size-splitter
pip install -e .
```

## ライブラリとしての使用

Pythonスクリプト内からライブラリとして使用することもできます（PyPIからインストールした場合、またはソースコードからインストールした場合のどちらでも使用可能）。

```python
from file_size_splitter import split_file, generate_bat_script, generate_ps1_script, calculate_sha512

# ファイルを分割
metadata = split_file("largefile.zip", "10M", "output")

# 復元スクリプトを生成
generate_bat_script(metadata, "output/restore.bat")
generate_ps1_script(metadata, "output/restore.ps1")

# sha512ハッシュを計算
hash_value = calculate_sha512("largefile.zip")
```
