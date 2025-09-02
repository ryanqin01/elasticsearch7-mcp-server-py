# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import Any, Dict, Optional

from elasticsearch import Elasticsearch

from mcp_server_elasticsearch.clusters_information import ClusterInfo, get_cluster
from tools.tool_params import baseToolArgs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# global profile variable from command line (保留接口，但在本地模式下不用)
arg_profile: Optional[str] = None

def initialize_client_with_cluster(cluster_info: ClusterInfo | None) -> Elasticsearch:
    """
    初始化 Elasticsearch 7.10 客户端。

    认证优先级：
    1. 如果设置了 ELASTICSEARCH_NO_AUTH=true，则不使用认证（适用于无认证集群）
    2. 否则尝试基本认证（用户名/密码）
    3. 如果都没有，则尝试无认证连接（但可能失败）

    Args:
        cluster_info (ClusterInfo | None): 集群信息（可选）

    Returns:
        Elasticsearch: 客户端实例
    """
    es_url = (
        cluster_info.elasticsearch_url if cluster_info else os.getenv("ELASTICSEARCH_URL", "")
    )
    if not es_url:
        raise ValueError(
            "Elasticsearch URL 必须通过配置文件或 ELASTICSEARCH_URL 环境变量提供"
        )

    es_username = (
        cluster_info.elasticsearch_username
        if cluster_info
        else os.getenv("ELASTICSEARCH_USERNAME", "")
    )
    es_password = (
        cluster_info.elasticsearch_password
        if cluster_info
        else os.getenv("ELASTICSEARCH_PASSWORD", "")
    )

    es_timeout = (
        cluster_info.timeout if cluster_info else os.getenv("ELASTICSEARCH_TIMEOUT", None)
    )

    client_kwargs: Dict[str, Any] = {
        "hosts": [es_url],
    }

    if es_timeout:
        client_kwargs["timeout"] = int(es_timeout)

    # 1. 显式无认证
    if os.getenv("ELASTICSEARCH_NO_AUTH", "").lower() == "true":
        logger.info("[NO AUTH] 尝试无认证连接 Elasticsearch")
        return Elasticsearch(**client_kwargs)

    # 2. 基本认证
    if es_username and es_password:
        logger.info(f"[BASIC AUTH] 使用基本认证: {es_username}")
        client_kwargs["http_auth"] = (es_username, es_password)
        return Elasticsearch(**client_kwargs)

    # 3. 默认尝试无认证
    logger.info("[DEFAULT] 未提供认证信息，尝试无认证连接")
    return Elasticsearch(**client_kwargs)


def initialize_client(args: baseToolArgs) -> Elasticsearch:
    """Initialize and return an Elasticsearch client based on provided arguments.

    Supports two modes:
    - Multi-cluster: When args.elasticsearch_cluster_name is provided
    - Single-cluster: When no cluster name is provided (uses environment variables)

    Args:
        args (baseToolArgs): Arguments containing optional elasticsearch_cluster_name

    Returns:
        Elasticsearch: An initialized Elasticsearch client instance
    """
    cluster_info = None
    if args and args.elasticsearch_cluster_name:
        cluster_info = get_cluster(args.elasticsearch_cluster_name)
    return initialize_client_with_cluster(cluster_info)
