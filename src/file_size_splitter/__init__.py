"""File Size Splitter - ファイル分割・復元ツール"""

from .splitter import parse_size, split_file, generate_bat_script, generate_ps1_script

__version__ = "0.1.5"
__all__ = ["parse_size", "split_file", "generate_bat_script", "generate_ps1_script"]
