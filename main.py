import os
import sys
from pathlib import Path

import requests
from pypinyin import pinyin


def is_chinese_char(char: str) -> bool:
    """
    Check if the given character is a Chinese character.

    Args:
        char (str): A single character to check

    Returns:
        bool: True if the character is Chinese, False otherwise
    """
    if len(char) != 1:
        return False

    code_point = ord(char)

    # Unicode ranges for Chinese characters
    ranges = [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
        (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
        (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
        (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
        (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
        (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F
        (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
        (0x31350, 0x323AF),  # CJK Unified Ideographs Extension H
        (0x2EBF0, 0x2EE5F),  # CJK Unified Ideographs Extension I
        (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
        (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
    ]

    return any(start <= code_point <= end for start, end in ranges)


def download_binary(url: str, out_path: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses

        with open(out_path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download file: {e}")


def main():
    # Create data directory if it doesn't exist
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)

    if len(sys.argv) <= 1:
        print("Please provide one or more Chinese characters as arguments.")
        print("Example: python main.py 想 好")
        return

    chars = sys.argv[1:]
    for char in chars:
        if not is_chinese_char(char):
            print(f"'{char}' is not a Chinese character.")
            continue

        print(f'Creating a worksheet for "{char}"...')
        unicode_value = ord(char)

        image_url = (
            f"https://www.strokeorder.com/assets/bishun/guide/{unicode_value}.png"
        )
        image_path = Path(out_dir) / f"{char}_stroke_order.png"
        download_binary(image_url, image_path)

        worksheet_url = f"https://www.strokeorder.com/assets/bishun/worksheets/pdf/2/{unicode_value}.pdf"
        worksheet_path = Path(out_dir) / f"{char}_worksheet.pdf"
        download_binary(worksheet_url, worksheet_path)

        # py = pinyin(char)


if __name__ == "__main__":
    main()
