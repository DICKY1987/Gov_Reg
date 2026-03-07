# DOC_LINK: DOC-SCRIPT-1324
"""
Common utilities for DOC_ID system.
Auto-generated after filename migration.
"""
import sys
import importlib.util
from pathlib import Path

__version__ = "2.1.0"

_dir = Path(__file__).parent

# Module mapping: old_name -> new_filename
_modules = {
    "cache": "DOC-CORE-COMMON-CACHE-1168__cache.py",
    "config": "DOC-CONFIG-COMMON-CONFIG-283__config.py",
    "coverage_provider": "DOC-CORE-SUB-DOC-ID-COMMON-COVERAGE-PROVIDER-1115__coverage_provider.py",
    "errors": "DOC-CORE-COMMON-ERRORS-1169__errors.py",
    "event_emitter": "DOC-CORE-SSOT-SYS-TOOLS-EVENT-EMITTER-1109__event_emitter.py",
    "event_router": "DOC-SCRIPT-1006__event_router.py",
    "event_sinks": "DOC-SCRIPT-1007__event_sinks.py",
    "index_store": "DOC-INDEX-COMMON-INDEX-STORE-001__index_store.py",
    "logging_setup": "DOC-CORE-COMMON-LOGGING-SETUP-1170__logging_setup.py",
    "registry": "DOC-CORE-COMMON-REGISTRY-1171__registry.py",
    "rules": "DOC-RULES-COMMON-RULES-001__rules.py",
    "staging": "DOC-STAGING-COMMON-STAGING-001__staging.py",
    "test_common": "DOC-TEST-COMMON-TEST-COMMON-670__test_common.py",
    "test_index_store": "DOC-TEST-INDEX-STORE-001__test_index_store.py",
    "test_rules": "DOC-TEST-RULES-001__test_rules.py",
    "trace_context": "DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108__trace_context.py",
    "tier2_canonical_hash": "DOC-SCRIPT-1008__tier2_canonical_hash.py",
    "tier2_edges": "DOC-SCRIPT-1009__tier2_edges.py",
    "tier2_symbols": "DOC-SCRIPT-1010__tier2_symbols.py",
    "utils": "DOC-CORE-COMMON-UTILS-1172__utils.py",
    "validators": "DOC-VALIDATORS-COMMON-VALIDATORS-001__validators.py",

}

# Load modules in dependency order
# 1. First load modules with no dependencies
# 2. Then load modules that depend on them
_load_order = [
    "errors",  # No dependencies
    "rules",   # No dependencies
    "config",  # Depends on: rules
    "utils",   # Depends on: config, errors
    "logging_setup",  # Depends on: config
    "cache",   # Depends on: nothing (time is stdlib)
    "registry",  # Depends on: config, utils, errors, cache
    "index_store",  # Later
    "staging",  # Later
    "validators",  # Later
    "trace_context",  # Later
    "event_emitter",  # Later
    "event_router",  # Later
    "event_sinks",  # Later
    "coverage_provider",  # Later
    "tier2_canonical_hash",  # Later
    "tier2_edges",  # Later
    "tier2_symbols",  # Later
    "test_common",  # Later
    "test_index_store",  # Later
    "test_rules",  # Later
]

_loaded = {}
for _old_name in _load_order:
    if _old_name in _modules:
        _filename = _modules[_old_name]
        try:
            _spec = importlib.util.spec_from_file_location(
                f"common.{_old_name}",
                _dir / _filename
            )
            _mod = importlib.util.module_from_spec(_spec)
            sys.modules[f"common.{_old_name}"] = _mod
            _spec.loader.exec_module(_mod)
            _loaded[_old_name] = _mod
        except Exception as e:
            # Skip modules that fail to load (might have other dependencies)
            print(f"Warning: Failed to load common.{_old_name}: {e}", file=sys.stderr)
            pass

# Export commonly used items from config
if "config" in _loaded:
    _cfg = _loaded["config"]
    REPO_ROOT = getattr(_cfg, "REPO_ROOT", None)
    MODULE_ROOT = getattr(_cfg, "MODULE_ROOT", None)
    REGISTRY_PATH = getattr(_cfg, "REGISTRY_PATH", None)
    INVENTORY_PATH = getattr(_cfg, "INVENTORY_PATH", None)
    REPORTS_DIR = getattr(_cfg, "REPORTS_DIR", None)
    DOC_ID_REGEX = getattr(_cfg, "DOC_ID_REGEX", None)
    ELIGIBLE_PATTERNS = getattr(_cfg, "ELIGIBLE_PATTERNS", None)
    EXCLUDE_PATTERNS = getattr(_cfg, "EXCLUDE_PATTERNS", None)

# Export commonly used items from utils
if "utils" in _loaded:
    _util = _loaded["utils"]
    load_yaml = getattr(_util, "load_yaml", None)
    save_yaml = getattr(_util, "save_yaml", None)
    load_jsonl = getattr(_util, "load_jsonl", None)
    save_jsonl = getattr(_util, "save_jsonl", None)
    validate_doc_id = getattr(_util, "validate_doc_id", None)
    extract_category_from_doc_id = getattr(_util, "extract_category_from_doc_id", None)

# Export commonly used items from errors
if "errors" in _loaded:
    _err = _loaded["errors"]
    DocIDError = getattr(_err, "DocIDError", None)
    RegistryNotFoundError = getattr(_err, "RegistryNotFoundError", None)
    InventoryNotFoundError = getattr(_err, "InventoryNotFoundError", None)
    InvalidDocIDError = getattr(_err, "InvalidDocIDError", None)

# Export commonly used items from logging_setup
if "logging_setup" in _loaded:
    _log = _loaded["logging_setup"]
    setup_logging = getattr(_log, "setup_logging", None)
    get_logger = getattr(_log, "get_logger", None)

# Export commonly used items from cache
if "cache" in _loaded:
    _cache = _loaded["cache"]
    SimpleCache = getattr(_cache, "SimpleCache", None)
    FileCache = getattr(_cache, "FileCache", None)
    cached = getattr(_cache, "cached", None)
    get_cache = getattr(_cache, "get_cache", None)
