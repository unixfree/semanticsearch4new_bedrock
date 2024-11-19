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
`git clone https://github.com/unixfree/semanticsearch4news_bedrock.git`<br>
`cd semanticsearch4news_bedrock`

### How to Configure

1. Install dependencies

  `pip install -r requirements.txt`

2. Required environment variables that you must configure in env_temp
  ```
  EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
  DB_CONN_STR=couchbase://localhost
  DB_USERNAME=Administrator
  DB_PASSWORD=password
  DB_BUCKET=travel-sample
  DB_SCOPE=semantic
  DB_COLLECTION=article
  INDEX_NAME=arcticle_idx
  ```

3. Copy the template environment template

  `cp env_temp .env`

- This example always uses and assumes secure connections to your couchbase instance, you should verify your firewall will pass at least 18091 (Management port), 18094 (Search service), 11210 / 11207 (Data service)

4. Create Bucket/Scope/Collection at Couchbase or Capella 

5. Create FTS Index from "article_idx.json" at Couchbase or Capella 
 > Data Tools - Search
  - Advanced Mode
  - Import from File < `article_idx.json` 
  - Select "Bucket" and "Scope"
  - Create Index

6. Run Cralwing, Vectorize and Load to Couchbase 

  `python3 import_news.py`

7. Run semantic Search

  `python3 search_vector.py` <br>
  
   Enter text to vector search in article : 김정숙  <br>
   Enter text to test search in title : 청문회

### Finished

When you are all done with this demo, you should deactivate the python virtual environment (you can always reactivate it later).<br><br>
`deactivate`
