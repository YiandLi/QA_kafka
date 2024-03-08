# -*- coding: utf-8 -*-
"""
PDF to epub ::: https://cloudconvert.com/pdf-to-epub
"""
import json
from collections import defaultdict

import ebooklib
import tqdm
from bs4 import BeautifulSoup
from ebooklib import epub


def parse_section(section, last_title=""):
    """
    # 内部结构为 section > div > section > div > ....
    # 这里需要将 section label（data-pdf-bookmark） 全部累加起来，然后获取其中的内容
    """
    children = section.find('section')
    if children:
        return parse_section(children, last_title + "<sec>" + section.get("data-pdf-bookmark"))
    else:
        try:
            return {last_title + "<sec>" + section.get("data-pdf-bookmark"):
                        [i.text.strip() for i in section.select('section > div > p')]}
        except Exception as e:
            print(e)
            return None


def merge_to_nested_dict(sub_dict: dict, target_dict: dict):
    for k, v in sub_dict.items():
        target_dict[k] += v
    return target_dict


def exact_p_tag(input_path, save_path):
    book = epub.read_epub(input_path)
    nested_total_dicts = defaultdict(list)  # 存储章节内容的字典
    
    for item in tqdm.tqdm(book.get_items()):
        # 提取书中的文本内容
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # epub中的内容是html格式，使用BeautifulSoup可以完美解析
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            mother_section = soup.select('body > section')
            for section in mother_section:
                sub_content = parse_section(section)
                if sub_content:
                    merge_to_nested_dict(sub_content, nested_total_dicts)
    
    json.dump(nested_total_dicts, open(save_path, "w"), ensure_ascii=False)
    return nested_total_dicts


# 批量处理文件
book_path = "epubs/kafka-the-definitive-guide.epub"
save_path = "epubs/kafka-the-definitive-guide.json"
exact_p_tag(book_path, save_path)
# print(path)
