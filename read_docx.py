import docx
import json

"""
https://dokumen.pub/qdownload
https://cloudconvert.com/pdf-to-doc
"""


def extract_sections(file_path):
    doc = docx.Document(file_path)
    paragraphs = doc.paragraphs
    res = {}
    last_level = 0
    last_titles = []
    current_content = []
    
    for paragraph in paragraphs:
        
        if paragraph.style.name.startswith('Heading'):
            
            # 获取新标题和级别
            current_title = paragraph.text.strip()
            current_level = int(paragraph.style.name[7:])
            print(" " * current_level, current_title, current_level)
            
            # 如果当前不是子节点了，就要更新前驱节点了
            if not current_level > last_level:
                last_titles = last_titles[:current_level - 1]
            
            # 然后更新自己的节点
            last_titles += ["" for _ in range(current_level - last_level - 1)]
            last_titles += [current_title]
            
            if current_content:
                res[f"<sec>".join(last_titles)] = current_content
            current_content = []
            last_level = current_level
        
        else:
            if len(paragraph.text.strip()) > 10:
                current_content.append(paragraph.text.strip())
    
    return res


# 使用示例
file_path = 'epubs/Kafka_in_Action.doc'
sections = extract_sections(file_path)
json.dump(sections, open("epubs/effective-Kafka_in_Action.json", "w"), indent=2)

# # 打印结果
# for title, content in sections.items():
#     print('标题：{}'.format(title))
#     print('内容：{}'.format(content))
#     print('-----------------------------------')
