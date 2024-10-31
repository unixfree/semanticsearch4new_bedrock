## RAG Demo using Couchbase, Langchain, and OpenAI

This is a demo app built to search for recommedation news article that with crawling data from Naver news using the vector search capabilities of Couchbase to augment the OpenAI results in a Embedding model.

The demo will run for both self-managed OnPrem 7.6+ Couchbase deployments and also clould based 7.6+ Capella deployments

### Prerequisites 

You will need a database user with login credentials to your Couchbase cluster and an OpenAI API bearer key for this Linux demo

You will probably want to create and activate a virtual environment using the standard library's virtual environment tool, *venv*, and install local python packages.

- https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

Quick tips on Python virtual environments (please folow this unless you are an expert). 

- Create and activate a virtual environment in a new empty demo directory<br><br>
`mkdir MYDEMO`<br>
`cd MYDEMO`<br>
`python3 -m venv .venv`<br>
`source .venv/bin/activate`

- The above works for *bash* or *zsh*, however you would use `. .venv/bin/activate` if you are using *sh*

- Then, when all done with this demo, you can deactivate it.<br><br>
`deactivate`

- Just in case you typed 'deactive' (you do this deactive when you're done with the full demo) - just run the source command again to reactivate the virtual Python environment:<br><br>
`source .venv/bin/activate`

- The above works for *bash* or *zsh*, however you would use `. .venv/bin/activate` if you are using *sh*

- Now download this git repo and cd into it.<br><br>
`git clone https://github.com/unixfree/semanticsearch4news.git`<br>
`cd semanticsearch4news`

### How to Configure

1. Install dependencies

  `pip install -r requirements.txt`

2. Required environment variables that you must configure in env_temp
  ```
  EMBEDDING_MODEL=text-embedding-ada-002
  DB_CONN_STR="<Connect Sting of your Couchbase server>"
  DB_USERNAME="<username_for_couchbase_cluster>"
  DB_PASSWORD="<password_for_couchbase_cluster>"
  DB_BUCKET="<bucket_for_couchbase_cluster>"
  DB_SCOPE="<scope_for_couchbase_cluster>"
  DB_COLLECTION="<collection_for_couchbase_cluster>"
  INDEX_NAME="<index name for vector search in FTS>"
  ```

3. Copy the template environment template

  `cp env_temp .env`

- This example always uses and assumes secure connections to your couchbase instance, you should verify your firewall will pass at least 18091 (Management port), 18094 (Search service), 11210 / 11207 (Data service)

4. Create FTS Index from "article-index.json" at Couchbase or Capella 
 > Data Tools - Search
  - Advanced Mode
  - Import from File < `article-index.json` 
  - Select "Bucket" and "Scope"
  - Create Index

5. Run Cralwing, Vectorize and Load to Couchbase 

  `python3 import_news.py`

6. Run semantic Search

  `python3 search_vector.py'
   Enter text to vector search in article : 김정숙  
   Enter text to test search in title : 청문회

7. Result Samples

FTS Vector Search results:
ID: article_Wrr2pIKT, Score: 0.7816184163093567
Title: [인사] 한국연구재단
Date: 2024-08-05 09:36:08
Url: https://n.news.naver.com/mnews/article/138/0002179152
--------
ID: article_6srcs81Y, Score: 0.7801542282104492
Title: 청문회 D-3...'출근길 말말말'로 본 유상임 과기정통부 후보자는
Date: 2024-08-05 17:16:19
Url: https://n.news.naver.com/mnews/article/138/0002179231
--------
ID: article_T4BClMGY, Score: 0.7796298861503601
Title: 정부, 이공계 대학원생 인건비 제도개선한다
Date: 2024-08-05 14:00:15
Url: https://n.news.naver.com/mnews/article/138/0002179194
--------
ID: article_WdDR5VgQ, Score: 0.776661217212677
Title: “더위 피했더니 사람 너무많네”…캐논, ‘사이니지 혼잡도 안내’ 공간관리 ‘척척’
Date: 2024-08-05 07:01:10
Url: https://n.news.naver.com/mnews/article/138/0002179138
--------
ID: article_5JD050s0, Score: 0.7757707238197327
Title: [날씨] 월요일 체감온도 35도 '사우나 폭염'…전국 곳곳 소나기
Date: 2024-08-05 09:22:09
Url: https://n.news.naver.com/mnews/article/138/0002179146
--------

SQL++ Hybrid Search results: QueryResult:<couchbase.n1ql.N1QLRequest object at 0x109d2fc50>
Score: 1.7373759177373305
Title: 청문회 D-3...'출근길 말말말'로 본 유상임 과기정통부 후보자는
Date: 2024-08-05 17:16:19
Author: 채성오 기자
Like Count: 3
Url: https://n.news.naver.com/mnews/article/138/0002179231
--------

### Finished

When you are all done with this demo, you should deactivate the python virtual environment (you can always reactivate it later).<br><br>
`deactivate`
