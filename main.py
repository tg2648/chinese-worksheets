import argparse
import os
import random
import time
from pathlib import Path

import pymupdf
import requests
from cedict_utils.cedict import CedictEntry, CedictParser
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


def download_files(char: str, out_dir: str, no_dl: bool) -> tuple[str, str]:
    """
    Download the stroke order image and worksheet PDF for a given Chinese character.

    Args:
        char (str): The Chinese character to download files for
        out_dir (str): The directory to save the downloaded files
    """
    unicode_value = ord(char)

    image_url = f"https://www.strokeorder.com/assets/bishun/guide/{unicode_value}.png"
    image_path = Path(out_dir) / f"{char}_stroke_order.png"
    if no_dl:
        print("...Skipping download of stroke order image")
    else:
        print("...Downloading stroke order image")
        time.sleep(random.uniform(0.1, 1))  # Simulate a delay for the download
        download_binary(image_url, image_path)

    worksheet_url = f"https://www.strokeorder.com/assets/bishun/worksheets/pdf/2/{unicode_value}.pdf"
    worksheet_path = Path(out_dir) / f"{char}_raw_worksheet.pdf"
    if no_dl:
        print("...Skipping download of raw worksheet")
    else:
        print("...Downloading raw worksheet")
        time.sleep(random.uniform(0.1, 1))  # Simulate a delay for the download
        download_binary(worksheet_url, worksheet_path)

    return image_path, worksheet_path


def add_text_to_pdf(input_pdf_path: str, text: str, rect: tuple[int, int, int, int], output_pdf_path: str):
    """
    Add text to a PDF file.

    Args:
        input_pdf_path (str): Path to the input PDF file
        text (str): Text to add to the PDF
        output_pdf_path (str): Path to save the modified PDF
    """
    doc = pymupdf.open(input_pdf_path)
    page = doc[0]
    page.insert_htmlbox(rect, text)

    if input_pdf_path == output_pdf_path:
        doc.save(output_pdf_path, incremental=True, encryption=0)
    else:
        doc.save(output_pdf_path, deflate=True, garbage=3, use_objstms=1)
    doc.close()


def add_image_to_pdf(input_pdf_path: str, image_path: str, output_pdf_path: str):
    doc = pymupdf.open(input_pdf_path)
    page = doc[0]
    page_rect = page.bound()
    # Offset from the top right corner
    image_rect = (page_rect.x1 - 125, 10, page_rect.x1 - 10, 125)
    page.insert_image(image_rect, filename=image_path)

    if input_pdf_path == output_pdf_path:
        doc.save(output_pdf_path, incremental=True, encryption=0)
    else:
        doc.save(output_pdf_path, deflate=True, garbage=3, use_objstms=1)
    doc.close()


def combine_worksheets(input_pdf_paths: list[str], output_pdf_path: str):
    """
    Combine multiple worksheets into one PDF.
    """
    doc = pymupdf.open()

    for path in input_pdf_paths:
        with pymupdf.open(path) as temp_doc:
            doc.insert_pdf(temp_doc)

    doc.save(output_pdf_path, deflate=True, garbage=3, use_objstms=1)
    doc.close()


def process_raw_worksheet(
    raw_worksheet_path: str,
    pinyin: str,
    stroke_order_image_path: str,
    definitions: list[str],
    final_worksheet_path: str,
):
    """
    Process the raw worksheet PDF by adding pinyin and stroke order image.
    """
    print("...Adding pinyin to worksheet")
    add_text_to_pdf(
        input_pdf_path=raw_worksheet_path,
        text=pinyin,
        rect=(50, 50, 200, 500),
        output_pdf_path=final_worksheet_path,
    )

    print("...Adding definitions to worksheet")
    definitions_formatted = "<br>".join(definitions)
    add_text_to_pdf(
        input_pdf_path=final_worksheet_path,
        text=definitions_formatted,
        rect=(50, 495, 800, 800),
        output_pdf_path=final_worksheet_path,
    )

    print("...Adding stroke order image")
    add_image_to_pdf(
        input_pdf_path=final_worksheet_path,
        image_path=stroke_order_image_path,
        output_pdf_path=final_worksheet_path,
    )


def read_characters_from_file(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        characters = f.read().strip().split()
    return characters


def lookup_chinese(word, entries: list[CedictEntry]) -> list[str]:
    """
    Returns the first three definitions for a given Chinese word.
    """
    results: list[str] = []
    for entry in entries:
        if entry.traditional == word or entry.simplified == word:
            results.extend(entry.meanings)

    # Filter results
    filtered_results = []
    for result in results:
        if result.startswith("surname"):
            continue
        if "variant of" in result:
            continue
        if "CL:" in result:
            continue
        if "(slang)" in result:
            continue

        filtered_results.append(result)

    return filtered_results[:3]


def main():
    # Create data directory if it doesn't exist
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--characters", nargs="*", default=[], help="Chinese characters to process")
    parser.add_argument(
        "-f", "--files", nargs="*", default=[], help="Chinese characters to process from one or more file"
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="combined_worksheet",
        help="Name of the final worksheet",
    )
    parser.add_argument(
        "--no-dl", action="store_true", help="Skip downloading files (if individual files already exist)"
    )
    args = parser.parse_args()

    # Parse the dictionary file (you need to download it first)
    parser = CedictParser(file_path="data/cedict_1_0_ts_utf-8_mdbg.txt")
    entries: list[CedictEntry] = parser.parse()

    characters = []
    for file in args.files:
        characters.extend(read_characters_from_file(file))
    characters.extend(args.characters)

    if not characters:
        print("No characters provided. Exiting.")
        return

    worksheet_paths = []
    for char in set(characters):
        if not is_chinese_char(char):
            print(f"'{char}' is not a Chinese character.")
            continue

        print(f'Processing "{char}":')
        final_worksheet_path = Path(out_dir) / f"worksheet_{char}.pdf"
        worksheet_paths.append(final_worksheet_path)

        pinyin_str = " ".join([p[0] for p in pinyin(char)])
        definitions = lookup_chinese(char, entries)

        image_path, raw_worksheet_path = download_files(char, out_dir, args.no_dl)
        process_raw_worksheet(raw_worksheet_path, pinyin_str, image_path, definitions, final_worksheet_path)

    print("Combining all worksheets into one...")
    combine_worksheets(worksheet_paths, Path(out_dir) / f"{args.name}.pdf")


if __name__ == "__main__":
    main()
