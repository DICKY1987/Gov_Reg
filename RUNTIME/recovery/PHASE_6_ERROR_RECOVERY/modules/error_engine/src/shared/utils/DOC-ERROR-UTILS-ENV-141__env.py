# DOC_LINK: DOC-ERROR-UTILS-ENV-141
from __future__ import annotations

import os
from typing import Dict


SCRUB_SUFFIXES = ("_PROXY",)


def scrub_env(base: Dict[str, str] | None = None) -> Dict[str, str]:
    env = dict(base or os.environ)
    # Set stable locale
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    # Remove path-affecting and network-proxy variables
    env.pop("PYTHONPATH", None)
    for key in list(env.keys()):
        if any(key.upper().endswith(s) for s in SCRUB_SUFFIXES):
            env.pop(key, None)
    return env

