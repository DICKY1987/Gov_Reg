# DOC_LINK: DOC-CORE-ENGINE-ROUTER-157
"""Task Router - WS-03-01B

Routes tasks to appropriate tools based on router_config.json.
Supports multiple routing strategies and capability matching.
"""

# DOC_ID: DOC-CORE-ENGINE-ROUTER-157

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from core.events.event_bus import EventBus, EventType
from patterns.decisions.decision_registry import Decision, DecisionRegistry

logger = logging.getLogger(__name__)


class RoutingStateStore(Protocol):
    """Protocol for routing state persistence"""

    def get_round_robin_index(self, rule_id: str) -> int: ...
    def set_round_robin_index(self, rule_id: str, index: int) -> None: ...
    def get_tool_metrics(self, tool_id: str) -> Dict[str, Any]: ...


class FileBackedStateStore:
    """File-based implementation of routing state store with persistence"""

    def __init__(self, state_file: str = ".state/router_state.json"):
        self.state_file = Path(state_file)
        self._load_state()

    def _load_state(self):
        """Load state from file if it exists"""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self._round_robin_indices = data.get("round_robin", {})
                self._tool_metrics = defaultdict(
                    lambda: {
                        "success_count": 0,
                        "failure_count": 0,
                        "total_latency_ms": 0.0,
                        "call_count": 0,
                    },
                    data.get("metrics", {}),
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load router state: {e}, starting fresh")
                self._init_empty_state()
        else:
            self._init_empty_state()

    def _init_empty_state(self):
        """Initialize empty state"""
        self._round_robin_indices: Dict[str, int] = {}
        self._tool_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "success_count": 0,
                "failure_count": 0,
                "total_latency_ms": 0.0,
                "call_count": 0,
            }
        )

    def _save_state(self):
        """Persist state to file"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "round_robin": self._round_robin_indices,
                "metrics": dict(self._tool_metrics),
            }
            self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to save router state: {e}")

    def get_round_robin_index(self, rule_id: str) -> int:
        return self._round_robin_indices.get(rule_id, 0)

    def set_round_robin_index(self, rule_id: str, index: int) -> None:
        self._round_robin_indices[rule_id] = index
        self._save_state()

    def get_tool_metrics(self, tool_id: str) -> Dict[str, Any]:
        return self._tool_metrics[tool_id]


class InMemoryStateStore:
    """In-memory implementation of routing state store"""

    def __init__(self):
        self._round_robin_indices: Dict[str, int] = defaultdict(int)
        self._tool_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "success_count": 0,
                "failure_count": 0,
                "total_latency_ms": 0.0,
                "call_count": 0,
            }
        )

    def get_round_robin_index(self, rule_id: str) -> int:
        return self._round_robin_indices[rule_id]

    def set_round_robin_index(self, rule_id: str, index: int) -> None:
        self._round_robin_indices[rule_id] = index

    def get_tool_metrics(self, tool_id: str) -> Dict[str, Any]:
        # Return reference to allow updates
        return self._tool_metrics[tool_id]


class RoutingDecision:
    """Records a routing decision for observability"""

    def __init__(
        self,
        task_kind: str,
        selected_tool: str,
        strategy: str,
        candidates: List[str],
        rule_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ):
        self.task_kind = task_kind
        self.selected_tool = selected_tool
        self.strategy = strategy
        self.candidates = candidates
        self.rule_id = rule_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.task_id = task_id
        self.run_id = run_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "task_kind": self.task_kind,
            "selected_tool": self.selected_tool,
            "strategy": self.strategy,
            "candidates": self.candidates,
            "rule_id": self.rule_id,
            "metadata": self.metadata,
            "task_id": self.task_id,
            "run_id": self.run_id,
        }


class TaskRouter:
    """Routes tasks to tools based on configuration and capabilities"""

    def __init__(
        self,
        router_config_path: str,
        state_store: Optional[RoutingStateStore] = None,
        event_bus: Optional[EventBus] = None,
        decision_registry: Optional[DecisionRegistry] = None,
    ):
        """
        Initialize router with configuration.

        Args:
            router_config_path: Path to router_config.json
            state_store: Optional state store for strategy persistence (defaults to in-memory)
            event_bus: Optional event bus for event emission
            decision_registry: Optional decision registry for logging routing decisions
        """
        self.config_path = Path(router_config_path)
        self.config = self._load_config()
        self.apps = self.config.get("apps", {})
        self.routing_rules = self.config.get("routing", {}).get("rules", [])
        self.defaults = self.config.get("defaults", {})
        self.state_store = state_store or InMemoryStateStore()
        self.decision_log: List[RoutingDecision] = []
        self.event_bus = event_bus
        self.decision_registry = decision_registry

    def _load_config(self) -> Dict[str, Any]:
        """Load and parse router configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Router config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Validate required fields
        if "apps" not in config:
            raise ValueError("Router config missing 'apps' field")
        if "routing" not in config:
            raise ValueError("Router config missing 'routing' field")

        return config

    def route_task(
        self,
        task_kind: str,
        risk_tier: Optional[str] = None,
        complexity: Optional[str] = None,
        domain: Optional[str] = None,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Route a task to the best tool.

        Args:
            task_kind: Kind of task (e.g., 'code_edit', 'analysis')
            risk_tier: Risk level ('low', 'medium', 'high')
            complexity: Complexity level ('low', 'medium', 'high')
            domain: Domain hint (e.g., 'software-dev')

        Returns:
            tool_id: ID of selected tool, or None if no match
        """
        # Try to match routing rules first
        for rule in self.routing_rules:
            if self._matches_rule(rule, task_kind, risk_tier, complexity):
                candidates = rule.get("select_from", [])
                strategy = rule.get("strategy", "fixed")
                rule_id = rule.get("id")

                if candidates:
                    selected = self._apply_strategy(candidates, strategy, rule_id)
                    if selected:
                        # Log decision
                        decision = RoutingDecision(
                            task_kind=task_kind,
                            selected_tool=selected,
                            strategy=strategy,
                            candidates=candidates,
                            rule_id=rule_id,
                            metadata={
                                "risk_tier": risk_tier,
                                "complexity": complexity,
                                "domain": domain,
                            },
                            task_id=task_id,
                            run_id=run_id,
                        )
                        self.decision_log.append(decision)
                        logger.info(
                            f"Routed {task_kind} to {selected} via rule {rule_id} (strategy: {strategy})"
                        )
                        self._emit_routing_event(
                            EventType.ROUTING_COMPLETE,
                            run_id,
                            task_id,
                            decision.to_dict(),
                        )

                        # Log to decision registry
                        if self.decision_registry:
                            reg_decision = Decision(
                                decision_id=f"ROUTE-{task_id or 'UNKNOWN'}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                                timestamp=datetime.now(timezone.utc).isoformat(),
                                category="routing",
                                context={
                                    "task_kind": task_kind,
                                    "risk_tier": risk_tier,
                                    "complexity": complexity,
                                    "domain": domain,
                                },
                                options=candidates,
                                selected_option=selected,
                                rationale=f"Strategy: {strategy}, Rule: {rule_id}",
                                metadata={
                                    "run_id": run_id,
                                    "task_id": task_id,
                                    "rule_id": rule_id,
                                },
                            )
                            self.decision_registry.log_decision(reg_decision)

                        return selected

        # Fallback: find any tool that can handle this task_kind
        capable_tools = self._find_capable_tools(task_kind, domain)

        if capable_tools:
            # Default to first capable tool
            selected = capable_tools[0]
            if hasattr(self, "event_bus") and self.event_bus:
                try:
                    self.event_bus.emit(
                        "ROUTING_FALLBACK",
                        run_id=run_id,
                        task_id=task_id,
                        payload={
                            "task_kind": task_kind,
                            "candidates": capable_tools,
                            "reason": "no_matching_rule",
                        },
                    )
                except Exception:
                    pass
            decision = RoutingDecision(
                task_kind=task_kind,
                selected_tool=selected,
                strategy="fallback",
                candidates=capable_tools,
                metadata={"reason": "no_matching_rule"},
                task_id=task_id,
                run_id=run_id,
            )
            self.decision_log.append(decision)
            logger.info(f"Routed {task_kind} to {selected} via fallback")
            self._emit_routing_event(
                "ROUTING_FALLBACK", run_id, task_id, decision.to_dict()
            )
            return selected

        logger.warning(f"No capable tools found for {task_kind}")
        return None

    def _emit_routing_event(
        self,
        event_type: Any,
        run_id: Optional[str],
        task_id: Optional[str],
        payload: Dict[str, Any],
    ) -> None:
        """Publish routing decisions if an event bus is attached."""
        if not self.event_bus:
            return
        try:
            self.event_bus.emit(
                event_type,
                run_id=run_id,
                task_id=task_id,
                payload=payload,
            )
        except Exception:
            return

    def _matches_rule(
        self,
        rule: Dict[str, Any],
        task_kind: str,
        risk_tier: Optional[str],
        complexity: Optional[str],
    ) -> bool:
        """Check if task matches routing rule"""
        match = rule.get("match", {})

        # Check task_kind
        if "task_kind" in match:
            if task_kind not in match["task_kind"]:
                return False

        # Check risk_tier
        if risk_tier and "risk_tier" in match:
            if risk_tier not in match["risk_tier"]:
                return False

        # Check complexity
        if complexity and "complexity" in match:
            if complexity != match["complexity"]:
                return False

        return True

    def _find_capable_tools(
        self, task_kind: str, domain: Optional[str] = None
    ) -> List[str]:
        """Find all tools capable of handling task_kind"""
        capable = []

        for tool_id, app_config in self.apps.items():
            capabilities = app_config.get("capabilities", {})

            # Check if tool supports this task_kind
            supported_tasks = capabilities.get("task_kinds", [])
            if task_kind in supported_tasks:
                # If domain specified, check domain match
                if domain:
                    supported_domains = capabilities.get("domains", [])
                    if domain in supported_domains or not supported_domains:
                        capable.append(tool_id)
                else:
                    capable.append(tool_id)

        return sorted(capable)

    def _apply_strategy(
        self, candidates: List[str], strategy: str, rule_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Apply routing strategy to select from candidates.

        Args:
            candidates: List of candidate tool IDs
            strategy: Routing strategy ('fixed', 'round_robin', 'metrics', 'auto')
            rule_id: Optional rule ID for state tracking

        Returns:
            Selected tool ID
        """
        if not candidates:
            return None

        if strategy == "fixed":
            # Always return first candidate
            return candidates[0]

        elif strategy == "round_robin":
            # Round-robin with persistent state
            if rule_id:
                index = self.state_store.get_round_robin_index(rule_id)
                selected = candidates[index % len(candidates)]
                # Update index for next call
                self.state_store.set_round_robin_index(rule_id, index + 1)
                logger.debug(f"Round-robin selected {selected} (index {index})")
                return selected
            else:
                # No rule_id, fall back to first
                logger.warning(
                    "Round-robin strategy without rule_id, using first candidate"
                )
                return candidates[0]

        elif strategy == "metrics" or strategy == "auto":
            # Metrics-based selection
            return self._select_by_metrics(candidates)

        else:
            # Unknown strategy, default to first
            logger.warning(f"Unknown strategy '{strategy}', using first candidate")
            return candidates[0]

    def _select_by_metrics(self, candidates: List[str]) -> str:
        """
        Select tool based on historical metrics.

        Prioritizes:
        1. Success rate (success_count / total calls)
        2. Average latency (lower is better)

        Args:
            candidates: List of candidate tool IDs

        Returns:
            Selected tool ID
        """
        best_tool = None
        best_score = -1.0

        for tool_id in candidates:
            metrics = self.state_store.get_tool_metrics(tool_id)
            call_count = metrics.get("call_count", 0)

            if call_count == 0:
                # No history, give it a neutral score
                score = 0.5
            else:
                success_count = metrics.get("success_count", 0)
                total_latency = metrics.get("total_latency_ms", 0.0)

                # Success rate (0-1)
                success_rate = success_count / call_count

                # Normalized latency (invert so lower latency = higher score)
                avg_latency = total_latency / call_count if call_count > 0 else 1000.0
                latency_score = 1.0 / (
                    1.0 + (avg_latency / 1000.0)
                )  # Normalize around 1000ms

                # Combined score (weighted: 70% success rate, 30% latency)
                score = (0.7 * success_rate) + (0.3 * latency_score)

            logger.debug(f"Tool {tool_id} score: {score:.3f}")

            if score > best_score:
                best_score = score
                best_tool = tool_id

        logger.info(f"Metrics-based selection: {best_tool} (score: {best_score:.3f})")
        return best_tool or candidates[0]

    def get_tool_config(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tool"""
        return self.apps.get(tool_id)

    def get_tool_command(self, tool_id: str) -> Optional[str]:
        """Get command for a tool"""
        tool_config = self.get_tool_config(tool_id)
        if tool_config:
            return tool_config.get("command")
        return None

    def get_tool_limits(self, tool_id: str) -> Dict[str, Any]:
        """Get limits for a tool (timeout, max_parallel, etc.)"""
        tool_config = self.get_tool_config(tool_id)
        if tool_config:
            limits = tool_config.get("limits", {})
            # Merge with defaults
            return {
                "max_parallel": limits.get("max_parallel", 1),
                "timeout_seconds": limits.get(
                    "timeout_seconds", self.defaults.get("timeout_seconds", 600)
                ),
            }
        return {
            "max_parallel": 1,
            "timeout_seconds": self.defaults.get("timeout_seconds", 600),
        }

    def list_tools(self) -> List[str]:
        """List all available tool IDs"""
        return list(self.apps.keys())

    def get_capabilities(self, tool_id: str) -> Dict[str, Any]:
        """Get capabilities for a tool"""
        tool_config = self.get_tool_config(tool_id)
        if tool_config:
            return tool_config.get("capabilities", {})
        return {}

    def get_decision_log(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get routing decision log.

        Args:
            last_n: Optional limit to last N decisions

        Returns:
            List of decision records
        """
        decisions = self.decision_log
        if last_n:
            decisions = decisions[-last_n:]
        return [d.to_dict() for d in decisions]

    def clear_decision_log(self) -> None:
        """Clear the decision log"""
        self.decision_log.clear()
        logger.debug("Decision log cleared")

    def record_execution_result(
        self, tool_id: str, success: bool, latency_ms: float
    ) -> None:
        """
        Record execution result for metrics-based routing.

        Args:
            tool_id: Tool that executed the task
            success: Whether execution succeeded
            latency_ms: Execution latency in milliseconds
        """
        metrics = self.state_store.get_tool_metrics(tool_id)
        metrics["call_count"] = metrics.get("call_count", 0) + 1
        metrics["total_latency_ms"] = metrics.get("total_latency_ms", 0.0) + latency_ms

        if success:
            metrics["success_count"] = metrics.get("success_count", 0) + 1
        else:
            metrics["failure_count"] = metrics.get("failure_count", 0) + 1

        # Update store (for in-memory this is a no-op, but important for persistent stores)
        logger.debug(
            f"Recorded {tool_id} result: success={success}, latency={latency_ms}ms"
        )


def create_router(
    router_config_path: str,
    state_store: Optional[RoutingStateStore] = None,
    event_bus: Optional[EventBus] = None,
) -> TaskRouter:
    """
    Factory function to create a router.

    Args:
        router_config_path: Path to router configuration file
        state_store: Optional state store for routing persistence
        event_bus: Optional event bus for telemetry

    Returns:
        Configured TaskRouter instance
    """
    return TaskRouter(router_config_path, state_store=state_store, event_bus=event_bus)
