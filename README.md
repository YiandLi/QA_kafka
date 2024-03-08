### Step1 : Get DATA

- Download : https://dokumen.pub/qdownload
- Format Transfer : https://cloudconvert.com/pdf-to-doc

采集的数据见 `epubs` ，最终处理后的版本为 `.json` 文件

<span style="color:red">难点：如何收集，解析数据，整理数据 ？ 数据质量决定了检索。</span>





### Step 2 : Create DB
[get_chunks.py](get_chunks.py)
1. 创建数据库：create_db_from_json
   1. 读取数据 `create_db_from_json`
   2. MinHash - LSH 数据去重 `LSH_dedup` > [LSHHash.py](LSHHash.py)
   3. embedding : `BAAI/bge-large-en-v1.5`
2. 读取数据库
   1. `FAISS.load_local`
   2. 切分用户回复 -> `user_response`
   3. 从 db 中检索得到相关文本 -> `docs`
   4. 组织 context，使用 llm 判别：`llama.cpp` + `"qwen1_5-4b-chat-q6_k.gguf"`

速度：
```text
llama_print_timings:        load time =   33183.27 ms
llama_print_timings:      sample time =       1.06 ms /     2 runs   (    0.53 ms per token,  1890.36 tokens per second)
llama_print_timings: prompt eval time =   27894.66 ms /   342 tokens (   81.56 ms per token,    12.26 tokens per second)
llama_print_timings:        eval time =    1778.37 ms /     1 runs   ( 1778.37 ms per token,     0.56 tokens per second)
llama_print_timings:       total time =   29713.67 ms /   343 tokens
```
流程输出：
```
question: 
	What is the difference between Event Time and Processing Time in the context of Kafka?

user repsonse chunk: 
	Event Time: Refers to the time at which an event actually occurred or was generated.
    Event Time: Typically associated with the timestamp embedded within the data of each event.

context retrieved: 
	Topic: Stream Processing What Is Stream Processing?
	It is worth noting that neither the definition of event streams nor the attributes we later listed say anything about the data contained in the events or the number of events per second. The data differs from system to system — events can be tiny (sometimes only a few bytes) or very large (XML messages with many headers); they can also be completely unstructured, key-value pairs, semi-structured JSON, or structured Avro or Protobuf messages. While it is often assumed that data streams are “big data” and involve millions of events per second, the same techniques we’ll discuss apply equally well (and often better) to smaller streams of events with only a few events per second or minute.
	Topic: Stream Processing Stream-Processing Concepts Time
	Stream-processing systems typically refer to the following notions of time:
	Topic: Stream Processing What Is Stream Processing?
	Let’s start at the beginning: What is a data stream (also called an event stream or streaming data)? First and foremost, a data stream is an abstraction representing an unbounded dataset. Unbounded means infinite and ever growing. The dataset is unbounded because over time, new records keep arriving. This definition is used by Google, Amazon, and pretty much everyone else.

Answer: 
	right
```
