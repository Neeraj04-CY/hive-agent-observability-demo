# HiveDevAgent

## 1. Project Overview

HiveDevAgent is a developer tool for analyzing and visualizing Hive-based agent workflows.
It helps you model agent nodes, validate dependencies, simulate runtime behavior, export traces,
and generate workflow visuals that are useful for debugging and optimization.

## 2. Example Agent

This repository includes an example agent named `GitHubIssueInvestigator` in
`examples/github_issue_investigator.py`.

The example workflow simulates how an agent handles a GitHub issue:

1. Issue input capture
2. LLM issue understanding
3. Decision-based issue classification
4. Repository scanning tool step
5. LLM fix suggestion
6. Result aggregation

You can run it through an interactive CLI in `examples/run_issue_agent.py`.

## 3. Features

- Agent workflow generation
- Graph visualization
- Execution simulation
- Runtime trace export
- Failure detection
- Optimization suggestions

## 4. Running the Example Agent

```bash
pip install -r requirements.txt
python examples/run_issue_agent.py
```

The CLI prompts for:

- `issue_title`
- `issue_description`
- `repository_name`

Then it prints the issue classification, suggested fix, trace path, and graph image path.

## 5. Output Artifacts

- `execution_trace.json`: Structured runtime trace from the simulation, including execution id,
	node timings, node statuses, and attempt counts.
- `github_issue_investigator_graph.png`: Rendered workflow graph showing node flow and dependencies
	for the example issue-investigation agent.

## 6. Example Execution Trace

```json
{
	"execution_id": "53d3cec4-de3a-43fd-aca1-31f8c1d534ea",
	"timestamp": "2026-03-16T12:38:19.603703Z",
	"total_execution_time": 2274,
	"nodes": [
		{
			"node_id": "issue_understanding",
			"node_type": "llm",
			"status": "success",
			"start_time": "2026-03-16T12:38:19.704703Z",
			"end_time": "2026-03-16T12:38:20.235703Z",
			"duration_ms": 531,
			"attempts": 1
		}
	]
}
```

## 7. Demo

This project includes a working example agent: `GitHubIssueInvestigator`.

The agent analyzes a GitHub issue, classifies it, scans the repository, and proposes a potential fix.

Running the demo:

```bash
python examples/run_issue_agent.py
```

Artifacts generated:

- `execution_trace.json` - runtime execution trace (`demo_artifacts/execution_trace.json`)
- `github_issue_investigator_graph.png` - workflow graph visualization (`demo_artifacts/github_issue_investigator_graph.png`)

A short demo video showing the full run is included in `/demo`.