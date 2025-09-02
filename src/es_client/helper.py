# SPDX-License-Identifier: Apache-2.0

import json
import logging
from semver import Version
from tools.tool_params import *

# Configure logging
logger = logging.getLogger(__name__)


# 所有 helper 函数都直接调用 Elasticsearch 客户端
# 这些函数会在 tools 中被用到，构建更复杂的工具

def list_indices(args: ListIndicesArgs) -> json:
    """列出所有索引"""
    from .client import initialize_client

    client = initialize_client(args)
    response = client.cat.indices(format='json')
    return response


def get_index(args: ListIndicesArgs) -> json:
    """获取指定索引的详细信息（包含 settings、mappings 等）"""
    from .client import initialize_client

    client = initialize_client(args)
    response = client.indices.get(index=args.index)
    return response


def get_index_mapping(args: GetIndexMappingArgs) -> json:
    """获取指定索引的 mapping"""
    from .client import initialize_client

    client = initialize_client(args)
    response = client.indices.get_mapping(index=args.index)
    return response


def search_index(args: SearchIndexArgs) -> json:
    """在指定索引中执行搜索"""
    from .client import initialize_client

    client = initialize_client(args)
    response = client.search(index=args.index, body=args.query)
    return response


def get_shards(args: GetShardsArgs) -> json:
    """获取指定索引的分片信息"""
    from .client import initialize_client

    client = initialize_client(args)
    response = client.cat.shards(index=args.index, format='json')
    return response


def get_elasticsearch_version(args: baseToolArgs) -> Version | None:
    """获取 Elasticsearch 版本号（SemVer 格式）"""
    from .client import initialize_client

    try:
        client = initialize_client(args)
        response = client.info()
        return Version.parse(response['version']['number'])
    except Exception as e:
        logger.error(f'Error getting Elasticsearch version: {e}')
        return None