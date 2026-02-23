"""Transactional multi-step operations with rollback (GAP-007).

FILE_ID: 01999000042260125110
PURPOSE: Atomic multi-step operations with automatic rollback
PHASE: Phase 7 - Transaction Safety
BACKLOG: 01999000042260125103 GAP-007

Provides transaction coordinator for multi-step operations:
- Begin/commit/rollback semantics
- Operation logging with snapshots
- Automatic restoration on failure
- Transaction evidence
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@dataclass
class TransactionOperation:
    """Single operation within a transaction."""
    op_type: str  # file_rename, file_delete, file_create, registry_patch, etc.
    target: str
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    timestamp: str
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Transaction:
    """Complete transaction record."""
    transaction_id: str
    started_at: str
    status: str  # active, committed, rolled_back
    operations: List[TransactionOperation] = field(default_factory=list)
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['operations'] = [op.to_dict() if hasattr(op, 'to_dict') else op for op in self.operations]
        return result


class TransactionCoordinator:
    """Manages atomic multi-step operations with rollback.
    
    Provides ACID semantics for complex operations:
    - Atomicity: All or nothing
    - Consistency: Maintains invariants
    - Isolation: Sequential execution
    - Durability: Transaction log persistence
    """
    
    def __init__(
        self,
        project_root: Path,
        transaction_dir: Optional[Path] = None
    ):
        """Initialize transaction coordinator.
        
        Args:
            project_root: Project root directory
            transaction_dir: Directory for transaction logs
        """
        self.project_root = project_root
        
        if transaction_dir is None:
            transaction_dir = project_root / ".state" / "transactions"
        self.transaction_dir = transaction_dir
        
        # Create transaction subdirectories
        self.active_dir = transaction_dir / "active"
        self.committed_dir = transaction_dir / "committed"
        self.rolled_back_dir = transaction_dir / "rolled_back"
        
        for directory in [self.active_dir, self.committed_dir, self.rolled_back_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.current_transaction: Optional[Transaction] = None
    
    def begin_transaction(self, transaction_id: Optional[str] = None) -> str:
        """Begin a new transaction.
        
        Args:
            transaction_id: Optional transaction ID (generates if None)
            
        Returns:
            Transaction ID
            
        Raises:
            RuntimeError: If transaction already active
        """
        if self.current_transaction:
            raise RuntimeError(f"Transaction {self.current_transaction.transaction_id} already active")
        
        if transaction_id is None:
            transaction_id = f"tx_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S%f')}"
        
        self.current_transaction = Transaction(
            transaction_id=transaction_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="active"
        )
        
        # Save initial transaction log
        self._save_transaction_log()
        
        return transaction_id
    
    def record_operation(
        self,
        op_type: str,
        target: str,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None
    ):
        """Record an operation in the current transaction.
        
        Args:
            op_type: Operation type (file_rename, registry_patch, etc.)
            target: Target of operation (file path, etc.)
            before_state: State before operation
            after_state: State after operation
            
        Raises:
            RuntimeError: If no transaction active
        """
        if not self.current_transaction:
            raise RuntimeError("No active transaction")
        
        operation = TransactionOperation(
            op_type=op_type,
            target=target,
            before_state=before_state,
            after_state=after_state,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        self.current_transaction.operations.append(operation)
        
        # Update transaction log
        self._save_transaction_log()
    
    def commit(self):
        """Commit the current transaction.
        
        Marks transaction as completed and archives log.
        
        Raises:
            RuntimeError: If no transaction active
        """
        if not self.current_transaction:
            raise RuntimeError("No active transaction")
        
        self.current_transaction.status = "committed"
        self.current_transaction.completed_at = datetime.now(timezone.utc).isoformat()
        
        # Move transaction log to committed
        active_log = self.active_dir / f"{self.current_transaction.transaction_id}.json"
        committed_log = self.committed_dir / f"{self.current_transaction.transaction_id}.json"
        
        with open(committed_log, 'w', encoding='utf-8') as f:
            json.dump(self.current_transaction.to_dict(), f, indent=2)
        
        if active_log.exists():
            active_log.unlink()
        
        self.current_transaction = None
    
    def rollback(self):
        """Rollback the current transaction.
        
        Restores all before states by reversing operations in reverse order.
        
        Raises:
            RuntimeError: If no transaction active
        """
        if not self.current_transaction:
            raise RuntimeError("No active transaction")
        
        errors = []
        
        # Rollback operations in reverse order
        for operation in reversed(self.current_transaction.operations):
            try:
                self._rollback_operation(operation)
            except Exception as e:
                errors.append(f"Failed to rollback {operation.op_type} on {operation.target}: {e}")
        
        self.current_transaction.status = "rolled_back"
        self.current_transaction.completed_at = datetime.now(timezone.utc).isoformat()
        if errors:
            self.current_transaction.error_message = "; ".join(errors)
        
        # Move transaction log to rolled_back
        active_log = self.active_dir / f"{self.current_transaction.transaction_id}.json"
        rolled_back_log = self.rolled_back_dir / f"{self.current_transaction.transaction_id}.json"
        
        with open(rolled_back_log, 'w', encoding='utf-8') as f:
            json.dump(self.current_transaction.to_dict(), f, indent=2)
        
        if active_log.exists():
            active_log.unlink()
        
        self.current_transaction = None
    
    def _rollback_operation(self, operation: TransactionOperation):
        """Rollback a single operation."""
        if operation.op_type == "file_rename":
            # Reverse rename
            if operation.before_state and operation.after_state:
                old_path = Path(operation.before_state['path'])
                new_path = Path(operation.after_state['path'])
                if new_path.exists():
                    shutil.move(str(new_path), str(old_path))
        
        elif operation.op_type == "file_create":
            # Delete created file
            file_path = Path(operation.target)
            if file_path.exists():
                file_path.unlink()
        
        elif operation.op_type == "file_delete":
            # Restore deleted file from snapshot
            if operation.before_state and 'content' in operation.before_state:
                file_path = Path(operation.target)
                file_path.write_text(operation.before_state['content'], encoding='utf-8')
        
        elif operation.op_type == "file_modify":
            # Restore previous content
            if operation.before_state and 'content' in operation.before_state:
                file_path = Path(operation.target)
                file_path.write_text(operation.before_state['content'], encoding='utf-8')
        
        elif operation.op_type == "registry_patch":
            # Would need registry writer to reverse patch
            pass
    
    def _save_transaction_log(self):
        """Save current transaction log to active directory."""
        if not self.current_transaction:
            return
        
        log_file = self.active_dir / f"{self.current_transaction.transaction_id}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_transaction.to_dict(), f, indent=2)
    
    @contextmanager
    def transaction(self, transaction_id: Optional[str] = None):
        """Context manager for transactions.
        
        Usage:
            with coordinator.transaction() as tx_id:
                # Do operations
                coordinator.record_operation(...)
        
        Automatically commits on success, rolls back on exception.
        """
        tx_id = self.begin_transaction(transaction_id)
        try:
            yield tx_id
            self.commit()
        except Exception as e:
            self.rollback()
            raise


def create_snapshot(file_path: Path) -> Dict[str, Any]:
    """Create snapshot of file for rollback.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with file metadata and content
    """
    if not file_path.exists():
        return {"exists": False}
    
    snapshot = {
        "exists": True,
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "modified_time": file_path.stat().st_mtime
    }
    
    # Read content for small files
    if file_path.stat().st_size < 1024 * 1024:  # 1MB
        try:
            snapshot["content"] = file_path.read_text(encoding='utf-8')
        except Exception:
            # Binary or unreadable
            snapshot["content_binary"] = True
    
    return snapshot


if __name__ == "__main__":
    # CLI entry point for transaction recovery
    import argparse
    
    parser = argparse.ArgumentParser(description="Transaction coordinator utilities")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--list", action="store_true", help="List active transactions")
    parser.add_argument("--rollback", help="Rollback transaction by ID")
    
    args = parser.parse_args()
    
    coordinator = TransactionCoordinator(args.project_root)
    
    if args.list:
        active_txs = list(coordinator.active_dir.glob("*.json"))
        print(f"Active transactions: {len(active_txs)}")
        for tx_file in active_txs:
            with open(tx_file, 'r', encoding='utf-8') as f:
                tx = json.load(f)
            print(f"  {tx['transaction_id']}: {len(tx['operations'])} operations")
    
    elif args.rollback:
        # Load transaction and rollback
        tx_file = coordinator.active_dir / f"{args.rollback}.json"
        if not tx_file.exists():
            print(f"Transaction {args.rollback} not found")
        else:
            with open(tx_file, 'r', encoding='utf-8') as f:
                tx_data = json.load(f)
            
            coordinator.current_transaction = Transaction(**tx_data)
            coordinator.current_transaction.operations = [
                TransactionOperation(**op) for op in tx_data['operations']
            ]
            
            print(f"Rolling back transaction {args.rollback}...")
            coordinator.rollback()
            print("Rollback complete")
