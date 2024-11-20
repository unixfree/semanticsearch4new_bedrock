import requests
from dotenv import load_dotenv
import os
import json
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, SearchOptions
from couchbase.exceptions import CouchbaseException
import couchbase.search as search
from couchbase.vector_search import VectorQuery, VectorSearch
import boto3
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_community.chat_models import BedrockChat

load_dotenv()

DB_CONN_STR = os.getenv("DB_CONN_STR")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_BUCKET = os.getenv("DB_BUCKET")
DB_SCOPE = os.getenv("DB_SCOPE")
DB_COLLECTION = os.getenv("DB_COLLECTION")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Couchbase 클러스터 연결 설정
auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
cluster = Cluster.connect(DB_CONN_STR, ClusterOptions(auth))
bucket = cluster.bucket(DB_BUCKET)
scope = bucket.scope(DB_SCOPE)
collection = scope.collection(DB_COLLECTION)

class TitanEmbeddings:
    def __init__(self, model_id=EMBEDDING_MODEL):
        self.bedrock = boto3.client(service_name='bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id
        self.accept = "application/json"
        self.content_type = "application/json"

    def get_embedding(self, text, dimensions=1024, normalize=True):
        body = json.dumps({
            "inputText": text,
            "dimensions": dimensions,
            "normalize": normalize
        })

        response = self.bedrock.invoke_model(
            body=body,
            modelId=self.model_id,
            accept=self.accept,
            contentType=self.content_type
        )

        response_body = json.loads(response.get('body').read())
        return response_body['embedding']

# 텍스트를 벡터로 변환하는 함수 (Bedrock API 사용)
def generate_vector_with_bedrock(text):
    titan_embeddings = TitanEmbeddings()
    embedding = titan_embeddings.get_embedding(text)
    return embedding

# 벡터 검색 수행 함수 (FTS)
def vector_search_with_fts(cluster, scope, query_vector):
    """
    Couchbase 벡터 검색을 수행합니다.
    :param cluster: Couchbase 클러스터
    :param scope: Couchbase 스코프
    :param query_vector: 검색할 벡터
    """
    try:
        # 벡터 검색 쿼리 설정
        vector_search = VectorSearch.from_vector_query(VectorQuery('article_vector', query_vector, num_candidates=5))
        
        request = search.SearchRequest.create(vector_search)

        # 검색 수행
        result = scope.search('article_idx', request)

        print(f"FTS Vector Search results:")
        for row in result.rows():
            print(f"ID: {row.id}, Score: {row.score}")
            doc = collection.get(row.id)
            doc_content = doc.content_as[dict]  # 문서를 사전 형식으로 변환
            print(f"Title: {doc_content['title']}")
            print(f"Date: {doc_content['date']}")
            print(f"Url: {doc_content['url']}")
            print("--------")

    except CouchbaseException as e:
        print(f"Search failed: {e}")

# SQL++ 하이브리드 검색 수행 함수
def hybrid_vector_search_with_sql(cluster, article_vector, title_vector, title_text):
    """
    Couchbase SQL++, 자연어검색, 벡터 검색을 결합하여 검색을 수행합니다.
    :param cluster: Couchbase 클러스터
    :param article_vector: 검색할기사 내용 벡터
    :param title_vector: 검색할기사 제목 벡터
    :param title_text: 검색할 단어
    """
    try:
        # N1QL을 사용한 KNN 및 필터 검색
        query = f"""
        SELECT title, date, author, url, like_count, SEARCH_SCORE() AS score
        FROM `travel-sample`.semantic.article AS t1
        WHERE author like "%기자"
        AND like_count >= 1
	AND SEARCH(t1, {{
                "query": {{"match": "{title_text}","field":"title"}}
            }})
        AND SEARCH(t1, {{
                "query": {{"match_none": {{}}}},
                "knn": [{{"field": "article_vector", "vector": {article_vector}, "k": 5}}]
            }})
        ORDER BY score,date DESC
        """
        
        # 쿼리 실행
        result = cluster.query(query)
        
        # 결과 출력
        print("")
        print(f"SQL++ Hybrid Search results:", result)
        for row in result:
            print(f"Score: {row['score']}")
            print(f"Title: {row['title']}")
            print(f"Date: {row['date']}")
            print(f"Author: {row['author']}")
            print(f"Like Count: {row['like_count']}")
            print(f"Url: {row['url']}")
            print("--------")
    except CouchbaseException as e:
        print(f"Hybrid search failed: {e}")

# 메인 함수
def main():

    # 검색할 텍스트 입력
    article_text = input("Enter text to vector search in article : ")
    title_text = input("Enter text to test search in title : ")

    # 텍스트를 벡터로 변환
    article_vector = generate_vector_with_bedrock(article_text)
    title_vector = generate_vector_with_bedrock(title_text)

    if not article_vector:
        print("No vector generated, exiting search.")
        return

    # FTS 벡터 검색 수행
    vector_search_with_fts(cluster, scope, article_vector)

    # SQL++ 하이브리드 검색 수행
    hybrid_vector_search_with_sql(cluster, article_vector, title_vector, title_text)

# 메인 함수 실행
if __name__ == "__main__":
    main()
