# DOC_LINK: DOC-CORE-TESTS-VALIDATE-POOL-625
"""Quick validation test for ToolProcessPool.

Simple smoke test to verify core functionality.
"""
DOC_ID: DOC-CORE-TESTS-VALIDATE-POOL-625

DOC_ID: DOC - CORE - TESTS - VALIDATE - POOL - 625

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.bridge import ToolProcessPool


def test_pool_basic():
    """Basic validation test."""
    from pathlib import Path

    # Create mock registry with absolute path
    project_root = Path(__file__).parent.parent.parent
    mock_path = str(project_root / "tests" / "aim" / "fixtures" / "mock_aider.py")

    mock_registry = {
        "tools": {
            "mock_aider": {
                "detectCommands": [["python", mock_path]],
                "capabilities": ["code_generation"],
            }
        }
    }

    # Test 1: Create pool
    pool = ToolProcessPool("mock_aider", count=1, registry=mock_registry)
    assert len(pool.instances) == 1
    print("✓ Pool created")

    # Test 2: Check status
    statuses = pool.get_status()
    assert statuses[0]["alive"] == True
    print("✓ Instance alive")

    # Test 3: Send prompt
    success = pool.send_prompt(0, "/help")
    assert success == True
    print("✓ Prompt sent")

    # Test 4: Read response
    banner = pool.read_response(0, timeout=2.0)
    assert banner is not None
    print(f"✓ Response received: {banner[:30]}...")

    # Test 5: Health check
    health = pool.check_health()
    assert health["alive"] >= 1
    print(f"✓ Health check: {health}")

    # Test 6: Shutdown
    pool.shutdown()
    final_statuses = pool.get_status()
    assert all(s["return_code"] is not None for s in final_statuses)
    print("✓ Shutdown successful")

    print("\n✅ All tests passed!")
    return True


if __name__ == "__main__":
    test_pool_basic()
