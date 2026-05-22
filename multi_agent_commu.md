# Multi-Agent Communication Implementation Spec

## 1. Core Design Principle

In this implementation, each agent should be implemented as a separate class with a common interface:

```python
def handle(message, state) -> message:
    ...
```

Each agent receives a structured `message` and the shared workflow `state`, then returns a new structured `message`.

Agents should **not** directly call each other.

Instead, the communication flow should be:

```text
Agent A
  -> returns Message
  -> Supervisor reads message.receiver
  -> Supervisor finds Agent B
  -> Supervisor calls AgentB.handle(message, state)
```

This makes the system easier to debug, trace, test, extend, and control.

---

## 2. Agent Interface

All agents should follow the same interface.

```python
class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def handle(self, message: dict, state: dict) -> dict:
        raise NotImplementedError
```

Example agents:

```python
class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner")

    def handle(self, message: dict, state: dict) -> dict:
        user_task = message["content"]["task"]

        plan = [
            "Analyze the request",
            "Create implementation steps",
            "Send the plan to the coding agent"
        ]

        state["plan"] = plan

        return {
            "sender": self.name,
            "receiver": "coder",
            "type": "task_request",
            "priority": 8,
            "content": {
                "task": user_task,
                "plan": plan,
                "language": "python"
            }
        }
```

```python
class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__("coder")

    def handle(self, message: dict, state: dict) -> dict:
        task = message["content"]["task"]
        plan = message["content"]["plan"]
        language = message["content"]["language"]

        code = f"""
# Task: {task}
# Language: {language}
# Plan: {plan}

class Example:
    pass
"""

        state["code"] = code

        return {
            "sender": self.name,
            "receiver": "evaluator",
            "type": "code_result",
            "priority": 7,
            "content": {
                "code": code
            }
        }
```

---

## 3. Message Format

A `Message` is the structured payload passed between agents.

Use this standard format:

```python
message = {
    "sender": "planner",
    "receiver": "coder",
    "type": "task_request",
    "priority": 8,
    "content": {
        "task": "Build a user registration API",
        "plan": [
            "Create endpoint",
            "Validate email",
            "Hash password",
            "Return JSON response"
        ],
        "language": "python"
    },
    "metadata": {
        "deadline_ms": 5000,
        "max_retries": 2
    }
}
```

Required fields:

```text
sender    : the agent or user who sends the message
receiver  : the next agent that should process the message
type      : message type, such as task_request, task_result, error, critique, final_result
priority  : task priority signal
content   : actual parameters passed to the next agent
metadata  : optional execution metadata, such as deadline, retry count, or trace ID
```

The most important field for parameter passing is:

```python
message["content"]
```

For example, the receiving agent can read parameters like this:

```python
task = message["content"]["task"]
plan = message["content"]["plan"]
language = message["content"]["language"]
```

---

## 4. State Object

The `state` object is the workflow-level shared context.

It stores everything the workflow has learned or produced so far.

Example:

```python
state = {
    "user_request": "Build a user registration API",
    "messages": [],
    "plan": None,
    "code": None,
    "evaluation_result": None,
    "errors": [],
    "retry_count": {},
    "step_count": 0,
    "execution_metadata": {}
}
```

The state should store:

```text
historical messages
intermediate artifacts
current plan
generated code
evaluation results
errors
retry counts
execution metadata
```

Important distinction:

```text
Message = data passed for the current step
State   = shared context for the entire workflow
```

---

## 5. Supervisor

The Supervisor acts as the orchestration layer.

The Supervisor should:

```text
1. Read message.receiver.
2. Find the corresponding agent instance.
3. Call that agent's handle(message, state) method.
4. Record the transition into state.
5. Continue the workflow until the receiver is user or final.
```

The Supervisor does **not** have to be an LLM.

For deterministic transitions, use rule-based routing.

For ambiguous routing decisions, an LLM router may be used, but its output must be validated by code.

Example Supervisor:

```python
class Supervisor:
    def __init__(self, agents: dict):
        self.agents = agents

    def dispatch(self, message: dict, state: dict) -> dict:
        receiver = message["receiver"]

        state["messages"].append(message)
        state["step_count"] += 1

        if receiver == "user":
            return message

        if receiver not in self.agents:
            return {
                "sender": "supervisor",
                "receiver": "user",
                "type": "error",
                "priority": 10,
                "content": {
                    "error": f"Unknown receiver: {receiver}"
                }
            }

        agent = self.agents[receiver]
        response = agent.handle(message, state)

        state["messages"].append(response)

        return response
```

Main runtime loop:

```python
message = initial_message

while message["receiver"] != "user":
    message = supervisor.dispatch(message, state)

print(message["content"])
```

---

## 6. Why Agents Should Communicate Through Supervisor

Agents should not directly call each other because direct calls create tight coupling.

Bad pattern:

```python
planner.call(coder)
coder.call(evaluator)
```

Preferred pattern:

```text
PlannerAgent returns Message(receiver="coder")
Supervisor routes Message to CoderAgent
CoderAgent returns Message(receiver="evaluator")
Supervisor routes Message to EvaluatorAgent
```

Benefits:

```text
1. Centralized routing
2. Easier debugging
3. Unified logging
4. Unified retry logic
5. Unified error handling
6. Tool permission control
7. Easier priority scheduling
8. Easier agent replacement
9. Loop prevention
10. Better observability
```

---

## 7. Supervisor as Rule-Based Router or LLM Router

The Supervisor does not have to be a powerful LLM.

Recommended design:

```text
Rule-based routing first.
LLM-based routing only for ambiguous cases.
Always validate LLM router output with code.
```

Example rule-based routing:

```python
def route(message: dict, state: dict) -> str:
    if message["type"] == "user_request":
        return "planner"

    if message["type"] == "plan_ready":
        return "coder"

    if message["type"] == "code_result":
        return "evaluator"

    if message["type"] == "evaluation_failed":
        return "coder"

    if message["type"] == "evaluation_passed":
        return "user"

    return "supervisor"
```

For LLM-based routing, the LLM should return structured JSON only:

```json
{
  "next_agent": "coder",
  "reason": "The plan is ready and should now be implemented.",
  "priority": 8
}
```

Then validate it:

```python
VALID_AGENTS = {"planner", "coder", "evaluator", "user"}

if llm_output["next_agent"] not in VALID_AGENTS:
    raise ValueError("Invalid next_agent from LLM router")
```

---

## 8. Task Priority

Task priority can be suggested by agents, but the final priority should be computed by the Supervisor or Scheduler.

Priority should consider:

```text
user-blocking status
dependencies
safety relevance
deadlines
retry count
business importance
execution cost
waiting time
```

Recommended priority scale:

```text
P0 = 100: critical safety, security, legal, urgent user-blocking issue
P1 = 80 : high-priority user-blocking task
P2 = 60 : normal task
P3 = 40 : low-priority task
P4 = 20 : background task
```

Example priority computation:

```python
def compute_priority(task: dict) -> int:
    score = task.get("base_priority", 60)

    if task.get("user_blocking"):
        score += 20

    if task.get("safety_related"):
        score += 30

    if task.get("blocks_other_tasks"):
        score += 15

    if task.get("deadline_ms", 999999) < 3000:
        score += 10

    if task.get("retry_count", 0) > 0:
        score += 5

    if task.get("estimated_cost") == "high":
        score -= 5

    return min(max(score, 0), 100)
```

---

## 9. Scheduler and Priority Queue

The Scheduler owns task execution order.

The Supervisor decides what tasks should exist.

The Scheduler decides which task runs first.

Use a priority queue.

```python
import heapq
import time


class Scheduler:
    def __init__(self):
        self.heap = []
        self.counter = 0

    def submit(self, task: dict):
        self.counter += 1
        priority = compute_priority(task)

        # heapq is a min-heap, so use negative priority.
        heapq.heappush(
            self.heap,
            (-priority, task.get("created_at", time.time()), self.counter, task)
        )

    def pop_next(self):
        if not self.heap:
            return None

        return heapq.heappop(self.heap)[3]
```

A task can wrap a message:

```python
task = {
    "task_id": "task_001",
    "agent": "coder",
    "message": {
        "sender": "supervisor",
        "receiver": "coder",
        "type": "task_request",
        "priority": 8,
        "content": {
            "task": "Implement the plan",
            "plan": ["step 1", "step 2"]
        }
    },
    "base_priority": 80,
    "user_blocking": True,
    "blocks_other_tasks": True,
    "deadline_ms": 5000,
    "retry_count": 0,
    "created_at": time.time()
}
```

---

## 10. Dependency-Aware Scheduling

Some tasks cannot run until other tasks finish.

Example:

```text
ResponseAgent cannot run before PolicyAgent and OrderAgent finish.
```

Task format:

```python
task = {
    "task_id": "response_task",
    "agent": "response_agent",
    "depends_on": ["order_task", "policy_task"],
    "message": {...}
}
```

Dependency check:

```python
def is_ready(task: dict, completed_tasks: set) -> bool:
    return all(dep in completed_tasks for dep in task.get("depends_on", []))
```

Scheduler should only execute ready tasks.

---

## 11. Full Runtime Pattern

The final execution pattern should look like this:

```python
agents = {
    "planner": PlannerAgent(),
    "coder": CoderAgent(),
    "evaluator": EvaluatorAgent()
}

state = {
    "user_request": "Build a user registration API",
    "messages": [],
    "plan": None,
    "code": None,
    "evaluation_result": None,
    "errors": [],
    "retry_count": {},
    "step_count": 0,
    "execution_metadata": {}
}

supervisor = Supervisor(agents)

message = {
    "sender": "user",
    "receiver": "planner",
    "type": "user_request",
    "priority": 10,
    "content": {
        "task": "Build a user registration API"
    }
}

while message["receiver"] != "user":
    message = supervisor.dispatch(message, state)

print("Final result:")
print(message["content"])
```

---

## 12. Implementation Requirements

The implementation should satisfy these requirements:

```text
1. Each agent is a separate class.
2. Each agent implements handle(message, state) -> message.
3. Agents do not directly call each other.
4. Agents communicate through structured messages.
5. Message contains sender, receiver, type, priority, and content.
6. Supervisor reads message.receiver and routes to the correct agent.
7. Supervisor records transitions into state.
8. State stores workflow-level context.
9. Supervisor can be rule-based; it does not have to be an LLM.
10. If an LLM router is used, its output must be validated by code.
11. Task priority can be suggested by agents but finalized by Supervisor or Scheduler.
12. Scheduler should use a priority queue.
13. Priority should consider user-blocking status, dependencies, safety relevance, deadlines, and retry count.
```

---

## 13. Acceptance Criteria

The implementation is complete when:

```text
1. A user message can enter the system.
2. Supervisor routes it to the first agent.
3. The first agent returns a new message.
4. Supervisor routes that message to the next agent.
5. State records all messages and intermediate artifacts.
6. The workflow stops when receiver == "user".
7. Priority queue can order tasks by priority.
8. Scheduler does not execute dependency-blocked tasks.
9. The system can be extended by adding a new agent class without changing existing agents.
```

---

## 14. Summary

The core design is:

```text
Agent = class with handle(message, state)
Message = structured parameter package
State = workflow-level shared context
Supervisor = orchestration layer
Scheduler = priority-based executor
```

The most important code path is:

```python
receiver = message["receiver"]
agent = agents[receiver]
response = agent.handle(message, state)
```

This is the foundation of code-level multi-agent communication.
