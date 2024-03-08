import re
from typing import List

import jieba
from datasketch import MinHash, MinHashLSH
from tqdm import tqdm


def generate_ngrams(tokens, n_gram):
    ngrams = []
    for i in range(len(tokens) - n_gram + 1):
        ngram = ' '.join(tokens[i:i + n_gram])
        ngrams.append(ngram)
    return ngrams


# 此函数用于分词
def split_word(sentence, n_gram):
    regex = re.compile("[^\u4e00-\u9fa5a-zA-Z]")
    # 使用正则表达式将匹配的字符替换为空格，然后进行分词
    tokens = jieba.lcut(re.sub(regex, ' ', sentence))
    res = [word for word in tokens if word.strip()]
    res = generate_ngrams(res, n_gram)
    return res


def LSH_dedup(documents: List,
              threshold=0.8,  # 相似度阈值
              num_perm=200,  # MinHash的排列次数
              n_gram=2
              ):
    # 初始化LSH对象
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    
    # 为每个问答回答创建MinHash并加入LSH
    ttrange = tqdm(documents, desc="Hashing doc", total=len(documents))
    for idx, doc in enumerate(ttrange):
        words = split_word(doc.page_content, n_gram)
        minhash = MinHash(num_perm=num_perm)
        for word in words:
            minhash.update(word.encode('utf-8'))
        lsh.insert("qa_pair_{}".format(idx), minhash)
    
    # 查询并去重
    unique_docs = []
    ttrange = tqdm(documents, "De-Duplicate doc")
    for idx, doc in enumerate(ttrange):
        if "qa_pair_{}".format(idx) in lsh.keys._dict.keys():
            words = split_word(doc.page_content, n_gram)
            minhash = MinHash(num_perm=num_perm)
            for word in words:
                minhash.update(word.encode('utf-8'))
            # 查询相似问答回答
            result = lsh.query(minhash)
            # 保存相似的问答回答
            similar_docs = [documents[int(doc_id.split('_')[-1])] for doc_id in result]
            # 如果没有相似的文档，则直接将当前文档添加到唯一项列表中
            if similar_docs:
                # 选择一个作为唯一项
                unique_doc = max(similar_docs, key=lambda x: len(x.page_content))
                # 将唯一项添加到列表中
                unique_docs.append(unique_doc)
                # 移除其他相似项
                for doc_id in result:
                    lsh.remove(doc_id)
            else:
                unique_docs.append(doc)
    
    return unique_docs
