teal_version: "1.0"
timestamp: "2026-02-25T17:19:33Z"

modules:
  skeptic:
    version: "1.0.0"
    interface: "QUALITY_GATES.md"
    sidecar: true

  spec:
    version: "1.0.0"
    inputs: ["TASK.md", "QUALITY_GATES.md"]
    outputs: ["SPEC_CONTRACT.json"]

  build:
    version: "1.0.0"
    depends_on: ["spec"]
    outputs: ["nmf_marimo.py"]

  qa:
    version: "1.0.0"
    depends_on: ["build"]
    gates: ["gate.type-safety", "gate.shared-selection", "gate.marimo-check"]

pipelines:
  standard:
    - spec
    - build
    - qa
