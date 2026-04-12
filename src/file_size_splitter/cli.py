"""CLIインターフェース"""

import argparse
import sys
from pathlib import Path

from file_size_splitter.splitter import split_file, generate_bat_script, generate_ps1_script


def main() -> int:
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="ファイルを指定されたサイズで分割し、復元用スクリプトを生成する"
    )
    parser.add_argument(
        "input_file",
        help="入力ファイルパス"
    )
    parser.add_argument(
        "size",
        help="分割サイズ（例: 1024, 1K, 1M, 1G）"
    )
    parser.add_argument(
        "-o", "--output",
        help="出力ディレクトリ（省略時は入力ファイルと同じディレクトリ）"
    )
    
    args = parser.parse_args()
    
    try:
        # ファイルを分割
        metadata = split_file(args.input_file, args.size, args.output)
        
        # 出力ディレクトリの決定
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = Path(args.input_file).parent
        
        # BATファイルとPS1ファイルを生成
        bat_path = output_dir / "restore.bat"
        ps1_path = output_dir / "restore.ps1"
        
        generate_bat_script(metadata, str(bat_path))
        generate_ps1_script(metadata, str(ps1_path))
        
        print(f"分割完了: {metadata['original_file']}")
        print(f"  - 分割数: {metadata['part_count']}")
        print(f"  - 分割サイズ: {metadata['split_size']} バイト")
        print(f"  - 復元スクリプト: restore.bat, restore.ps1")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
