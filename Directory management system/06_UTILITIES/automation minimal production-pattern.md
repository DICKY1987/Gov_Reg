Below is a minimal, production-pattern “library + thin runner” skeleton that makes automation objectively testable. It includes:

* `ExecutionPlan`, `Step`, `Gate` (complete schema + deterministic plan hash)
* `Ops` interfaces + `RealOps` + `FakeOps`
* One example trigger handler (`FILE_IDENTITY_CREATE`) with `plan()` + `execute()`
* `pytest` tests for:

  * Layer 2: plan determinism/hash + plan validation
  * Layer 3: sandbox e2e execution in workspace
  * Layer 5: negative path (forced gate fail) + rollback verification

You can paste these files into a repo and run `pytest`.

---

## File layout

```
src/
  automation/
    core.py
    ops.py
    workspace.py
    triggers/
      file_identity_create.py
tests/
  test_layer2_plan.py
  test_layer3_sandbox.py
  test_layer5_negative_rollback.py
```

---

## src/automation/core.py

```python
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Tuple
from pathlib import Path
import json
import hashlib
import time


# -----------------------
# Events
# -----------------------

@dataclass(frozen=True)
class Event:
    event_type: str
    trigger_id: str
    run_id: str
    step_id: str
    timestamp_ms: int
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    duration_ms: Optional[int] = None


# -----------------------
# Gate protocol
# -----------------------

@dataclass(frozen=True)
class GateResult:
    gate_id: str
    passed: bool
    reason: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


class Gate(Protocol):
    gate_id: str

    def check(self, ctx: "ExecutionContext") -> GateResult:
        ...


# -----------------------
# Plan schema
# -----------------------

@dataclass(frozen=True)
class Step:
    step_id: str
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected_outputs: List[str] = field(default_factory=list)
    gate_ids: List[str] = field(default_factory=list)
    rollback_action: Optional[str] = None  # Name of rollback handler in executor


@dataclass
class ExecutionPlan:
    plan_id: str
    trigger_id: str
    steps: List[Step]
    required_tools: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.plan_id:
            errors.append("plan_id missing")
        if not self.trigger_id:
            errors.append("trigger_id missing")
        if not self.steps:
            errors.append("no steps")

        step_ids = [s.step_id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("duplicate step_id found")

        # Minimal structural checks
        for s in self.steps:
            if not s.step_id:
                errors.append("step has empty step_id")
            if not s.action:
                errors.append(f"step {s.step_id} missing action")
        return errors

    def stable_dict(self) -> Dict[str, Any]:
        # Deterministic serialization for hashing
        d = asdict(self)
        return d

    def hash(self) -> str:
        payload = json.dumps(self.stable_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


# -----------------------
# Execution
# -----------------------

@dataclass
class ExecutionResult:
    trigger_id: str
    run_id: str
    success: bool
    artifacts: Dict[str, str] = field(default_factory=dict)  # artifact_id -> path
    gate_results: List[GateResult] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ExecutionContext:
    trigger_id: str
    run_id: str
    workspace: "Workspace"
    ops: "Ops"
    config: Dict[str, Any]
    gates: Dict[str, Gate]  # gate_id -> instance


def now_ms() -> int:
    return int(time.time() * 1000)


def emit(ctx: ExecutionContext, event_type: str, step_id: str, payload: Dict[str, Any], duration_ms: Optional[int] = None):
    evt = Event(
        event_type=event_type,
        trigger_id=ctx.trigger_id,
        run_id=ctx.run_id,
        step_id=step_id,
        timestamp_ms=now_ms(),
        payload=payload,
        duration_ms=duration_ms,
    )
    ctx.ops.evidence.emit(evt)


class StepExecutor(Protocol):
    def execute(self, plan: ExecutionPlan, ctx: ExecutionContext) -> ExecutionResult:
        ...
```

---

## src/automation/ops.py

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence
from pathlib import Path
import json
import subprocess


# -----------------------
# Protocols
# -----------------------

class FileSystemOps(Protocol):
    def read_text(self, path: Path) -> str: ...
    def write_text(self, path: Path, content: str) -> None: ...
    def exists(self, path: Path) -> bool: ...
    def mkdir(self, path: Path, parents: bool = True) -> None: ...
    def list_dir(self, path: Path) -> List[Path]: ...
    def delete(self, path: Path) -> None: ...
    def move(self, src: Path, dst: Path) -> None: ...


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


class ProcessOps(Protocol):
    def run(self, cmd: Sequence[str], cwd: Optional[Path] = None) -> ProcessResult: ...
    def check_installed(self, tool: str) -> bool: ...


class RegistryOps(Protocol):
    def read_registry(self, path: Path) -> Dict[str, Any]: ...
    def write_registry(self, path: Path, data: Dict[str, Any]) -> None: ...
    def apply_patch_append_file_record(self, registry_path: Path, record: Dict[str, Any]) -> None: ...


class EvidenceOps(Protocol):
    def emit(self, event: Any) -> None: ...
    def all_events(self) -> List[Any]: ...
    def flush_jsonl(self, path: Path) -> None: ...


@dataclass
class Ops:
    fs: FileSystemOps
    proc: ProcessOps
    registry: RegistryOps
    evidence: EvidenceOps


# -----------------------
# Real implementations
# -----------------------

class RealFS:
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def exists(self, path: Path) -> bool:
        return path.exists()

    def mkdir(self, path: Path, parents: bool = True) -> None:
        path.mkdir(parents=parents, exist_ok=True)

    def list_dir(self, path: Path) -> List[Path]:
        return list(path.iterdir())

    def delete(self, path: Path) -> None:
        if path.is_dir():
            for p in path.iterdir():
                self.delete(p)
            path.rmdir()
        elif path.exists():
            path.unlink()

    def move(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.replace(dst)


class RealProc:
    def run(self, cmd, cwd: Optional[Path] = None) -> ProcessResult:
        p = subprocess.run(
            list(cmd),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
        )
        return ProcessResult(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)

    def check_installed(self, tool: str) -> bool:
        # Minimal heuristic: try running "<tool> --version"
        try:
            r = self.run([tool, "--version"])
            return r.returncode == 0
        except Exception:
            return False


class RealRegistry:
    def read_registry(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"files": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def write_registry(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def apply_patch_append_file_record(self, registry_path: Path, record: Dict[str, Any]) -> None:
        reg = self.read_registry(registry_path)
        reg.setdefault("files", [])
        reg["files"].append(record)
        self.write_registry(registry_path, reg)


class RealEvidence:
    def __init__(self):
        self._events: List[Any] = []

    def emit(self, event: Any) -> None:
        self._events.append(event)

    def all_events(self) -> List[Any]:
        return list(self._events)

    def flush_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for e in self._events:
                f.write(json.dumps(e.__dict__, sort_keys=True) + "\n")


def make_real_ops() -> Ops:
    return Ops(fs=RealFS(), proc=RealProc(), registry=RealRegistry(), evidence=RealEvidence())


# -----------------------
# Fake implementations
# -----------------------

class FakeFS:
    """
    A minimal in-memory filesystem for unit tests.
    Supports read/write/exists/move/delete for file paths.
    Directory semantics are simplified.
    """
    def __init__(self):
        self._files: Dict[str, str] = {}

    def _k(self, path: Path) -> str:
        return str(path).replace("\\", "/")

    def read_text(self, path: Path) -> str:
        k = self._k(path)
        if k not in self._files:
            raise FileNotFoundError(k)
        return self._files[k]

    def write_text(self, path: Path, content: str) -> None:
        self._files[self._k(path)] = content

    def exists(self, path: Path) -> bool:
        k = self._k(path)
        if k in self._files:
            return True
        # treat any "dir" as exists if any file has that prefix
        prefix = k.rstrip("/") + "/"
        return any(p.startswith(prefix) for p in self._files.keys())

    def mkdir(self, path: Path, parents: bool = True) -> None:
        # no-op in fake
        return

    def list_dir(self, path: Path) -> List[Path]:
        k = self._k(path).rstrip("/") + "/"
        children = set()
        for p in self._files.keys():
            if p.startswith(k):
                rest = p[len(k):]
                first = rest.split("/", 1)[0]
                children.add(Path(k + first))
        return sorted(children)

    def delete(self, path: Path) -> None:
        k = self._k(path)
        if k in self._files:
            del self._files[k]
            return
        prefix = k.rstrip("/") + "/"
        for p in list(self._files.keys()):
            if p.startswith(prefix):
                del self._files[p]

    def move(self, src: Path, dst: Path) -> None:
        ks = self._k(src)
        kd = self._k(dst)
        if ks not in self._files:
            raise FileNotFoundError(ks)
        self._files[kd] = self._files.pop(ks)


class FakeProc:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.installed: Dict[str, bool] = {}

    def run(self, cmd, cwd: Optional[Path] = None) -> ProcessResult:
        self.calls.append({"cmd": list(cmd), "cwd": str(cwd) if cwd else None})
        return ProcessResult(returncode=0, stdout="", stderr="")

    def check_installed(self, tool: str) -> bool:
        return self.installed.get(tool, True)


class FakeRegistry:
    def __init__(self):
        self._registries: Dict[str, Dict[str, Any]] = {}

    def _k(self, path: Path) -> str:
        return str(path).replace("\\", "/")

    def read_registry(self, path: Path) -> Dict[str, Any]:
        return self._registries.get(self._k(path), {"files": []})

    def write_registry(self, path: Path, data: Dict[str, Any]) -> None:
        self._registries[self._k(path)] = json.loads(json.dumps(data))

    def apply_patch_append_file_record(self, registry_path: Path, record: Dict[str, Any]) -> None:
        reg = self.read_registry(registry_path)
        reg.setdefault("files", [])
        reg["files"].append(record)
        self.write_registry(registry_path, reg)


class FakeEvidence:
    def __init__(self):
        self._events: List[Any] = []

    def emit(self, event: Any) -> None:
        self._events.append(event)

    def all_events(self) -> List[Any]:
        return list(self._events)

    def flush_jsonl(self, path: Path) -> None:
        # tests typically inspect in-memory events
        return


def make_fake_ops() -> Ops:
    return Ops(fs=FakeFS(), proc=FakeProc(), registry=FakeRegistry(), evidence=FakeEvidence())
```

---

## src/automation/workspace.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Workspace:
    root: Path

    @property
    def inputs_dir(self) -> Path:
        return self.root / "inputs"

    @property
    def outputs_dir(self) -> Path:
        return self.root / "outputs"

    @property
    def evidence_dir(self) -> Path:
        return self.root / "evidence"

    def ensure(self, fs) -> None:
        fs.mkdir(self.root, parents=True)
        fs.mkdir(self.inputs_dir, parents=True)
        fs.mkdir(self.outputs_dir, parents=True)
        fs.mkdir(self.evidence_dir, parents=True)
```

---

## src/automation/triggers/file_identity_create.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from ..core import (
    ExecutionPlan, Step, ExecutionContext, ExecutionResult,
    Gate, GateResult, emit
)


# -----------------------
# Gates
# -----------------------

class GateNoDuplicateDocIds:
    gate_id = "GATE-NO-DUPLICATES"

    def check(self, ctx: ExecutionContext) -> GateResult:
        import time
        start = time.time()
        registry_path = Path(ctx.config["registry_path"])
        reg = ctx.ops.registry.read_registry(registry_path)
        ids: List[str] = [r.get("doc_id") for r in reg.get("files", []) if r.get("doc_id")]
        dups = sorted({x for x in ids if ids.count(x) > 1})
        passed = len(dups) == 0
        dur = int((time.time() - start) * 1000)
        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            reason=None if passed else f"Duplicate doc_id(s): {dups}",
            evidence={"duplicates": dups},
            duration_ms=dur,
        )


class GateRegistryReadable:
    gate_id = "GATE-REGISTRY-READABLE"

    def check(self, ctx: ExecutionContext) -> GateResult:
        import time
        start = time.time()
        registry_path = Path(ctx.config["registry_path"])
        try:
            _ = ctx.ops.registry.read_registry(registry_path)
            passed = True
            reason = None
        except Exception as e:
            passed = False
            reason = str(e)
        dur = int((time.time() - start) * 1000)
        return GateResult(self.gate_id, passed, reason=reason, evidence={}, duration_ms=dur)


# -----------------------
# Trigger handler
# -----------------------

TRIGGER_ID = "FILE_IDENTITY_CREATE"


@dataclass(frozen=True)
class FileIdentityInputs:
    target_relpath: str  # relative to workspace/inputs
    embed_mode: str = "filename_prefix"  # filename_prefix | header_comment
    seed: int = 42


def _allocate_doc_id_deterministic(seed: int, relpath: str) -> str:
    # Deterministic 16-digit numeric ID derived from seed+relpath (not cryptographic; test-friendly)
    import hashlib
    h = hashlib.sha256(f"{seed}:{relpath}".encode("utf-8")).hexdigest()
    # take 16 digits from hex by converting
    n = int(h[:16], 16)
    return f"{n % (10**16):016d}"


def plan(inputs: FileIdentityInputs, config: Dict[str, Any]) -> ExecutionPlan:
    plan_id = f"plan-{TRIGGER_ID}-{uuid.uuid4().hex[:8]}"
    steps = [
        Step(
            step_id="STEP-DETECT",
            action="capture_event",
            inputs={"target_relpath": inputs.target_relpath},
            expected_outputs=["evidence/events.jsonl"],
        ),
        Step(
            step_id="STEP-ALLOCATE_ID",
            action="allocate_doc_id",
            inputs={"seed": inputs.seed, "target_relpath": inputs.target_relpath},
            expected_outputs=[],
        ),
        Step(
            step_id="STEP-EMBED_ID",
            action="embed_doc_id",
            inputs={"embed_mode": inputs.embed_mode},
            expected_outputs=["outputs/renamed_path.txt"],
            rollback_action="ROLLBACK-RENAME",
        ),
        Step(
            step_id="STEP-REGISTRY_UPDATE",
            action="registry_append",
            inputs={"registry_path": config["registry_path"]},
            expected_outputs=["outputs/registry_patch.json"],
            rollback_action="ROLLBACK-REGISTRY",
        ),
        Step(
            step_id="STEP-GATES",
            action="run_gates",
            gate_ids=["GATE-REGISTRY-READABLE", "GATE-NO-DUPLICATES"],
            expected_outputs=["outputs/gate_results.json"],
        ),
        Step(
            step_id="STEP-EVIDENCE",
            action="write_evidence",
            expected_outputs=["outputs/run_summary.json", "outputs/artifacts_manifest.json"],
        ),
    ]
    p = ExecutionPlan(
        plan_id=plan_id,
        trigger_id=TRIGGER_ID,
        steps=steps,
        required_tools=[],
        meta={"registry_path": config["registry_path"]},
    )
    return p


def execute(plan: ExecutionPlan, ctx: ExecutionContext) -> ExecutionResult:
    ctx.workspace.ensure(ctx.ops.fs)
    artifacts: Dict[str, str] = {}
    gate_results: List[GateResult] = []

    # Mutable state for rollback
    state: Dict[str, Any] = {"original_path": None, "new_path": None, "registry_record": None}

    def rollback_all():
        # best-effort rollback; emit events
        try:
            if state.get("new_path") and state.get("original_path"):
                newp = Path(state["new_path"])
                origp = Path(state["original_path"])
                if ctx.ops.fs.exists(newp):
                    ctx.ops.fs.move(newp, origp)
                emit(ctx, "rollback_applied", "ROLLBACK-RENAME", {"from": str(newp), "to": str(origp)})
        except Exception as e:
            emit(ctx, "rollback_failed", "ROLLBACK-RENAME", {"error": str(e)})

        try:
            rec = state.get("registry_record")
            if rec:
                # remove last matching record (simple rollback policy)
                reg_path = Path(ctx.config["registry_path"])
                reg = ctx.ops.registry.read_registry(reg_path)
                files = reg.get("files", [])
                for i in range(len(files) - 1, -1, -1):
                    if files[i].get("doc_id") == rec.get("doc_id") and files[i].get("path") == rec.get("path"):
                        files.pop(i)
                        break
                reg["files"] = files
                ctx.ops.registry.write_registry(reg_path, reg)
                emit(ctx, "rollback_applied", "ROLLBACK-REGISTRY", {"doc_id": rec.get("doc_id")})
        except Exception as e:
            emit(ctx, "rollback_failed", "ROLLBACK-REGISTRY", {"error": str(e)})

    try:
        for step in plan.steps:
            if step.action == "capture_event":
                emit(ctx, "step_started", step.step_id, step.inputs)
                emit(ctx, "step_completed", step.step_id, {"ok": True})

            elif step.action == "allocate_doc_id":
                emit(ctx, "step_started", step.step_id, step.inputs)
                doc_id = _allocate_doc_id_deterministic(step.inputs["seed"], step.inputs["target_relpath"])
                ctx.config["doc_id"] = doc_id
                emit(ctx, "step_completed", step.step_id, {"doc_id": doc_id})

            elif step.action == "embed_doc_id":
                emit(ctx, "step_started", step.step_id, step.inputs)
                target = ctx.workspace.inputs_dir / ctx.config["target_relpath"]
                if not ctx.ops.fs.exists(target):
                    raise FileNotFoundError(f"target file missing: {target}")

                state["original_path"] = str(target)

                doc_id = ctx.config["doc_id"]
                if step.inputs["embed_mode"] == "filename_prefix":
                    new_name = f"{doc_id}__{target.name}"
                    new_path = target.with_name(new_name)
                    ctx.ops.fs.move(target, new_path)
                    state["new_path"] = str(new_path)
                    ctx.ops.fs.write_text(ctx.workspace.outputs_dir / "renamed_path.txt", str(new_path))
                    artifacts["renamed_path"] = str(ctx.workspace.outputs_dir / "renamed_path.txt")
                    emit(ctx, "step_completed", step.step_id, {"new_path": str(new_path)})
                else:
                    # header_comment mode (for text files)
                    content = ctx.ops.fs.read_text(target)
                    ctx.ops.fs.write_text(target, f"# doc_id: {doc_id}\n{content}")
                    emit(ctx, "step_completed", step.step_id, {"embedded": "header_comment"})

            elif step.action == "registry_append":
                emit(ctx, "step_started", step.step_id, step.inputs)
                reg_path = Path(step.inputs["registry_path"])
                reg = ctx.ops.registry.read_registry(reg_path)

                doc_id = ctx.config["doc_id"]
                final_path = state.get("new_path") or state.get("original_path")
                record = {"doc_id": doc_id, "path": final_path}
                state["registry_record"] = dict(record)

                ctx.ops.registry.apply_patch_append_file_record(reg_path, record)

                # write a "patch" artifact (simple append record)
                patch_path = ctx.workspace.outputs_dir / "registry_patch.json"
                ctx.ops.fs.write_text(patch_path, __import__("json").dumps({"append": record}, indent=2))
                artifacts["registry_patch"] = str(patch_path)
                emit(ctx, "step_completed", step.step_id, {"registry_path": str(reg_path), "doc_id": doc_id})

            elif step.action == "run_gates":
                emit(ctx, "step_started", step.step_id, {"gates": step.gate_ids})
                results: List[GateResult] = []
                for gid in step.gate_ids:
                    gate = ctx.gates[gid]
                    r = gate.check(ctx)
                    results.append(r)
                    gate_results.append(r)
                    emit(ctx, "gate_checked", step.step_id, {"gate_id": gid, "passed": r.passed, "reason": r.reason}, duration_ms=r.duration_ms)
                    if not r.passed:
                        raise RuntimeError(f"Gate failed: {gid}: {r.reason}")

                # persist gate results
                out = [{"gate_id": r.gate_id, "passed": r.passed, "reason": r.reason, "evidence": r.evidence, "duration_ms": r.duration_ms} for r in results]
                gate_path = ctx.workspace.outputs_dir / "gate_results.json"
                ctx.ops.fs.write_text(gate_path, __import__("json").dumps(out, indent=2))
                artifacts["gate_results"] = str(gate_path)
                emit(ctx, "step_completed", step.step_id, {"all_passed": True})

            elif step.action == "write_evidence":
                emit(ctx, "step_started", step.step_id, {})
                # artifacts manifest
                manifest_path = ctx.workspace.outputs_dir / "artifacts_manifest.json"
                ctx.ops.fs.write_text(manifest_path, __import__("json").dumps(artifacts, indent=2, sort_keys=True))
                artifacts["artifacts_manifest"] = str(manifest_path)

                # run summary
                summary_path = ctx.workspace.outputs_dir / "run_summary.json"
                summary = {
                    "trigger_id": ctx.trigger_id,
                    "run_id": ctx.run_id,
                    "success": True,
                    "artifacts": artifacts,
                    "gate_results": [{"gate_id": r.gate_id, "passed": r.passed} for r in gate_results],
                }
                ctx.ops.fs.write_text(summary_path, __import__("json").dumps(summary, indent=2, sort_keys=True))
                artifacts["run_summary"] = str(summary_path)

                emit(ctx, "step_completed", step.step_id, {"written": True})

            else:
                raise RuntimeError(f"Unknown step action: {step.action}")

        return ExecutionResult(trigger_id=ctx.trigger_id, run_id=ctx.run_id, success=True, artifacts=artifacts, gate_results=gate_results)

    except Exception as e:
        emit(ctx, "execution_failed", "EXECUTOR", {"error": str(e)})
        rollback_all()
        return ExecutionResult(trigger_id=ctx.trigger_id, run_id=ctx.run_id, success=False, artifacts=artifacts, gate_results=gate_results, error=str(e))
```

---

## tests/test_layer2_plan.py

```python
from src.automation.triggers.file_identity_create import plan, FileIdentityInputs, TRIGGER_ID

def test_layer2_plan_is_deterministic_hash_for_same_inputs():
    config = {"registry_path": "registry.json"}
    inputs = FileIdentityInputs(target_relpath="foo.txt", embed_mode="filename_prefix", seed=123)

    p1 = plan(inputs, config)
    p2 = plan(inputs, config)

    # plan_id differs due to uuid; determinism should be assessed by a stable hash of stable_dict
    # Here we compare hashes after normalizing plan_id.
    p1.plan_id = "PLAN"
    p2.plan_id = "PLAN"

    assert p1.trigger_id == TRIGGER_ID
    assert p2.trigger_id == TRIGGER_ID

    assert p1.validate() == []
    assert p2.validate() == []
    assert p1.hash() == p2.hash()
```

---

## tests/test_layer3_sandbox.py

```python
from pathlib import Path
import json

from src.automation.ops import make_real_ops
from src.automation.workspace import Workspace
from src.automation.core import ExecutionContext
from src.automation.triggers.file_identity_create import (
    plan, execute, FileIdentityInputs,
    GateNoDuplicateDocIds, GateRegistryReadable, TRIGGER_ID
)

def test_layer3_sandbox_e2e(tmp_path: Path):
    ops = make_real_ops()
    ws = Workspace(tmp_path / "ws")
    ws.ensure(ops.fs)

    # Seed input file
    target_rel = "hello.txt"
    ops.fs.write_text(ws.inputs_dir / target_rel, "hello")

    # Seed empty registry
    registry_path = tmp_path / "registry.json"
    ops.registry.write_registry(registry_path, {"files": []})

    config = {"registry_path": str(registry_path), "target_relpath": target_rel}
    inputs = FileIdentityInputs(target_relpath=target_rel, embed_mode="filename_prefix", seed=1)

    pl = plan(inputs, config)
    pl.plan_id = "PLAN"  # stable for test

    ctx = ExecutionContext(
        trigger_id=TRIGGER_ID,
        run_id="RUN-1",
        workspace=ws,
        ops=ops,
        config=config,
        gates={
            "GATE-REGISTRY-READABLE": GateRegistryReadable(),
            "GATE-NO-DUPLICATES": GateNoDuplicateDocIds(),
        },
    )

    result = execute(pl, ctx)
    assert result.success is True, result.error
    assert "run_summary" in result.artifacts
    assert Path(result.artifacts["artifacts_manifest"]).exists()

    summary = json.loads(Path(result.artifacts["run_summary"]).read_text(encoding="utf-8"))
    assert summary["success"] is True
```

---

## tests/test_layer5_negative_rollback.py

```python
from pathlib import Path
import json

from src.automation.ops import make_real_ops
from src.automation.workspace import Workspace
from src.automation.core import ExecutionContext
from src.automation.triggers.file_identity_create import (
    plan, execute, FileIdentityInputs,
    GateNoDuplicateDocIds, GateRegistryReadable, TRIGGER_ID,
    _allocate_doc_id_deterministic
)

def test_layer5_negative_gate_fail_triggers_rollback(tmp_path: Path):
    ops = make_real_ops()
    ws = Workspace(tmp_path / "ws")
    ws.ensure(ops.fs)

    target_rel = "x.txt"
    original_path = ws.inputs_dir / target_rel
    ops.fs.write_text(original_path, "data")

    registry_path = tmp_path / "registry.json"

    # Pre-seed registry with a duplicate doc_id that will be generated for this file
    seed = 7
    dup_doc_id = _allocate_doc_id_deterministic(seed, target_rel)
    ops.registry.write_registry(registry_path, {"files": [{"doc_id": dup_doc_id, "path": "SOMEWHERE"}]})

    config = {"registry_path": str(registry_path), "target_relpath": target_rel}
    inputs = FileIdentityInputs(target_relpath=target_rel, embed_mode="filename_prefix", seed=seed)

    pl = plan(inputs, config)
    pl.plan_id = "PLAN"

    ctx = ExecutionContext(
        trigger_id=TRIGGER_ID,
        run_id="RUN-NEG-1",
        workspace=ws,
        ops=ops,
        config=config,
        gates={
            "GATE-REGISTRY-READABLE": GateRegistryReadable(),
            "GATE-NO-DUPLICATES": GateNoDuplicateDocIds(),
        },
    )

    result = execute(pl, ctx)
    assert result.success is False
    assert result.error is not None

    # Verify rollback: original path exists again (renamed file moved back)
    assert original_path.exists()

    # Verify evidence contains rollback_applied (best-effort check)
    evts = ops.evidence.all_events()
    evt_types = [e.event_type for e in evts]
    assert "execution_failed" in evt_types
    assert "rollback_applied" in evt_types
```

---

## How to run

```bash
pip install -U pytest
pytest -q
```

---

## How this makes automation easier to test

If you adopt only these rules across automations, tests become straightforward and objective:

1. **Every trigger implements `plan()` + `execute()`**
2. **Every side effect goes through `ops`**
3. **Every step emits structured events**
4. **Every run is confined to a `Workspace`**

That guarantees you can always write:

* deterministic plan tests (Layer 2)
* sandbox e2e tests (Layer 3)
* negative-path/rollback tests (Layer 5)

