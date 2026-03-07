# DOC_LINK: DOC-CORE-CORE-TRACE-STORAGE-1151
"""Trace Storage - persistent storage for execution traces and audit logs."""
DOC_ID: DOC-CORE-CORE-TRACE-STORAGE-1151

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.core.exceptions import StorageError

Base = declarative_base()


class ExecutionTrace(Base):
    """SQLAlchemy model for execution traces."""

    __tablename__ = "execution_traces"

    trace_id = Column(String(36), primary_key=True)
    ccis_id = Column(String(50), nullable=False, index=True)
    project_id = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    seed = Column(Integer, nullable=False)

    # JSON-serialized data
    input_ccis = Column(Text, nullable=False)  # JSON
    output_psjp = Column(Text, nullable=True)  # JSON
    events = Column(Text, nullable=False)  # JSON array
    metadata = Column(Text, nullable=True)  # JSON

    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ExecutionTrace(trace_id='{self.trace_id}', ccis_id='{self.ccis_id}')>"


class StageSnapshot(Base):
    """SQLAlchemy model for individual stage snapshots."""

    __tablename__ = "stage_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(36), nullable=False, index=True)
    stage_name = Column(String(20), nullable=False, index=True)
    stage_index = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    success = Column(Boolean, nullable=False, default=False)

    input_data = Column(Text, nullable=False)  # JSON
    output_data = Column(Text, nullable=True)  # JSON
    events = Column(Text, nullable=False)  # JSON array

    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<StageSnapshot(trace_id='{self.trace_id}', stage='{self.stage_name}')>"


class TraceStorage:
    """Manages persistent storage of execution traces.

    Provides CRUD operations for storing and retrieving pipeline execution traces,
    enabling replay and audit capabilities.
    """

    def __init__(self, database_url: str = "sqlite:///data/audit.db") -> None:
        """Initialize trace storage.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def _get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy Session
        """
        return self.SessionLocal()

    def store_trace(
        self,
        trace_id: str,
        ccis_id: str,
        project_id: str,
        seed: int,
        input_ccis: Dict[str, Any],
        output_psjp: Optional[Dict[str, Any]],
        events: List[Dict[str, Any]],
        started_at: datetime,
        completed_at: Optional[datetime],
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a complete execution trace.

        Args:
            trace_id: Unique trace identifier
            ccis_id: CCIS identifier
            project_id: Project identifier
            seed: Deterministic seed used
            input_ccis: Input CCIS data
            output_psjp: Output PSJP data (if successful)
            events: List of event dictionaries
            started_at: Execution start time
            completed_at: Execution completion time
            success: Whether execution succeeded
            error_message: Optional error message
            metadata: Optional additional metadata

        Raises:
            StorageError: If storage operation fails
        """
        session = self._get_session()
        try:
            trace = ExecutionTrace(
                trace_id=trace_id,
                ccis_id=ccis_id,
                project_id=project_id,
                seed=seed,
                input_ccis=json.dumps(input_ccis),
                output_psjp=json.dumps(output_psjp) if output_psjp else None,
                events=json.dumps(events),
                started_at=started_at,
                completed_at=completed_at,
                success=success,
                error_message=error_message,
                metadata=json.dumps(metadata) if metadata else None,
            )

            session.add(trace)
            session.commit()

        except Exception as e:
            session.rollback()
            raise StorageError(f"Failed to store trace: {e}")
        finally:
            session.close()

    def store_stage_snapshot(
        self,
        trace_id: str,
        stage_name: str,
        stage_index: int,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        events: List[Dict[str, Any]],
        started_at: datetime,
        completed_at: Optional[datetime],
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """Store a stage snapshot.

        Args:
            trace_id: Parent trace identifier
            stage_name: Pipeline stage name
            stage_index: Stage index in pipeline
            input_data: Stage input data
            output_data: Stage output data (if successful)
            events: Stage-specific events
            started_at: Stage start time
            completed_at: Stage completion time
            success: Whether stage succeeded
            error_message: Optional error message

        Raises:
            StorageError: If storage operation fails
        """
        session = self._get_session()
        try:
            snapshot = StageSnapshot(
                trace_id=trace_id,
                stage_name=stage_name,
                stage_index=stage_index,
                input_data=json.dumps(input_data),
                output_data=json.dumps(output_data) if output_data else None,
                events=json.dumps(events),
                started_at=started_at,
                completed_at=completed_at,
                success=success,
                error_message=error_message,
            )

            session.add(snapshot)
            session.commit()

        except Exception as e:
            session.rollback()
            raise StorageError(f"Failed to store stage snapshot: {e}")
        finally:
            session.close()

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a trace by ID.

        Args:
            trace_id: Trace identifier

        Returns:
            Trace data dictionary, or None if not found
        """
        session = self._get_session()
        try:
            trace = session.query(ExecutionTrace).filter_by(trace_id=trace_id).first()

            if not trace:
                return None

            return {
                "trace_id": trace.trace_id,
                "ccis_id": trace.ccis_id,
                "project_id": trace.project_id,
                "seed": trace.seed,
                "input_ccis": json.loads(trace.input_ccis),
                "output_psjp": json.loads(trace.output_psjp) if trace.output_psjp else None,
                "events": json.loads(trace.events),
                "started_at": trace.started_at,
                "completed_at": trace.completed_at,
                "success": trace.success,
                "error_message": trace.error_message,
                "metadata": json.loads(trace.metadata) if trace.metadata else None,
            }

        finally:
            session.close()

    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        project_id: Optional[str] = None,
        success_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """List execution traces.

        Args:
            limit: Maximum number of traces to return
            offset: Number of traces to skip
            project_id: Optional filter by project ID
            success_only: If True, only return successful traces

        Returns:
            List of trace summary dictionaries
        """
        session = self._get_session()
        try:
            query = session.query(ExecutionTrace)

            if project_id:
                query = query.filter_by(project_id=project_id)

            if success_only:
                query = query.filter_by(success=True)

            query = query.order_by(ExecutionTrace.started_at.desc())
            query = query.limit(limit).offset(offset)

            traces = query.all()

            return [
                {
                    "trace_id": t.trace_id,
                    "ccis_id": t.ccis_id,
                    "project_id": t.project_id,
                    "started_at": t.started_at,
                    "completed_at": t.completed_at,
                    "success": t.success,
                    "seed": t.seed,
                }
                for t in traces
            ]

        finally:
            session.close()

    def get_stage_snapshots(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all stage snapshots for a trace.

        Args:
            trace_id: Trace identifier

        Returns:
            List of stage snapshot dictionaries
        """
        session = self._get_session()
        try:
            snapshots = (
                session.query(StageSnapshot)
                .filter_by(trace_id=trace_id)
                .order_by(StageSnapshot.stage_index)
                .all()
            )

            return [
                {
                    "stage_name": s.stage_name,
                    "stage_index": s.stage_index,
                    "input_data": json.loads(s.input_data),
                    "output_data": json.loads(s.output_data) if s.output_data else None,
                    "events": json.loads(s.events),
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "success": s.success,
                    "error_message": s.error_message,
                }
                for s in snapshots
            ]

        finally:
            session.close()

    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace and its snapshots.

        Args:
            trace_id: Trace identifier

        Returns:
            True if deleted, False if not found

        Raises:
            StorageError: If deletion fails
        """
        session = self._get_session()
        try:
            # Delete stage snapshots first
            session.query(StageSnapshot).filter_by(trace_id=trace_id).delete()

            # Delete trace
            deleted = session.query(ExecutionTrace).filter_by(trace_id=trace_id).delete()

            session.commit()
            return deleted > 0

        except Exception as e:
            session.rollback()
            raise StorageError(f"Failed to delete trace: {e}")
        finally:
            session.close()

    def cleanup_old_traces(self, days: int = 90) -> int:
        """Delete traces older than specified days.

        Args:
            days: Number of days to retain

        Returns:
            Number of traces deleted

        Raises:
            StorageError: If cleanup fails
        """
        session = self._get_session()
        try:
            cutoff_date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

            # Get trace IDs to delete
            traces = (
                session.query(ExecutionTrace.trace_id)
                .filter(ExecutionTrace.started_at < cutoff_date)
                .all()
            )

            trace_ids = [t.trace_id for t in traces]

            # Delete snapshots
            for trace_id in trace_ids:
                session.query(StageSnapshot).filter_by(trace_id=trace_id).delete()

            # Delete traces
            deleted = (
                session.query(ExecutionTrace)
                .filter(ExecutionTrace.started_at < cutoff_date)
                .delete()
            )

            session.commit()
            return deleted

        except Exception as e:
            session.rollback()
            raise StorageError(f"Failed to cleanup old traces: {e}")
        finally:
            session.close()
