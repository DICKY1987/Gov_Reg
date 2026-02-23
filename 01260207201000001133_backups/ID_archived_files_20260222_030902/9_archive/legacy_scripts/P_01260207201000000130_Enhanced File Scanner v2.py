#!/usr/bin/env python3
"""
Enhanced File Scanner v2.0
A robust, cross-platform file metadata collection tool with streaming output,
resume capability, and comprehensive error handling.
"""

import os
import json
import csv
import hashlib
import mimetypes
import platform
import signal
import sys
import time
import threading
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Generator, Any, Tuple
from collections import defaultdict, deque
import argparse
import logging
import gzip

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# =============================================================================
# USER CONFIGURATION SECTION
# Modify these settings to customize the scanner behavior
# =============================================================================

# SCAN SOURCE DIRECTORY
# Set the directory you want to scan
# Examples:
#   Windows: r"C:\Users\YourName\Documents"
#   Linux/Mac: "/home/username" or "/Users/username"
#   Current directory: "."
SCAN_PATH = r"C:\Users\richg\eafix-modular"  # Default: User's home directory

# OUTPUT DIRECTORY
# Where to save the scan results
# Examples:
#   Windows: r"C:\Users\YourName\Desktop\ScanResults"
#   Linux/Mac: "/home/username/scan_results"
#   Relative: "./scan_output"
OUTPUT_DIR = os.path.join(r"C:\Users\richg\eafix-modular", 'scan_output')

# OUTPUT FORMATS
# Choose which file formats to generate
# Options: 'json', 'ndjson', 'csv', 'markdown'
# You can specify one or multiple formats
OUTPUT_FORMATS = ['markdown', 'csv']

# HASH CALCULATION
# Set to True to calculate file checksums (slower but provides file integrity info)
INCLUDE_HASHES = False

# HASH ALGORITHMS
# Which hash algorithms to use (only applies if INCLUDE_HASHES is True)
# Options: 'md5', 'sha1', 'sha256', 'sha512'
# Note: SHA256 is recommended for security, MD5 is fastest
HASH_ALGORITHMS = ['sha256']

# FILE SIZE LIMITS
# Set maximum file size for hash calculation (in bytes)
# Large files take longer to hash. Set to 0 for no limit.
# Examples: 50MB = 50 * 1024 * 1024, 100MB = 100 * 1024 * 1024
MAX_FILE_SIZE_FOR_HASH = 100 * 1024 * 1024  # 100MB

# PRIMARY CONTENT HASH (NATURAL-KEY)
# content_hash is required for registry natural keys. By default we always compute
# SHA-256 with no size limit (0 = no limit).
MAX_FILE_SIZE_FOR_CONTENT_HASH = 0

# IDENTITY / NAMING RULES
# Used to detect and plan 16-digit filename prefixes.
ID_REGEX = r'^\d{16}_'
ID_PLACEHOLDER = '0000000000000000'
DEFAULT_SCOPE = 'GLOBAL'

# Optional identity configuration JSON (overrides ID_REGEX/mappings if provided)
# Example structure:
# {
#   "id_regex": "^\\d{16}_",
#   "placeholder_id": "0000000000000000",
#   "default_scope": "GLOBAL",
#   "type_code_by_extension": {"py": "PY", "md": "DOC"},
#   "ns_code_by_top_dir": {"docs": "DOC", "src": "SRC"},
#   "scope_by_ns_code": {"DOC": "DOCS"}
# }
IDENTITY_CONFIG_PATH = ''

# Minimum file size to process (0 = no minimum)
MIN_FILE_SIZE = 0

# Maximum file size to process (0 = no maximum)  
MAX_FILE_SIZE = 0

# FILTERING OPTIONS
# Exclude files containing these patterns in their names (case-insensitive)
# Examples: ['.tmp', 'cache', 'temp', '.log']
EXCLUDE_PATTERNS = []

# Exclude directories by name (case-insensitive)
# Examples: ['.git', '__pycache__', 'node_modules', 'venv', '.venv']
EXCLUDE_DIR_NAMES = ['.git', '__pycache__', 'node_modules', 'venv', '.venv']

# Include only files containing these patterns (leave empty to include all)
# If specified, only files matching these patterns will be processed
INCLUDE_PATTERNS = []

# ADVANCED OPTIONS
# Include file permissions and ownership information
INCLUDE_PERMISSIONS = True

# Include extended file attributes (Linux/Mac only)
INCLUDE_EXTENDED_ATTRS = False

# Compress output files with gzip
COMPRESS_OUTPUT = False

# Enable resume capability (can restart interrupted scans)
RESUME_FROM_CHECKPOINT = True

# Progress update interval in seconds
PROGRESS_INTERVAL = 2.0

# How often to save checkpoints (number of files)
CHECKPOINT_INTERVAL = 1000

# Maximum errors to report per error type
MAX_ERRORS_PER_TYPE = 50

# =============================================================================
# END OF USER CONFIGURATION
# =============================================================================

# Version and metadata
VERSION = "2.0.0"
SCANNER_ID = f"enhanced_file_scanner_v{VERSION}"

@dataclass
class ScanConfig:
    """Configuration for file scanning operations"""
    scan_path: str
    output_dir: str
    output_formats: List[str] = None  # json, ndjson, csv, markdown
    include_hashes: bool = False
    hash_algorithms: List[str] = None  # md5, sha1, sha256
    # Primary content hash used for natural keys (typically SHA-256)
    max_file_size_for_content_hash: int = 0  # 0 means no limit
    include_permissions: bool = True
    include_extended_attrs: bool = False
    max_file_size_for_hash: int = 100 * 1024 * 1024  # 100MB
    file_filters: Dict[str, Any] = None
    progress_interval: float = 2.0
    checkpoint_interval: int = 1000
    compress_output: bool = False
    resume_from_checkpoint: bool = True
    max_errors_per_type: int = 50
    parallel_hashing: bool = True
    exclude_patterns: List[str] = None
    exclude_dir_names: List[str] = None
    include_patterns: List[str] = None
    min_file_size: int = 0
    max_file_size: int = 0  # 0 means no limit

    # Identity / naming settings (used to populate registry planning columns)
    identity_config_path: Optional[str] = None
    id_regex: str = r'^\d{16}_'
    id_placeholder: str = '0000000000000000'
    default_scope: str = 'GLOBAL'
    type_code_by_extension: Dict[str, str] = None
    ns_code_by_top_dir: Dict[str, str] = None
    scope_by_ns_code: Dict[str, str] = None
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['json', 'markdown']
        if self.hash_algorithms is None:
            self.hash_algorithms = ['sha256']
        if self.file_filters is None:
            self.file_filters = {}
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.exclude_dir_names is None:
            self.exclude_dir_names = []
        if self.include_patterns is None:
            self.include_patterns = []
        if self.type_code_by_extension is None:
            self.type_code_by_extension = {}
        if self.ns_code_by_top_dir is None:
            self.ns_code_by_top_dir = {}
        if self.scope_by_ns_code is None:
            self.scope_by_ns_code = {}

@dataclass
class FileMetadata:
    """Comprehensive file metadata structure (registry-ready)"""

    # Per-scan invariants
    scan_id: str = ""
    scan_root: str = ""
    first_seen_utc: str = ""  # snapshot timestamp used in natural keys

    # Core registry fields
    relative_path: str = ""  # repo-root-relative path (portable)
    path: str = ""  # absolute path at scan time
    name: str = ""  # basename at scan time
    extension: str = ""  # lowercase, no dot
    size_bytes: int = 0
    mtime_utc: str = ""  # modified time (UTC ISO-8601)
    created_time: str = ""  # filesystem ctime (UTC ISO-8601)
    accessed_time: str = ""  # atime (UTC ISO-8601)
    is_directory: bool = False
    is_symlink: bool = False
    permissions: Optional[str] = None
    owner: Optional[str] = None
    group: Optional[str] = None
    mime_type: Optional[str] = None

    # Identity / naming rule fields
    doc_id: str = ""  # extracted 16-digit prefix from filename, if present
    has_id_prefix: bool = False
    current_id_prefix: str = ""  # explicit version of doc_id
    needs_id: bool = False

    # Planning placeholders (Phase 0/1)
    type_code: str = ""
    ns_code: str = ""
    scope: str = ""
    planned_id: str = ""  # populated during planning; blank in scan
    planned_rel_path: str = ""  # populated during planning; blank in scan

    # Hashing
    content_hash: str = ""  # primary natural-key content hash (typically SHA-256)
    hashes: Optional[Dict[str, str]] = None  # optional extra hash columns

    # Misc
    extended_attrs: Optional[Dict[str, str]] = None
    symlink_target: Optional[str] = None

    # Error capture (audit-perfect runs)
    error: str = ""
    error_kind: str = ""

class ProgressTracker:
    """Rolling average progress tracker without pre-scanning"""
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self.start_time = time.time()
        self.last_update = self.start_time
        self.processed_files = 0
        self.processed_dirs = 0
        self.total_size = 0
        self.error_counts = defaultdict(int)
        self.recent_rates = deque(maxlen=10)  # Keep last 10 rates for smoothing
        
    def update(self, files_delta: int = 0, dirs_delta: int = 0, size_delta: int = 0):
        """Update counters and maybe display progress"""
        self.processed_files += files_delta
        self.processed_dirs += dirs_delta
        self.total_size += size_delta
        
        now = time.time()
        if now - self.last_update >= self.update_interval:
            self._display_progress(now)
            self.last_update = now
    
    def _display_progress(self, now: float):
        """Display current progress with rolling average rate"""
        elapsed = now - self.start_time
        if elapsed < 1:
            return
            
        current_rate = self.processed_files / elapsed
        self.recent_rates.append(current_rate)
        smooth_rate = sum(self.recent_rates) / len(self.recent_rates)
        
        size_mb = self.total_size / (1024 * 1024)
        
        print(f"[PROGRESS] Files: {self.processed_files:,} | "
              f"Dirs: {self.processed_dirs:,} | "
              f"Size: {size_mb:.1f}MB | "
              f"Rate: {smooth_rate:.1f} files/sec | "
              f"Elapsed: {self._format_time(elapsed)}")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as human-readable time"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m{seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h{minutes:.0f}m"
    
    def add_error(self, error_type: str):
        """Record an error for statistics"""
        self.error_counts[error_type] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get final summary statistics"""
        elapsed = time.time() - self.start_time
        return {
            'files_processed': self.processed_files,
            'directories_processed': self.processed_dirs,
            'total_size_bytes': self.total_size,
            'elapsed_seconds': elapsed,
            'average_rate': self.processed_files / elapsed if elapsed > 0 else 0,
            'error_counts': dict(self.error_counts)
        }

class CheckpointManager:
    """Manages scan checkpoints for resume capability"""
    def __init__(self, checkpoint_file: str, interval: int = 1000):
        self.checkpoint_file = checkpoint_file
        self.interval = interval
        self.processed_paths = set()
        self.files_since_checkpoint = 0
        
    def load_checkpoint(self) -> set:
        """Load processed paths from checkpoint file"""
        if not os.path.exists(self.checkpoint_file):
            return set()
            
        try:
            with open(self.checkpoint_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logging.warning(f"Could not load checkpoint: {e}")
            return set()
    
    def save_checkpoint(self, path: str):
        """Add path to checkpoint and maybe save"""
        self.processed_paths.add(path)
        self.files_since_checkpoint += 1
        
        if self.files_since_checkpoint >= self.interval:
            self._write_checkpoint()
            self.files_since_checkpoint = 0
    
    def _write_checkpoint(self):
        """Write checkpoint to disk"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                for path in sorted(self.processed_paths):
                    f.write(f"{path}\n")
        except Exception as e:
            logging.error(f"Could not save checkpoint: {e}")
    
    def cleanup(self):
        """Remove checkpoint file on successful completion"""
        try:
            os.remove(self.checkpoint_file)
        except OSError:
            pass

class EnhancedFileScanner:
    """Main scanner class with streaming output and resume capability"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.should_stop = False
        self.progress = ProgressTracker(config.progress_interval)
        self.checkpoint_manager = None
        self.output_writers = {}

        # Per-scan invariants (set at scan start)
        self.scan_id: str = ""
        self.scan_root: str = os.path.abspath(self.config.scan_path)
        self.first_seen_utc: str = ""

        # Identity config (may be overridden by identity_config_path)
        self._load_identity_config()
        self._id_prefix_re = re.compile(self.config.id_regex)
        # Extraction stays 16-digit specific for doc_id/current_id_prefix
        self._doc_id_extract_re = re.compile(r'^(?P<doc_id>\d{16})_')
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Create output directory and setup logging
        self._setup_output_directory()
        self.logger = self._setup_logging()

    def _load_identity_config(self):
        """Optionally load identity / naming rules from a JSON config file."""
        path = self.config.identity_config_path
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                self.config.id_regex = cfg.get('id_regex', self.config.id_regex)
                self.config.id_placeholder = cfg.get('placeholder_id', self.config.id_placeholder)
                self.config.default_scope = cfg.get('default_scope', self.config.default_scope)
                self.config.type_code_by_extension.update(cfg.get('type_code_by_extension', {}) or {})
                self.config.ns_code_by_top_dir.update(cfg.get('ns_code_by_top_dir', {}) or {})
                self.config.scope_by_ns_code.update(cfg.get('scope_by_ns_code', {}) or {})
        except FileNotFoundError:
            # Silently ignore missing identity config.
            return
        except Exception:
            # Keep scanning even if identity config is malformed.
            return

    @staticmethod
    def _utc_iso(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    @staticmethod
    def _norm_relpath(p: str) -> str:
        # Portable path for registries
        return p.replace('\\', '/').replace(os.sep, '/')

    def _derive_type_code(self, extension: str, is_directory: bool) -> str:
        if is_directory:
            return 'DIR'
        ext = (extension or '').lower()
        if not ext:
            return 'NOEXT'
        if ext in self.config.type_code_by_extension:
            return str(self.config.type_code_by_extension.get(ext) or '').strip()
        return ext.upper()

    def _derive_ns_code(self, relative_dir: str) -> str:
        """Derive namespace code using directory rules only."""
        rp = (relative_dir or '').replace('\\', '/').strip('/')
        if not rp or rp == '.':
            top = ''
        else:
            top = rp.split('/')[0]

        if top and top in self.config.ns_code_by_top_dir:
            return str(self.config.ns_code_by_top_dir.get(top) or '').strip()
        if not top:
            return 'ROOT'
        return top.upper()[:32]

    def _derive_scope(self, ns_code: str) -> str:
        ns = (ns_code or '').strip()
        if ns and ns in self.config.scope_by_ns_code:
            return str(self.config.scope_by_ns_code.get(ns) or '').strip()
        return self.config.default_scope

    def _populate_identity_fields(self, meta: FileMetadata):
        meta.has_id_prefix = bool(self._id_prefix_re.match(meta.name or ''))
        m = self._doc_id_extract_re.match(meta.name or '')
        if m:
            meta.doc_id = m.group('doc_id')
            meta.current_id_prefix = meta.doc_id
        else:
            meta.doc_id = ''
            meta.current_id_prefix = ''
        meta.needs_id = not meta.has_id_prefix

        # Derivations for planning columns
        meta.type_code = self._derive_type_code(meta.extension, meta.is_directory)
        rel_dir = meta.relative_path or ''
        if not meta.is_directory:
            rel_dir = os.path.dirname(rel_dir.replace('\\', '/'))
        meta.ns_code = self._derive_ns_code(rel_dir)
        meta.scope = self._derive_scope(meta.ns_code)
        
    def _setup_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.config.output_dir, exist_ok=True)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging with file and console output"""
        logger = logging.getLogger(SCANNER_ID)
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_file = os.path.join(self.config.output_dir, 'scanner.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
    
    def scan(self) -> bool:
        """Main scanning method with full error handling"""
        try:
            self._validate_config()

            # Per-run snapshot identifiers
            now_utc = datetime.now(timezone.utc)
            self.scan_root = os.path.abspath(self.config.scan_path)
            self.first_seen_utc = self._utc_iso(now_utc.replace(microsecond=0))
            self.scan_id = f"{now_utc.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:12]}"

            self._initialize_output_writers()
            
            if self.config.resume_from_checkpoint:
                self.checkpoint_manager = CheckpointManager(
                    os.path.join(self.config.output_dir, 'checkpoint.txt'),
                    self.config.checkpoint_interval
                )
                processed_paths = self.checkpoint_manager.load_checkpoint()
                self.logger.info(f"Resuming scan, skipping {len(processed_paths)} already processed paths")
            else:
                processed_paths = set()
            
            # Start the scan
            self.logger.info(f"Starting scan of: {self.config.scan_path}")
            self.logger.info(f"Output formats: {', '.join(self.config.output_formats)}")
            
            scan_successful = self._perform_scan(processed_paths)
            
            if scan_successful and not self.should_stop:
                self._finalize_outputs()
                self._generate_summary_report()
                if self.checkpoint_manager:
                    self.checkpoint_manager.cleanup()
                self.logger.info("Scan completed successfully!")
                return True
            else:
                self.logger.warning("Scan was interrupted or failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Fatal error during scan: {e}", exc_info=True)
            return False
        finally:
            self._cleanup_outputs()
    
    def _validate_config(self):
        """Validate configuration parameters"""
        if not os.path.exists(self.config.scan_path):
            raise ValueError(f"Scan path does not exist: {self.config.scan_path}")
        
        if not os.path.isdir(self.config.scan_path):
            raise ValueError(f"Scan path is not a directory: {self.config.scan_path}")
        
        # Validate output formats
        valid_formats = {'json', 'ndjson', 'csv', 'markdown'}
        invalid_formats = set(self.config.output_formats) - valid_formats
        if invalid_formats:
            raise ValueError(f"Invalid output formats: {invalid_formats}")
        
        # Validate hash algorithms
        if self.config.include_hashes:
            valid_algos = {'md5', 'sha1', 'sha256', 'sha512'}
            invalid_algos = set(self.config.hash_algorithms) - valid_algos
            if invalid_algos:
                raise ValueError(f"Invalid hash algorithms: {invalid_algos}")
    
    def _initialize_output_writers(self):
        """Initialize output file writers for each format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"file_scan_{timestamp}"
        
        for fmt in self.config.output_formats:
            if fmt == 'json':
                self._init_json_writer(base_name)
            elif fmt == 'ndjson':
                self._init_ndjson_writer(base_name)
            elif fmt == 'csv':
                self._init_csv_writer(base_name)
            elif fmt == 'markdown':
                self._init_markdown_writer(base_name)
    
    def _init_json_writer(self, base_name: str):
        """Initialize JSON array writer"""
        filename = f"{base_name}.json"
        if self.config.compress_output:
            filename += ".gz"
            file_obj = gzip.open(os.path.join(self.config.output_dir, filename), 'wt')
        else:
            file_obj = open(os.path.join(self.config.output_dir, filename), 'w')
        
        file_obj.write('[\n')
        self.output_writers['json'] = {
            'file': file_obj,
            'first_entry': True,
            'filename': filename
        }
    
    def _init_ndjson_writer(self, base_name: str):
        """Initialize newline-delimited JSON writer"""
        filename = f"{base_name}.ndjson"
        if self.config.compress_output:
            filename += ".gz"
            file_obj = gzip.open(os.path.join(self.config.output_dir, filename), 'wt')
        else:
            file_obj = open(os.path.join(self.config.output_dir, filename), 'w')
        
        self.output_writers['ndjson'] = {
            'file': file_obj,
            'filename': filename
        }
    
    def _init_csv_writer(self, base_name: str):
        """Initialize CSV writer"""
        filename = f"{base_name}.csv"
        if self.config.compress_output:
            filename += ".gz"
            file_obj = gzip.open(os.path.join(self.config.output_dir, filename), 'wt', newline='')
        else:
            file_obj = open(os.path.join(self.config.output_dir, filename), 'w', newline='')
        
        # Write CSV header (registry-ready)
        fieldnames = [
            'scan_id',
            'scan_root',
            'first_seen_utc',
            'relative_path',
            'path',
            'name',
            'extension',
            'size_bytes',
            'mtime_utc',
            'created_time',
            'is_directory',
            'mime_type',
            'permissions',
            'content_hash',
            'doc_id',
            'has_id_prefix',
            'current_id_prefix',
            'needs_id',
            '0000000000000000_filename',
            'type_code',
            'ns_code',
            'scope',
            'planned_id',
            'planned_rel_path',
            'error',
            'error_kind',
        ]
        if self.config.include_hashes:
            fieldnames.extend([f'hash_{algo}' for algo in self.config.hash_algorithms])
        
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        
        self.output_writers['csv'] = {
            'file': file_obj,
            'writer': writer,
            'filename': filename,
            'fieldnames': fieldnames
        }
    
    def _init_markdown_writer(self, base_name: str):
        """Initialize Markdown report writer"""
        filename = f"{base_name}.md"
        file_obj = open(os.path.join(self.config.output_dir, filename), 'w')
        
        # Write markdown header
        file_obj.write(f"# File Scan Report\n\n")
        file_obj.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        file_obj.write(f"**Scan Path:** `{self.config.scan_path}`\n\n")
        file_obj.write(f"**Scanner Version:** {VERSION}\n\n")
        file_obj.write("## Configuration\n\n")
        file_obj.write(f"- Include Hashes: {self.config.include_hashes}\n")
        file_obj.write(f"- Hash Algorithms: {', '.join(self.config.hash_algorithms)}\n")
        file_obj.write(f"- Include Permissions: {self.config.include_permissions}\n")
        file_obj.write("\n## Scan Progress\n\n")
        
        # Inventory table (streamed; one row per file)
        file_obj.write("## Inventory\n\n")
        file_obj.write("| doc_id | relative_path | size_bytes | mtime_utc | mime_type | perms |\n")
        file_obj.write("|---|---|---:|---|---|---|\n")
        
        self.output_writers['markdown'] = {
            'file': file_obj,
            'filename': filename
        }
    
    def _perform_scan(self, skip_paths: set) -> bool:
        """Perform the actual directory traversal and file processing"""
        try:
            # Normalize output dir for exclusion check
            output_dir_abs = os.path.abspath(self.config.output_dir)
            
            for root, dirs, files in os.walk(self.config.scan_path):
                if self.should_stop:
                    break
                
                # Skip if we've already processed this directory
                if root in skip_paths:
                    dirs[:] = []  # Prune subtree
                    continue
                
                # Skip output directory if it's inside scan path
                if os.path.abspath(root).startswith(output_dir_abs):
                    dirs[:] = []  # Prune subtree
                    continue
                
                # Filter out excluded directory names
                if self.config.exclude_dir_names:
                    dirs[:] = [d for d in dirs if d.lower() not in 
                              [x.lower() for x in self.config.exclude_dir_names]]
                
                # Process directory itself
                dir_meta = self._process_directory(root)
                if dir_meta:
                    self._write_to_outputs(dir_meta)
                self.progress.update(dirs_delta=1)
                
                # Process files in directory
                for filename in files:
                    if self.should_stop:
                        break
                    
                    file_path = os.path.join(root, filename)
                    
                    # Skip if already processed
                    if file_path in skip_paths:
                        continue
                    
                    # Apply filters
                    if not self._should_process_file(file_path, filename):
                        continue
                    
                    # Process the file
                    metadata = self._process_file(file_path)
                    if metadata:
                        self._write_to_outputs(metadata)
                        if self.checkpoint_manager:
                            self.checkpoint_manager.save_checkpoint(file_path)
                        
                        self.progress.update(files_delta=1, size_delta=metadata.size_bytes)
                
                # Checkpoint directory completion
                if self.checkpoint_manager:
                    self.checkpoint_manager.save_checkpoint(root)
            
            return not self.should_stop
            
        except Exception as e:
            self.logger.error(f"Error during directory traversal: {e}", exc_info=True)
            return False
    
    def _should_process_file(self, file_path: str, filename: str) -> bool:
        """Apply file filters to determine if file should be processed"""
        try:
            # Size filters
            if self.config.min_file_size > 0 or self.config.max_file_size > 0:
                file_size = os.path.getsize(file_path)
                if self.config.min_file_size > 0 and file_size < self.config.min_file_size:
                    return False
                if self.config.max_file_size > 0 and file_size > self.config.max_file_size:
                    return False
            
            # Pattern filters
            if self.config.exclude_patterns:
                for pattern in self.config.exclude_patterns:
                    if pattern in filename.lower():
                        return False
            
            if self.config.include_patterns:
                included = False
                for pattern in self.config.include_patterns:
                    if pattern in filename.lower():
                        included = True
                        break
                if not included:
                    return False
            
            return True
            
        except OSError:
            # Allow downstream processing so we can capture an error row.
            return True
    
    def _process_directory(self, dir_path: str) -> Optional[FileMetadata]:
        """Process directory metadata (returns a registry-ready record)."""
        rel = self._norm_relpath(os.path.relpath(dir_path, self.config.scan_path))
        name = os.path.basename(dir_path) or dir_path

        # Start with minimal record so we can emit an error row if stat fails
        meta = FileMetadata(
            scan_id=self.scan_id,
            scan_root=self.scan_root,
            first_seen_utc=self.first_seen_utc,
            relative_path=rel,
            path=dir_path,
            name=name,
            extension='',
            size_bytes=0,
            is_directory=True,
        )
        self._populate_identity_fields(meta)

        try:
            stat_info = os.stat(dir_path)
            meta.mtime_utc = self._utc_iso(datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc).replace(microsecond=0))
            meta.created_time = self._utc_iso(datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc).replace(microsecond=0))
            meta.accessed_time = self._utc_iso(datetime.fromtimestamp(stat_info.st_atime, tz=timezone.utc).replace(microsecond=0))

            if self.config.include_permissions:
                meta.permissions = oct(stat_info.st_mode)[-3:]
                if hasattr(stat_info, 'st_uid') and PSUTIL_AVAILABLE:
                    try:
                        import pwd
                        meta.owner = pwd.getpwuid(stat_info.st_uid).pw_name
                    except (ImportError, KeyError):
                        pass

            # No MIME type or content_hash for directories
            return meta

        except PermissionError as e:
            self.progress.add_error('permission_denied')
            meta.error_kind = 'permission_denied'
            meta.error = str(e) or 'permission_denied'
            return meta
        except OSError as e:
            self.progress.add_error('directory_access')
            meta.error_kind = 'stat_failed'
            meta.error = str(e)
            if self.progress.error_counts['directory_access'] <= self.config.max_errors_per_type:
                self.logger.warning(f"Could not access directory {dir_path}: {e}")
            return meta
    
    def _process_file(self, file_path: str) -> FileMetadata:
        """Process individual file and extract metadata (returns a record even on error)."""
        rel = self._norm_relpath(os.path.relpath(file_path, self.config.scan_path))
        name = os.path.basename(file_path)
        ext = Path(file_path).suffix.lstrip('.').lower() if Path(file_path).suffix else ''

        # Start with minimal record so we can emit an error row if stat fails
        meta = FileMetadata(
            scan_id=self.scan_id,
            scan_root=self.scan_root,
            first_seen_utc=self.first_seen_utc,
            relative_path=rel,
            path=file_path,
            name=name,
            extension=ext,
            is_directory=False,
            is_symlink=os.path.islink(file_path)
        )
        self._populate_identity_fields(meta)

        try:
            stat_info = os.stat(file_path)
            meta.size_bytes = stat_info.st_size
            meta.mtime_utc = self._utc_iso(datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc).replace(microsecond=0))
            meta.created_time = self._utc_iso(datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc).replace(microsecond=0))
            meta.accessed_time = self._utc_iso(datetime.fromtimestamp(stat_info.st_atime, tz=timezone.utc).replace(microsecond=0))

            # Get MIME type
            meta.mime_type, _ = mimetypes.guess_type(file_path)

            # Handle symlinks
            if meta.is_symlink:
                try:
                    meta.symlink_target = os.readlink(file_path)
                except OSError:
                    pass

            # Get permissions and ownership
            if self.config.include_permissions:
                meta.permissions = oct(stat_info.st_mode)[-3:]
                if hasattr(stat_info, 'st_uid') and PSUTIL_AVAILABLE:
                    try:
                        import pwd, grp
                        meta.owner = pwd.getpwuid(stat_info.st_uid).pw_name
                        meta.group = grp.getgrgid(stat_info.st_gid).gr_name
                    except (ImportError, KeyError):
                        pass

            # Calculate required content_hash (sha256) + optional hash columns
            if not meta.is_symlink:
                algos: List[str] = []
                # content_hash (sha256) is the primary natural-key hash
                if (self.config.max_file_size_for_content_hash == 0 or
                        stat_info.st_size <= self.config.max_file_size_for_content_hash):
                    algos.append('sha256')

                # optional extra hash columns
                if self.config.include_hashes and (
                        self.config.max_file_size_for_hash == 0 or
                        stat_info.st_size <= self.config.max_file_size_for_hash):
                    for a in self.config.hash_algorithms:
                        if a not in algos:
                            algos.append(a)

                if algos:
                    try:
                        file_hashes = self._calculate_hashes(file_path, algos)
                        meta.content_hash = file_hashes.get('sha256', '')
                        if self.config.include_hashes:
                            meta.hashes = {a: file_hashes.get(a, '') for a in self.config.hash_algorithms}
                    except (PermissionError, OSError) as e:
                        self.progress.add_error('hash_failed')
                        meta.error_kind = meta.error_kind or 'hash_failed'
                        meta.error = meta.error or str(e)

            return meta

        except PermissionError as e:
            self.progress.add_error('permission_denied')
            meta.error_kind = 'permission_denied'
            meta.error = str(e) or 'permission_denied'
            if self.progress.error_counts['permission_denied'] <= self.config.max_errors_per_type:
                self.logger.warning(f"Permission denied: {file_path}")
            return meta
        except OSError as e:
            self.progress.add_error('file_access')
            meta.error_kind = 'stat_failed'
            meta.error = str(e)
            if self.progress.error_counts['file_access'] <= self.config.max_errors_per_type:
                self.logger.warning(f"Could not access file {file_path}: {e}")
            return meta
        except Exception as e:
            self.progress.add_error('unexpected')
            meta.error_kind = 'unexpected'
            meta.error = str(e)
            self.logger.error(f"Unexpected error processing {file_path}: {e}")
            return meta
    
    def _calculate_hashes(self, file_path: str, algorithms: List[str]) -> Dict[str, str]:
        """Calculate file hashes for the requested algorithms in a single pass."""
        hashes: Dict[str, str] = {}
        hash_objects: Dict[str, Any] = {}

        # Initialize hash objects
        for algo in algorithms:
            hash_objects[algo] = hashlib.new(algo)
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            chunk_size = 64 * 1024  # 64KB chunks
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                for hash_obj in hash_objects.values():
                    hash_obj.update(chunk)

        # Get final hash values
        for algo, hash_obj in hash_objects.items():
            hashes[algo] = hash_obj.hexdigest()
        
        return hashes
    
    def _write_to_outputs(self, metadata: FileMetadata):
        """Write metadata to all configured output formats"""
        try:
            # Convert to dictionary for easier handling
            data = asdict(metadata)
            
            # Write to JSON
            if 'json' in self.output_writers:
                writer = self.output_writers['json']
                if not writer['first_entry']:
                    writer['file'].write(',\n')
                json.dump(data, writer['file'], indent=2)
                writer['first_entry'] = False
            
            # Write to NDJSON
            if 'ndjson' in self.output_writers:
                writer = self.output_writers['ndjson']
                writer['file'].write(json.dumps(data) + '\n')
            
            # Write to CSV
            if 'csv' in self.output_writers:
                writer = self.output_writers['csv']
                fieldnames = writer.get('fieldnames') or getattr(writer['writer'], 'fieldnames', [])
                hashes = data.get('hashes') or {}

                csv_row: Dict[str, Any] = {}
                for col in fieldnames:
                    if col == '0000000000000000_filename':
                        has_prefix = bool(data.get('has_id_prefix', False))
                        nm = data.get('name', '') or ''
                        csv_row[col] = nm if has_prefix else f"{self.config.id_placeholder}_{nm}"
                        continue
                    if col.startswith('hash_'):
                        algo = col[len('hash_'):]
                        csv_row[col] = hashes.get(algo, '')
                        continue
                    val = data.get(col, '')
                    csv_row[col] = '' if val is None else val

                writer['writer'].writerow(csv_row)
            
            # Write to Markdown (files only; avoid huge directory spam)
            if 'markdown' in self.output_writers and not data.get('is_directory', False):
                md = self.output_writers['markdown']['file']
                doc_id = data.get('doc_id') or ""
                rel = (data.get('relative_path') or data.get('path') or "").replace("\\", "/")
                size = data.get('size_bytes', 0)
                mtime = data.get('mtime_utc', "")
                mime = data.get('mime_type') or ""
                perms = data.get('permissions') or ""
                # basic escaping for markdown tables
                rel = rel.replace("|", "\\|")
                mime = mime.replace("|", "\\|")
                md.write(f"| {doc_id} | `{rel}` | {size} | {mtime} | {mime} | {perms} |\n")
            
        except Exception as e:
            self.logger.error(f"Error writing output for {metadata.path}: {e}")
    
    def _finalize_outputs(self):
        """Finalize output files"""
        # Flush all writers before closing
        for writer_info in self.output_writers.values():
            try:
                writer_info['file'].flush()
            except:
                pass
        
        # Close JSON array
        if 'json' in self.output_writers:
            self.output_writers['json']['file'].write('\n]')
        
        # Add summary to markdown
        if 'markdown' in self.output_writers:
            summary = self.progress.get_summary()
            md_file = self.output_writers['markdown']['file']
            md_file.write("\n## Scan Summary\n\n")
            md_file.write(f"- **Files Processed:** {summary['files_processed']:,}\n")
            md_file.write(f"- **Directories Processed:** {summary['directories_processed']:,}\n")
            md_file.write(f"- **Total Size:** {summary['total_size_bytes'] / (1024**3):.2f} GB\n")
            md_file.write(f"- **Elapsed Time:** {summary['elapsed_seconds']:.1f} seconds\n")
            md_file.write(f"- **Average Rate:** {summary['average_rate']:.1f} files/second\n")
            
            if summary['error_counts']:
                md_file.write("\n### Errors Encountered\n\n")
                for error_type, count in summary['error_counts'].items():
                    md_file.write(f"- **{error_type}:** {count:,}\n")
    
    def _cleanup_outputs(self):
        """Close all output files"""
        for writer_info in self.output_writers.values():
            try:
                writer_info['file'].close()
            except:
                pass
    
    def _generate_summary_report(self):
        """Generate final summary report"""
        summary = self.progress.get_summary()
        
        self.logger.info("=" * 50)
        self.logger.info("SCAN COMPLETE - SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Files processed: {summary['files_processed']:,}")
        self.logger.info(f"Directories processed: {summary['directories_processed']:,}")
        self.logger.info(f"Total size: {summary['total_size_bytes'] / (1024**3):.2f} GB")
        self.logger.info(f"Elapsed time: {summary['elapsed_seconds']:.1f} seconds")
        self.logger.info(f"Average rate: {summary['average_rate']:.1f} files/second")
        
        if summary['error_counts']:
            self.logger.info("\nErrors encountered:")
            for error_type, count in summary['error_counts'].items():
                self.logger.info(f"  {error_type}: {count:,}")
        
        self.logger.info("\nOutput files generated:")
        for writer_info in self.output_writers.values():
            output_path = os.path.join(self.config.output_dir, writer_info['filename'])
            file_size = os.path.getsize(output_path) / (1024**2)  # MB
            self.logger.info(f"  {writer_info['filename']} ({file_size:.1f} MB)")

def create_user_config() -> ScanConfig:
    """Create configuration from user-defined constants"""
    return ScanConfig(
        scan_path=os.path.abspath(SCAN_PATH),
        output_dir=os.path.abspath(OUTPUT_DIR),
        output_formats=OUTPUT_FORMATS,
        include_hashes=INCLUDE_HASHES,
        hash_algorithms=HASH_ALGORITHMS,
        max_file_size_for_content_hash=MAX_FILE_SIZE_FOR_CONTENT_HASH,
        include_permissions=INCLUDE_PERMISSIONS,
        include_extended_attrs=INCLUDE_EXTENDED_ATTRS,
        max_file_size_for_hash=MAX_FILE_SIZE_FOR_HASH,
        min_file_size=MIN_FILE_SIZE,
        max_file_size=MAX_FILE_SIZE,
        exclude_patterns=[p.lower() for p in EXCLUDE_PATTERNS],
        exclude_dir_names=[d.lower() for d in EXCLUDE_DIR_NAMES],
        include_patterns=[p.lower() for p in INCLUDE_PATTERNS],
        progress_interval=PROGRESS_INTERVAL,
        checkpoint_interval=CHECKPOINT_INTERVAL,
        compress_output=COMPRESS_OUTPUT,
        resume_from_checkpoint=RESUME_FROM_CHECKPOINT,
        max_errors_per_type=MAX_ERRORS_PER_TYPE,
        identity_config_path=(IDENTITY_CONFIG_PATH or None),
        id_regex=ID_REGEX,
        id_placeholder=ID_PLACEHOLDER,
        default_scope=DEFAULT_SCOPE
    )

def create_default_config() -> ScanConfig:
    """Create default configuration (fallback)"""
    # Use platform-appropriate default paths
    if platform.system() == "Windows":
        default_output = os.path.join(os.path.expanduser('~'), 'Documents', 'FileScanOutput')
    else:
        default_output = os.path.join(os.path.expanduser('~'), 'file_scan_output')
    
    return ScanConfig(
        scan_path=os.path.expanduser('~'),
        output_dir=default_output,
        output_formats=['json', 'markdown'],
        include_hashes=False,
        hash_algorithms=['sha256'],
        include_permissions=True,
        max_file_size_for_hash=50 * 1024 * 1024,  # 50MB
        progress_interval=2.0,
        checkpoint_interval=1000,
        compress_output=False,
        resume_from_checkpoint=True
    )

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Enhanced File Scanner v2.0 - Comprehensive file metadata collection"
    )
    
    parser.add_argument('scan_path', nargs='?', 
                       help='Directory to scan (overrides script configuration)')
    parser.add_argument('-o', '--output-dir', 
                       help='Output directory for results (overrides script configuration)')
    parser.add_argument('-f', '--formats', nargs='+', 
                       choices=['json', 'ndjson', 'csv', 'markdown'],
                       help='Output formats (overrides script configuration)')
    parser.add_argument('--include-hashes', action='store_true',
                       help='Calculate file hashes (overrides script configuration)')
    parser.add_argument('--hash-algorithms', nargs='+',
                       choices=['md5', 'sha1', 'sha256', 'sha512'],
                       help='Hash algorithms to use (overrides script configuration)')
    parser.add_argument('--identity-config',
                       help='Optional JSON identity config (id_regex, placeholder_id, type_code_by_extension, ns_code_by_top_dir, scope_by_ns_code)')
    parser.add_argument('--no-permissions', action='store_true',
                       help='Skip permission information')
    parser.add_argument('--compress', action='store_true',
                       help='Compress output files')
    parser.add_argument('--no-resume', action='store_true',
                       help='Disable resume capability')
    parser.add_argument('--min-size', type=int,
                       help='Minimum file size to process (bytes)')
    parser.add_argument('--max-size', type=int,
                       help='Maximum file size to process (bytes, 0=no limit)')
    parser.add_argument('--exclude', nargs='+',
                       help='Filename patterns to exclude')
    parser.add_argument('--include', nargs='+',
                       help='Filename patterns to include (others excluded)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    
    args = parser.parse_args()
    
    # Start with user configuration from script constants
    config = create_user_config()
    
    # Override with command line arguments if provided
    if args.scan_path:
        config.scan_path = os.path.abspath(args.scan_path)
    if args.output_dir:
        config.output_dir = args.output_dir
    if args.formats:
        config.output_formats = args.formats
    if args.include_hashes:
        config.include_hashes = True
    if args.hash_algorithms:
        config.hash_algorithms = args.hash_algorithms
    if args.identity_config:
        config.identity_config_path = args.identity_config
    if args.no_permissions:
        config.include_permissions = False
    if args.compress:
        config.compress_output = True
    if args.no_resume:
        config.resume_from_checkpoint = False
    if args.min_size is not None:
        config.min_file_size = args.min_size
    if args.max_size is not None:
        config.max_file_size = args.max_size
    if args.exclude:
        config.exclude_patterns = [p.lower() for p in args.exclude]
    if args.include:
        config.include_patterns = [p.lower() for p in args.include]
    
    # Check for psutil if advanced features are needed
    if not PSUTIL_AVAILABLE and (config.include_permissions or config.resume_from_checkpoint):
        print("Warning: psutil not available. Some features may be limited.")
        print("Install with: pip install psutil")
    
    # Create and run scanner
    scanner = EnhancedFileScanner(config)
    
    print(f"Enhanced File Scanner v{VERSION}")
    print("=" * 50)
    print(f"Scanning: {config.scan_path}")
    print(f"Output: {config.output_dir}")
    print(f"Formats: {', '.join(config.output_formats)}")
    print(f"Include Hashes: {config.include_hashes}")
    if config.include_hashes:
        print(f"Hash Algorithms: {', '.join(config.hash_algorithms)}")
    print()
    
    success = scanner.scan()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()