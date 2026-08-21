# Private evaluation package

This directory is evaluator-only. It must never be mounted in an Agent-visible workspace.

- `oracle.patch`: minimal reference repair.
- `manifest.json`: frozen engine, scenario and integrity metadata.
- `suite.gd`: private runtime probe that inspects live scene state and captures rendered artifacts.
- `evaluate.py`: independent scorer for Functional 45 / Visual 35 / Regression 20.
