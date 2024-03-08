import json
import re
import pandas as pd
from llama_cpp import Llama
from tqdm import tqdm
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from LSHHash import LSH_dedup


def create_db_from_csv(file_path: str, embedding):
    df = pd.read_csv(file_path).drop_duplicates(subset=['sample_answer'])
    field_counts_dict = df['field'].value_counts().to_dict()
    field_tech_counts_dict = (df['field'] + '-' + df['tech_keywords']).value_counts().to_dict()
    
    print(f"field count is \n {field_counts_dict}")
    print(f"field_tech count is \n {field_tech_counts_dict}")
    
    # 假设你的DataFrame是df
    _documents = []
    for index, row in tqdm(df.iterrows(), desc=file_path):
        splits = [i.strip() for i in row.sample_answer.split("\n") if i.strip()]
        splits = [re.sub(r'\d+\.', '', i).strip() for i in splits]
        _documents += [Document(page_content=i, metadata=dict(file_path=file_path,
                                                              field=row.field,
                                                              tech_keywords=row.tech_keywords,
                                                              question=row.question)) for i in splits]
    
    # 文档去重复
    print(f"Get {len(_documents)} sub text from document {file_path} .")
    _documents = LSH_dedup(_documents, threshold=0.8, num_perm=200, n_gram=2)
    print(f"After LSH de-duplication : get {len(_documents)} sub text from document {file_path} .")
    db = FAISS.from_documents(_documents, embedding)
    return db


def create_db_from_json(file_path: str, embedding):
    data = json.load(open(file_path, "r"))
    _documents = []
    for k, v in data.items():
        prefix = k.replace("<sec>", " ")
        prefix = re.sub(r'Chapter \d+\.', ' ', prefix).strip()
        _documents += [Document(page_content=f"Topic: {prefix}\n{vv}",
                                metadata=dict(file_path=file_path,
                                              field="kafka",
                                              key=k,
                                              idx=idx))
                       for idx, vv in enumerate(v)]
    
    print(f"Get {len(_documents)} sub text from document {file_path} .")
    _documents = LSH_dedup(_documents, threshold=0.8, num_perm=200, n_gram=2)
    print(f"After LSH de-duplication : get {len(_documents)} sub text from document {file_path} .")
    db = FAISS.from_documents(_documents, embedding)
    return db


def generate(model, question, context, answer):
    messages = [
        {"role": "system",
         "content": f"For this task, you're going to evaluate a user's response to a computer science interview question. "
                    "\nYour evaluation should be based solely on the provided context. "
                    "If the response is correct, provide 'right' as the value, if it's incorrect, provide 'wrong', "
                    "and if you're unable to make a decision, provide 'don't know'."
                    " Remember, your assessment should be based only on the given context and only from right / wrong / don't know."
                    f"\n\ncontext : {context}" \
                    f"\n\nquestion : {question}"},
        {"role": "user", "content": answer}
    ]
    
    # messages = [
    #     {"role": "system",
    #      "content": f"Based on context, please answer users' question."},
    #     {"role": "user", "content": f"\n\ncontext : {context}"
    #                                 f"{answer}"}
    # ]
    
    output = model.create_chat_completion(
        messages=messages,
        max_tokens=10,
        # response_format={"type": "json_object",
        #                  "schema": {
        #                      "type": "object",
        #                      "properties": {"报告名称": {"type": "string"},
        #                                     "发布机构": {"type": "string"},
        #                                     "作者列表": {"type": "List"},
        #                                     "报告时间": {"type": "string"},
        #                                     "涉及行业": {"type": "string"}},
        #                      "required": ["team_name"],
        #                  },
        #                  }
    )
    output_txt = output["choices"][0]['message']['content']
    return output_txt


if __name__ == "__main__":
    
    emb_model_path = "BAAI/bge-large-en-v1.5"  # "BAAI/bge-base-en"  # "BAAI/bge-large-en-v1.5"
    instruction = "Represent this sentence for searching relevant passages: "
    file_path = "data/kafka.json"
    save_path = "my_faiss_db"
    model_path = "qwen1_5-4b-chat-q6_k.gguf"
    
    embedding = HuggingFaceBgeEmbeddings(
        model_name=emb_model_path,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
        query_instruction=instruction
        # https://python.langchain.com/docs/integrations/text_embedding/bge_huggingface
    )
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    
    # TODO：Create
    # db = create_db_from_json(file_path, embedding)
    # db.save_local(save_path)
    
    # TODO：QUERY
    question = "What is the difference between Event Time and Processing Time in the context of Kafka?"
    user_response = """
    Event Time: Refers to the time at which an event actually occurred or was generated.
    Event Time: Typically associated with the timestamp embedded within the data of each event.
    """
    
    llm = Llama(model_path=model_path)
    
    # Split Inputs
    db = FAISS.load_local(save_path, embedding.embed_query)
    user_response = [i.page_content for i in text_splitter.create_documents([user_response])]
    for response in user_response:
        docs = db.similarity_search_with_score(response,
                                               k=3
                                               # fetch_k=10,
                                               # filter=dict(field="database")
                                               )
        
        # LLM Generate
        
        context = "\n".join([i[0].page_content for i in docs])
        llm_response = generate(llm, question, context, response)
        print(f"question: \n\t{question}\n\n"
              f"user repsonse chunk: \n\t{response}\n\n"
              f"context retrieved: \n\t{context}\n\n"
              f"Answer: \n\t{llm_response}")
    
    print(docs)
    # https://python.langchain.com/docs/integrations/vectorstores/faiss
