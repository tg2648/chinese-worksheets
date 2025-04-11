# chinese-worksheets

Given Chinese characters, creates writing practice worksheets by combining the following:
- Practice worksheet from strokeorder.com
- Stroke order diagram from strokeorder.com
- Pinyin
- Top 3 English meanings (using data from https://www.mdbg.net/chinese/dictionary)

Sample usage:
```bash
python main.py -c 水 冰 -f chars.txt -n week1_study
```

This will create a file `week1_study.pdf` with practice worksheets for 水, 冰, and all characters contained in `chars.txt`
