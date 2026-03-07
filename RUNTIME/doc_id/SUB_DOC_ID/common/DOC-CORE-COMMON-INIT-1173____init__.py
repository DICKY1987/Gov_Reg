# DOC_LINK: DOC-CORE-COMMON-INIT-1173
"""
Common utilities for DOC_ID system.

Provides shared configuration, utilities, and helpers to eliminate
code duplication across the DOC_ID management tools.

Version: 2.1.0
"""
# DOC_ID: DOC-CORE-COMMON-INIT-1173

__version__ = "2.1.0"

from common.DOC_CONFIG_COMMON_CONFIG_283__config import (
    REPO_ROOT,
    MODULE_ROOT,
    REGISTRY_PATH,
    INVENTORY_PATH,
    REPORTS_DIR,
    DOC_ID_REGEX,
    ELIGIBLE_PATTERNS,
    EXCLUDE_PATTERNS,
)

from common.DOC_CORE_COMMON_UTILS_1172__utils import (
    load_yaml,
    save_yaml,
    load_jsonl,
    save_jsonl,
    validate_doc_id,
    extract_category_from_doc_id,
)

from common.DOC_CORE_COMMON_ERRORS_1169__errors import (
    DocIDError,
    RegistryNotFoundError,
    InventoryNotFoundError,
    InvalidDocIDError,
)

from common.DOC_CORE_COMMON_LOGGING_SETUP_1170__logging_setup import (
    setup_logging,
    get_logger,
)

from common.DOC_CORE_COMMON_CACHE_1168__cache import (
    SimpleCache,
    FileCache,
    cached,
    get_cache,
)

__all__ = [
    # Config
    'REPO_ROOT',
    'MODULE_ROOT',
    'REGISTRY_PATH',
    'INVENTORY_PATH',
    'REPORTS_DIR',
    'DOC_ID_REGEX',
    'ELIGIBLE_PATTERNS',
    'EXCLUDE_PATTERNS',
    # Utils
    'load_yaml',
    'save_yaml',
    'load_jsonl',
    'save_jsonl',
    'validate_doc_id',
    'extract_category_from_doc_id',
    # Errors
    'DocIDError',
    'RegistryNotFoundError',
    'InventoryNotFoundError',
    'InvalidDocIDError',
    # Logging
    'setup_logging',
    'get_logger',
    # Caching
    'SimpleCache',
    'FileCache',
    'cached',
    'get_cache',
]
