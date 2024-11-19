import requests
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import re
import json
import random
import string
import time
from couchbase_config import get_cluster, get_bucket, get_scope, get_collection, upsert_document

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

def scrape_naver_article(article_id):
    """
    주어진 기사 ID를 사용하여 네이버 뉴스 기사를 스크래핑하고, 기사 정보를 추출하는 함수입니다.
    
    :param article_id: 스크래핑할 기사의 ID
    :return: 기사 제목, 날짜, 기자명, 본문, 원본 URL을 포함한 딕셔너리
    """
    # 스크래핑할 URL 설정
    url = f"https://n.news.naver.com/mnews/article/138/{article_id}"

    # HTTP 요청 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # URL로부터 기사 HTML 데이터를 가져옴
    print("===================================================================")
    print(f"Fetching article: {url}")
    response = requests.get(url, headers=headers)
    
    # 응답 상태 코드가 200(정상)이 아닐 경우 None 반환
    if response.status_code != 200:
        print(f"Failed to fetch article {url}, status code: {response.status_code}")
        return None
    
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # 기사 제목 추출
    title_tag = soup.find("h2", id="title_area")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
    print("title : ", title)
    
    # 기사 게시일 추출
    date_tag = soup.find("span", class_="media_end_head_info_datestamp_time _ARTICLE_DATE_TIME")
    date = date_tag['data-date-time'] if date_tag else "Unknown Date"

    # 기자명 추출
    reporter_tag = soup.find("em", class_="media_end_head_journalist_name")
    reporter = reporter_tag.get_text(strip=True) if reporter_tag else "Unknown Reporter"

    # 기사 본문 추출
    article_tag = soup.find("article", id="dic_area")
    content = article_tag.get_text(strip=True) if article_tag else "No Content"

    # 뉴스 ID 및 OID 추출 (좋아요/댓글 수 API 호출에 필요)
    match = re.search(r'/article/(\d+)/(\d+)', url)

    if not match:
        print("Could not find 'newsId' or 'oid' in the URL.")

    oid = match.group(1)
    news_id = match.group(2)

    # 좋아요 수 가져오기 (API 요청)
    like_url = f"https://news.like.naver.com/v1/search/contents?callback=&q=NEWS%5Bne_{oid}_{news_id}%5D"
    like_response = requests.get(like_url, headers=headers)
    
    if like_response.status_code == 200:
        # 응답이 JSON 형태인지 확인
        try:
            like_data = json.loads(like_response.text.strip('()'))  # JSONP 포맷에서 괄호 제거

            # contents 리스트와 reactions 리스트 존재 여부 확인
            if 'contents' in like_data and len(like_data['contents']) > 0:
                reactions = like_data['contents'][0].get('reactions', [])
                if len(reactions) > 0:
                    like_count = reactions[0].get('count', 0)
                else:
                    like_count = 0
            else:
                like_count = 0
        except json.JSONDecodeError:
            like_count = "Invalid JSON response for likes"
    else:
        like_count = 0

    # 댓글 수 가져오기 (API 요청)
    comment_url = f"https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=view_politics&pool=cbox5&lang=ko&country=KR&objectId=news{oid},{news_id}&categoryId=&pageSize=10&indexSize=10&groupId="
    comment_response = requests.get(comment_url, headers=headers)

    if comment_response.status_code == 200:
        # 응답이 JSON 형태인지 확인
        try:
            comment_data = json.loads(comment_response.text.strip('()'))  # JSONP 포맷에서 괄호 제거
            comment_count = comment_data['result']['count']['comment'] if 'result' in comment_data else 0
        except json.JSONDecodeError:
            comment_count = "Invalid JSON response for comments"
    else:
        comment_count = "Comment count not available"

    # 기사 정보 딕셔너리로 저장
    article_info = {
        "title": title,
        "date": date,
        "reporter": reporter,
        "content": content,
        "url": url,
        "like_count": like_count, 
        "comment_count": comment_count
    }

    # 스크래핑한 기사 정보 출력
    print(f"Scraped article: {title} by {reporter}")
    return article_info

def generate_vector_with_bedrock(text):
    titan_embeddings = TitanEmbeddings()
    embedding = titan_embeddings.get_embedding(text)
    return embedding

def connect_couchbase():
    # Couchbase 클러스터 연결
    cluster = get_cluster(DB_USERNAME, DB_PASSWORD, DB_CONN_STR)
    bucket = get_bucket(cluster, DB_BUCKET)
    scope = get_scope(bucket, DB_SCOPE)
    collection = get_collection(scope, DB_COLLECTION)
    return collection

def store_in_couchbase(collection, article_info):
    """
    스크래핑한 기사 정보를 Couchbase에 저장합니다.
    
    :param collection: 저장할 콜레션
    :param article_info: 저장할 기사 정보
    """

    # 고유한 키 생성 (예: "article_12345678")
    key = "article_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Bedrock API를 사용하여 기사 본문을 벡터화
    print("Bedrock API를 사용하여 기사 본문을 벡터화")
    title_vector = generate_vector_with_bedrock(article_info['title'])
    article_vector = generate_vector_with_bedrock(article_info['content'])
    
    # Couchbase에 저장할 데이터 준비
    value = {
        "title": article_info['title'],
        "content": article_info['content'],
        "author": article_info['reporter'],
        "date": article_info['date'],
        "url": article_info['url'],
        "like_count": article_info['like_count'],
        "comment_count": article_info['comment_count'],
        "article_vector": article_vector,
        "title_vector": title_vector,
        "vector_model": "OpenAI API"
    }
    
    # Couchbase에 문서 저장
    try:
        upsert_document(collection, key, value)
        print(f"Inserted article with key: {key}")
    except Exception as e:
        print(f"Failed to insert article with key: {key}. Error: {e}")

def main():
    """
    시작하는 기사 ID로부터 지정된 개수만큼 기사를 스크래핑하고 Couchbase에 저장합니다.
    """
    starting_article_id = 2179100  # 시작 기사 ID
    num_articles = 400  # 스크래핑할 기사 개수
    
    collection = connect_couchbase()

    # 시작 기사 ID로부터 순차적으로 스크래핑
    for i in range(num_articles):
        article_id = str(starting_article_id + i).zfill(10)  # 기사 ID를 10자리로 포맷팅
        article_info = scrape_naver_article(article_id)  # 기사 정보 스크래핑

        if article_info:
            store_in_couchbase(collection, article_info)  # 기사 정보를 Couchbase에 저장
        else:
            print(f"No article found for ID: {article_id}")

        time.sleep(1)  # 각 요청 사이에 1초 딜레이를 주어 서버 부하를 방지

# 메인 함수 실행
if __name__ == "__main__":
    main()
