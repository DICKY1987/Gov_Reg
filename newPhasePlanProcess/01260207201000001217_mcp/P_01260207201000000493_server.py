"""Local Planning MCP server (stdio, JSON-RPC)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from .tools import (
    plan_validate_structure,
    plan_validate_step_contracts,
    plan_validate_ssot,
    planning_extract_file_mutation_set,
    registry_snapshot_query,
)
from .utils import config as config_loader
from .utils.schema import validate_input
from .utils.tool_result import build_envelope


CONTRACT_PATH = Path(__file__).resolve().parent / "contracts" / "tool_contracts.v1.json"


def load_contracts() -> Dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def tools_by_name(contracts: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {tool["tool"]: tool for tool in contracts.get("tools", [])}


TOOL_HANDLERS = {
    "plan.validate_structure": plan_validate_structure.handle,
    "plan.validate_step_contracts": plan_validate_step_contracts.handle,
    "plan.validate_ssot": plan_validate_ssot.handle,
    "registry.snapshot_query": registry_snapshot_query.handle,
    "planning.extract_file_mutation_set": planning_extract_file_mutation_set.handle,
}


def main() -> None:
    contracts = load_contracts()
    config = config_loader.load_config()
    tool_map = tools_by_name(contracts)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handle_request(line, tool_map, config, contracts)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def handle_request(
    raw: str,
    tool_map: Dict[str, Dict[str, Any]],
    config: Dict[str, Any],
    contracts: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        request = json.loads(raw)
    except json.JSONDecodeError:
        return _jsonrpc_error(None, -32700, "parse error")

    if not isinstance(request, dict) or "method" not in request:
        return _jsonrpc_error(request.get("id") if isinstance(request, dict) else None, -32600, "invalid request")

    method = request.get("method")
    req_id = request.get("id")

    if method == "tools/list":
        tools = []
        for name, spec in tool_map.items():
            tools.append(
                {
                    "name": name,
                    "description": spec.get("description", ""),
                    "input_schema": spec.get("input_schema", {}),
                }
            )
        return _jsonrpc_result(req_id, {"tools": tools})

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name not in tool_map:
            return _jsonrpc_result(req_id, _unknown_tool_envelope(tool_name))

        tool_spec = tool_map[tool_name]
        args = _apply_defaults(args, tool_spec.get("input_schema", {}))
        input_schema = dict(tool_spec.get("input_schema", {}))
        if "shared" in contracts:
            input_schema["shared"] = contracts["shared"]
        errors = validate_input(args, input_schema)
        if errors:
            return _jsonrpc_result(req_id, _invalid_input_envelope(tool_spec, args, errors))

        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return _jsonrpc_result(req_id, _missing_handler_envelope(tool_spec, args))

        result = handler(args, tool_spec, config)
        return _jsonrpc_result(req_id, result)

    return _jsonrpc_error(req_id, -32601, "method not found")


def _apply_defaults(instance: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(instance, dict):
        return instance
    props = schema.get("properties", {})
    output = dict(instance)
    for key, prop in props.items():
        if key not in output and "default" in prop:
            output[key] = prop["default"]
    return output


def _jsonrpc_result(req_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _jsonrpc_error(req_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _unknown_tool_envelope(tool_name: str) -> Dict[str, Any]:
    return build_envelope(
        tool=tool_name or "unknown",
        tool_version="0.0.0",
        status="error",
        exit_code=1,
        run_id="RUN-UNKNOWN",
        evidence_path=Path(".state/evidence/mcp/unknown_tool.json"),
        summary=f"unknown tool: {tool_name}",
        defects=[
            {
                "severity": "high",
                "code": "INTERNAL_ERROR",
                "location": "mcp.server",
                "message": f"unknown tool: {tool_name}",
            }
        ],
        artifacts_emitted=[],
        hashes={},
        write_evidence_flag=False,
        input_payload={},
    )


def _missing_handler_envelope(tool_spec: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    run_id = args.get("context", {}).get("run_id", "RUN-UNKNOWN")
    evidence_path = Path(tool_spec.get("default_evidence_path_template", "").replace("{run_id}", run_id) or ".state/evidence/mcp/missing_handler.json")
    return build_envelope(
        tool=tool_spec["tool"],
        tool_version=tool_spec["tool_version"],
        status="error",
        exit_code=1,
        run_id=run_id,
        evidence_path=evidence_path,
        summary="tool handler missing",
        defects=[
            {
                "severity": "high",
                "code": "EXEC_BINDING_MISSING",
                "location": "mcp.server",
                "message": "tool handler missing",
            }
        ],
        artifacts_emitted=[],
        hashes={},
        write_evidence_flag=True,
        input_payload=args,
    )


def _invalid_input_envelope(tool_spec: Dict[str, Any], args: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    run_id = args.get("context", {}).get("run_id", "RUN-UNKNOWN")
    evidence_path = Path(tool_spec.get("default_evidence_path_template", "").replace("{run_id}", run_id) or ".state/evidence/mcp/invalid_input.json")
    defects = [
        {
            "severity": "high",
            "code": "INVALID_INPUT_SCHEMA",
            "location": "mcp.server",
            "message": err,
        }
        for err in errors
    ]
    return build_envelope(
        tool=tool_spec["tool"],
        tool_version=tool_spec["tool_version"],
        status="error",
        exit_code=1,
        run_id=run_id,
        evidence_path=evidence_path,
        summary="input schema validation failed",
        defects=defects,
        artifacts_emitted=[],
        hashes={},
        write_evidence_flag=True,
        input_payload=args,
    )


if __name__ == "__main__":
    main()
