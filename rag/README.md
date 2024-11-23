### Run milvus
```
podman run -it \
        --name milvus-standalone \
        --security-opt seccomp:unconfined \
        -e ETCD_USE_EMBED=true \
        -e ETCD_CONFIG_PATH=/milvus/configs/embedEtcd.yaml \
        -e COMMON_STORAGETYPE=local \
        -v $(pwd)/volumes/milvus:/var/lib/milvus \
        -v $(pwd)/embedEtcd.yaml:/milvus/configs/embedEtcd.yaml \
        -p 19530:19530 \
        -p 9091:9091 \
        -p 2379:2379 \
        --health-cmd="curl -f http://localhost:9091/healthz" \
        --health-interval=30s \
        --health-start-period=90s \
        --health-timeout=20s \
        --health-retries=3 \
        milvusdb/milvus:master-20240426-bed6363f \
        milvus run standalone  1> /dev/null
```
### Serve RAG API and Run RAG manager tool
```
uvicorn rag_app:app --host 0.0.0.0 --port 8000
streamlit run rag/rag_UI.py
```
### Run mistral model
* Download Ollama and run ollama pull mistral
* Run ollama serve

### Run discovery bot
```
streamlit run rag/chat_with_rag.py
```

