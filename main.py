import os
import sys
from pathlib import Path

import pymupdf
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


def download_files(char: str, out_dir: str) -> tuple[str, str]:
    """
    Download the stroke order image and worksheet PDF for a given Chinese character.

    Args:
        char (str): The Chinese character to download files for
        out_dir (str): The directory to save the downloaded files
    """
    unicode_value = ord(char)

    image_url = f"https://www.strokeorder.com/assets/bishun/guide/{unicode_value}.png"
    image_path = Path(out_dir) / f"{char}_stroke_order.png"
    print(f'Downloading stroke order image for "{char}"...')
    # download_binary(image_url, image_path)

    worksheet_url = f"https://www.strokeorder.com/assets/bishun/worksheets/pdf/2/{unicode_value}.pdf"
    worksheet_path = Path(out_dir) / f"{char}_raw_worksheet.pdf"
    print(f'Downloading raw worksheet for "{char}"...')
    # download_binary(worksheet_url, worksheet_path)

    return image_path, worksheet_path


def add_text_to_pdf(input_pdf_path: str, text: str, output_pdf_path: str):
    """
    Add text to a PDF file.

    Args:
        input_pdf_path (str): Path to the input PDF file
        text (str): Text to add to the PDF
        output_pdf_path (str): Path to save the modified PDF
    """
    doc = pymupdf.open(input_pdf_path)
    page = doc[0]
    rect = (50, 50, 200, 500)
    page.insert_htmlbox(rect, text)

    doc.save(output_pdf_path)


def add_image_to_pdf(pdf_path: str, image_path: str):
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    page_rect = page.bound()
    # Offset from the top right corner
    image_rect = (page_rect.x1 - 125, 10, page_rect.x1 - 10, 125)
    page.insert_image(image_rect, filename=image_path)

    doc.save(pdf_path, incremental=True, encryption=0)
    doc.close()


def combines_files(
    char: str,
    stroke_order_image_path: str,
    raw_worksheet_path: str,
    out_dir: str,
):
    pinyin_str = " ".join([p[0] for p in pinyin(char)])

    final_worksheet_path = Path(out_dir) / f"worksheet_{char}.pdf"
    print(f'Adding pinyin to worksheet for "{char}"...')
    add_text_to_pdf(raw_worksheet_path, pinyin_str, final_worksheet_path)
    print(f'Adding stroke order image to worksheet for "{char}"...')
    add_image_to_pdf(final_worksheet_path, stroke_order_image_path)


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

        image_path, raw_worksheet_path = download_files(char, out_dir)
        combines_files(char, image_path, raw_worksheet_path, out_dir)
        print(f'Created a worksheet for "{char}"...')


if __name__ == "__main__":
    main()
