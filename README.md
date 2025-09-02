# Elasticsearch MCP Server for 7.x

The official MCP server for Elasticsearch does **not support Elasticsearch 7.x**.  
Since many users and industries still use Elasticsearch 7.x—especially the **7.10.2 OSS** version.  
This project provides a workable MCP server code for Elasticsearch 7.x.

---

## Installation and Run

```
pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir

export ELASTICSEARCH_URL="******"
export ELASTICSEARCH_USERNAME="admin"
export ELASTICSEARCH_PASSWORD="******"

python -m mcp_server_elasticsearch --transport stream --host 0.0.0.0 --port 8080
```

## Sample MCP Server output:

```
2025-09-02 15:50:56,175 - mcp_server_elasticsearch - INFO - Starting MCP server...
2025-09-02 15:50:56,826 - es_client.client - INFO - [BASIC AUTH] 使用基本认证: admin
2025-09-02 15:50:56,835 - elasticsearch - INFO - GET http://******:9200/ [status:200 request:0.007s]
2025-09-02 15:50:56,836 - root - INFO - Connected ElasticSearch version: 7.10.2
2025-09-02 15:50:56,837 - root - INFO - Applied tool filter from environment variables
2025-09-02 15:50:56,838 - root - INFO - Available tools after filtering: ['ListIndexTool', 'IndexMappingTool', 'SearchIndexTool', 'GetShardsTool']
2025-09-02 15:50:56,839 - root - INFO - Enabled tools: ['ListIndexTool', 'IndexMappingTool', 'SearchIndexTool', 'GetShardsTool']
INFO:     Started server process [10294]
INFO:     Waiting for application startup.
2025-09-02 15:50:57,035 - mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started
2025-09-02 15:50:57,035 - root - INFO - Application started with StreamableHTTP session manager!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

## Sample langchain output:

```
Starting agent invocation...


> Entering new AgentExecutor chain...
Thought: The user wants to list all indices in the Elasticsearch cluster. I should use the ListIndexTool to get this information.

Action:
```json
{
  "action": "ListIndexTool",
  "action_input": {}
}

Observation: All indices information:
[
  {
    "health": "green",
    "status": "open",
    "index": "test_index_3",
    "uuid": "vC2-kYNWSZSYxNXiMxC0mw",
    "pri": "1",
    "rep": "0",
    "docs.count": "0",
    "docs.deleted": "0",
    "store.size": "208b",
    "pri.store.size": "208b"
  },
  {
    "health": "green",
    "status": "open",
    "index": "test_index_2",
    "uuid": "lR8JOb4eQDWaFH6DK1DaPA",
    "pri": "1",
    "rep": "0",
    "docs.count": "1",
    "docs.deleted": "0",
    "store.size": "4.4kb",
    "pri.store.size": "4.4kb"
  },
  {
    "health": "green",
    "status": "open",
    "index": "test_index_1",
    "uuid": "WALKOQbtQkq-4YPRn8BkOw",
    "pri": "1",
    "rep": "0",
    "docs.count": "3",
    "docs.deleted": "0",
    "store.size": "4.7kb",
    "pri.store.size": "4.7kb"
  }
]
Thought:{
  "action": "Final Answer",
  "action_input": "当前Elasticsearch集群中有以下3个索引：\n\n1. test_index_3 - 健康状态: green, 文档数: 0, 存储大小: 208b\n2. test_index_2 - 健康状态: green, 文档数: 1, 存储大小: 4.4kb\n3. test_index_1 - 健康状态: green, 文档数: 3, 存储大小: 4.7kb\n\n所有索引都处于正常运行状态（green）。"
}

> Finished chain.

Agent Response: {
  "action": "Final Answer",
  "action_input": "当前Elasticsearch集群中有以下3个索引：\n\n1. test_index_3 - 健康状态: green, 文档数: 0, 存储大小: 208b\n2. test_index_2 - 健康状态: green, 文档数: 1, 存储大小: 4.4kb\n3. test_index_1 - 健康状态: green, 文档数: 3, 存储大小: 4.7kb\n\n所有索引都处于正常运行状态（green）。"
}

Agent process completed
```