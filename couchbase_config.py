from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, ClusterTimeoutOptions, QueryOptions, UpsertOptions, RemoveOptions
from datetime import timedelta

def get_cluster(username, password, cluster_ip):
    # 인증 및 타임아웃 옵션 설정
    auth = PasswordAuthenticator(username, password)
    timeout_options = ClusterTimeoutOptions(kv_timeout=timedelta(seconds=50), query_timeout=timedelta(seconds=50))
    options = ClusterOptions(auth, timeout_options=timeout_options)

    # 클러스터 연결
    cluster = Cluster(f'{cluster_ip}', options)
    cluster.wait_until_ready(timedelta(seconds=10))
    
    return cluster

def get_bucket(cluster, bucket_name):
    return cluster.bucket(bucket_name)

def get_scope(bucket, scope_name):
    return bucket.scope(scope_name)

def get_collection(scope, coll_name):
    return scope.collection(coll_name)

def execute_n1ql_query(cluster, query, params, bucket_name, scope_name):
    # 쿼리 실행
    query_options = QueryOptions(named_parameters=params, query_context=f'`{bucket_name}`.`{scope_name}`')
    result = cluster.query(query, query_options)
    
    return result

def get_document(collection, key):
    return collection.get(key)

def insert_document(collection, key, value):
    return collection.insert(key, value)

def upsert_document(collection, key, value):
    return collection.upsert(key, value)

def remove_document(collection, key):
    return collection.remove(key)
