# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import re

from es_client.helper import get_elasticsearch_version

from .tool_params import baseToolArgs
from .utils import (
    is_tool_compatible,
    parse_comma_separated,
    load_yaml_config,
    validate_tools,
)


def process_regex_patterns(regex_list, tool_names):
    """Process regex patterns and return matching tool names."""
    matching_tools = []
    for regex in regex_list:
        for tool_name in tool_names:
            if re.match(regex, tool_name, re.IGNORECASE):
                matching_tools.append(tool_name)
    return matching_tools


def apply_write_filter(registry):
    """Apply allow_write filters to the registry."""
    for tool_name in list(registry.keys()):
        http_methods = registry[tool_name].get('http_methods', [])
        if 'GET' not in http_methods:
            registry.pop(tool_name, None)


def process_categories(category_list, category_to_tools):
    """Process categories and return tools from those categories."""
    tools = []
    for category in category_list:
        if category in category_to_tools:
            tools.extend(category_to_tools[category])
        else:
            logging.warning(f"Category '{category}' not found in tool categories")
    return tools


def process_tool_filter(
    disabled_tools: str = None,
    tool_categories: str = None,
    disabled_categories: str = None,
    disabled_tools_regex: str = None,
    allow_write: bool = None,
    filter_path: str = None,
    tool_registry: dict = None,
) -> None:
    """Process tool filter configuration from a YAML file and environment variables.

    Args:
        disabled_tools: Comma-separated list of disabled tool names
        tool_categories: JSON string defining tool categories, e.g. '{"critical":["ListIndexTool","MsearchTool"]}'
        disabled_categories: Comma-separated list of disabled category names
        disabled_tools_regex: Comma-separated list of disabled tools regex
        allow_write: If True, allow tools with PUT/POST methods
        filter_path: Path to the YAML filter configuration file
        tool_registry: The tool registry to filter.
    """
    try:
        # Create display name lookup
        display_name = {
            tool_info.get('display_name', '').lower(): k for k, tool_info in tool_registry.items()
        }

        # Initialize collections
        category_to_tools = {}
        disabled_tools_list = []
        disabled_category_list = []
        disabled_tools_regex_list = []

        # Process YAML config file if provided
        config = load_yaml_config(filter_path)
        if config:
            # Extract configuration values
            category_to_tools.update(config.get('tool_category', {}))
            tool_filters = config.get('tool_filters', {})

            # Get lists from config
            disabled_tools_list = tool_filters.get('disabled_tools', [])
            disabled_category_list = tool_filters.get('disabled_categories', [])
            disabled_tools_regex_list = tool_filters.get('disabled_tools_regex', [])

            # Get settings
            settings = tool_filters.get('settings', {})
            if settings:
                allow_write = settings.get('allow_write', True)

        # Process environment variables
        if tool_categories:
            try:
                category_to_tools.update(
                    json.loads(tool_categories) if isinstance(tool_categories, str) else {}
                )
            except json.JSONDecodeError:
                logging.warning(f'Invalid JSON in tool_categories: {tool_categories}')

        # Parse comma-separated strings from environment variables
        if disabled_tools:
            disabled_tools_list.extend(parse_comma_separated(disabled_tools))
        if disabled_categories:
            disabled_category_list.extend(parse_comma_separated(disabled_categories))
        if disabled_tools_regex:
            disabled_tools_regex_list.extend(parse_comma_separated(disabled_tools_regex))

        # Apply allow_write filter first
        if not allow_write:
            apply_write_filter(tool_registry)

        # Process tools from categories and regex patterns
        disabled_tools_from_categories = process_categories(
            disabled_category_list, category_to_tools
        )

        # Get current tool names after allow_write filtering
        current_tool_names = [tool['display_name'] for tool in tool_registry.values()]
        disabled_tools_from_regex = process_regex_patterns(
            disabled_tools_regex_list, current_tool_names
        )

        # Apply disabled tools filter
        if disabled_tools_list or disabled_tools_from_categories or disabled_tools_from_regex:
            # Validate and collect all disabled tools
            all_disabled_tools = set()
            all_disabled_tools.update(
                validate_tools(disabled_tools_list, display_name, 'disabled_tools')
            )
            all_disabled_tools.update(
                validate_tools(disabled_tools_from_categories, display_name, 'disabled_categories')
            )
            all_disabled_tools.update(
                validate_tools(disabled_tools_from_regex, display_name, 'disabled_tools_regex')
            )

            # Remove tools in the disabled list
            for tool_name in list(tool_registry.keys()):
                if tool_name.lower() in all_disabled_tools:
                    tool_registry.pop(tool_name, None)

        # Log results
        source = filter_path if filter_path else 'environment variables'
        tool_display_names = [tool['display_name'] for tool in tool_registry.values()]
        logging.info(f'Applied tool filter from {source}')
        logging.info(f'Available tools after filtering: {tool_display_names}')

    except Exception as e:
        logging.error(f'Error processing tool filter: {str(e)}')


def get_tools(tool_registry: dict, mode: str = 'single', config_file_path: str = '') -> dict:
    """Filter and return available tools based on server mode and ElasticSearch version.

    In 'multi' mode, returns all tools without filtering. In 'single' mode, filters tools
    based on ElasticSearch version compatibility and removes base tool arguments from schemas.

    Args:
        tool_registry (dict): The tool registry to filter.
        mode (str): Server mode - 'single' for version-filtered tools, 'multi' for all tools
        config_file_path (str): Path to a YAML configuration file

    Returns:
        dict: Dictionary of enabled tools with their configurations
    """
    # In multi mode, return all tools without any filtering
    if mode == 'multi':
        return tool_registry

    enabled = {}

    # Get ElasticSearch version for compatibility checking (only in single mode)
    version = get_elasticsearch_version(baseToolArgs())
    logging.info(f'Connected ElasticSearch version: {version}')

    # Get environment variables for tool filtering
    env_config = {
        'disabled_tools': os.getenv('ELASTICSEARCH_DISABLED_TOOLS', ''),
        'tool_categories': os.getenv('ELASTICSEARCH_TOOL_CATEGORIES', ''),
        'disabled_categories': os.getenv('ELASTICSEARCH_DISABLED_CATEGORIES', ''),
        'disabled_tools_regex': os.getenv('ELASTICSEARCH_DISABLED_TOOLS_REGEX', ''),
        'allow_write': os.getenv('ELASTICSEARCH_SETTINGS_ALLOW_WRITE', 'true').lower() == 'true',
    }

    # Check if both config and env variables are set
    if config_file_path and any(env_config.values()):
        logging.warning('Both config file and environment variables are set. Using config file.')

    # Apply tool filtering, update the TOOL_REGISTRY
    process_tool_filter(
        tool_registry=tool_registry,
        filter_path=config_file_path if config_file_path else None,
        **{k: v for k, v in env_config.items() if not config_file_path},
    )

    for name, info in tool_registry.items():
        # Create a copy to avoid modifying the original tool info
        tool_info = info.copy()
        tool_name = tool_info['display_name']

        # If tool is not compatible with the current ElasticSearch version, skip, don't enable
        if not is_tool_compatible(version, info):
            continue

        # Remove baseToolArgs fields from input schema for single mode
        # This simplifies the schema since base args are handled internally
        schema = tool_info['input_schema'].copy()
        if 'properties' in schema:
            base_fields = baseToolArgs.model_fields.keys()
            for field in base_fields:
                schema['properties'].pop(field, None)
        tool_info['input_schema'] = schema

        enabled[tool_name] = tool_info

    return enabled
