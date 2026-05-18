"""QA agent — reads specs from the vector DB, plans tests, executes them in a browser."""

import os
import json
from datetime import datetime
import anthropic
from search import search_docs
from browser_tools import (
    browser_navigate,
    browser_click,
    browser_type,
    browser_screenshot,
    browser_assert,
    browser_get_text,
    browser_get_html,
    close_browser,
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"
REPORTS_DIR = "reports"

TOOLS = [
    {
        "name": "search_docs",
        "description": "Search the knowledge base for specs, PRDs, or requirements. Use this to understand what the app should do before writing tests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "browser_navigate",
        "description": "Navigate the browser to a URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to navigate to"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "browser_click",
        "description": "Click an element on the page using a CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to click"}
            },
            "required": ["selector"],
        },
    },
    {
        "name": "browser_type",
        "description": "Type text into an input field using a CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the input field"},
                "text": {"type": "string", "description": "Text to type"},
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current page. Use this to capture evidence of test results.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_assert",
        "description": "Check if an element matching a CSS selector is visible on the page. Returns PASS or FAIL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "condition": {"type": "string", "description": "CSS selector to check for visibility"}
            },
            "required": ["condition"],
        },
    },
    {
        "name": "browser_get_text",
        "description": "Get the text content of an element on the page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element"}
            },
            "required": ["selector"],
        },
    },
    {
        "name": "browser_get_html",
        "description": "Get the HTML of the current page. Use this BEFORE clicking or typing to find the correct CSS selectors. Do not guess selectors.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "write_report",
        "description": "Write the final QA test report as structured JSON. Call this when all tests are done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "report": {
                    "type": "object",
                    "description": "The test report with test results, screenshots, and summary",
                }
            },
            "required": ["report"],
        },
    },
]

PLAN_PROMPT = (
    "You are a QA agent. The user wants you to test a web application.\n\n"
    "STEP 1 — PLAN: First, use search_docs to find any relevant specs or requirements "
    "in the knowledge base. Then output a numbered test plan in plain text. "
    "Each test should have: a name, steps to execute, and expected result.\n\n"
    "Do NOT execute any browser actions yet. Only search docs and output the plan."
)

EXECUTE_PROMPT = (
    "You are a QA agent. Execute the approved test plan against the live application.\n\n"
    "IMPORTANT: After navigating to any page, ALWAYS call browser_get_html first to read "
    "the actual page structure. Use the real CSS selectors from the HTML. NEVER guess selectors.\n\n"
    "For each test:\n"
    "1. Navigate to the page\n"
    "2. Call browser_get_html to see the actual selectors\n"
    "3. Use the browser tools to perform the steps with real selectors\n"
    "4. Take a screenshot after key actions\n"
    "5. Use browser_assert to verify expected results\n\n"
    "After all tests are done, call write_report with a JSON object containing:\n"
    "- url: the URL tested\n"
    "- tests: array of {name, status (PASS/FAIL), steps_taken, evidence (screenshot paths), notes}\n"
    "- summary: overall pass/fail count\n"
)


def _handle_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_docs":
        results = search_docs(tool_input["query"])
        return "\n\n".join(f"[{r['source']}]: {r['text']}" for r in results)

    elif tool_name == "browser_navigate":
        return browser_navigate(tool_input["url"])

    elif tool_name == "browser_click":
        return browser_click(tool_input["selector"])

    elif tool_name == "browser_type":
        return browser_type(tool_input["selector"], tool_input["text"])

    elif tool_name == "browser_screenshot":
        result = browser_screenshot()
        return f"Screenshot saved: {result['path']}"

    elif tool_name == "browser_assert":
        return browser_assert(tool_input["condition"])

    elif tool_name == "browser_get_text":
        return browser_get_text(tool_input["selector"])

    elif tool_name == "browser_get_html":
        return browser_get_html()

    elif tool_name == "write_report":
        return _save_report(tool_input["report"])

    return f"Unknown tool: {tool_name}"


def _save_report(report: dict) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"qa_report_{timestamp}.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    return f"Report saved to {path}"


def _run_loop(system_prompt: str, messages: list) -> str:
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            assistant_content = response.content
            tool_results = []

            for block in assistant_content:
                if block.type == "tool_use":
                    print(f"  -> {block.name}({json.dumps(block.input)[:80]})")
                    result_text = _handle_tool_call(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        else:
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text


def run_qa(task: str, url: str):
    # Step 1: Plan
    print("\n--- PLANNING ---\n")
    plan_messages = [
        {"role": "user", "content": f"Test task: {task}\nTarget URL: {url}"}
    ]
    plan = _run_loop(PLAN_PROMPT, plan_messages)
    print(plan)

    # Step 2: Confirm
    print("\n--- CONFIRM ---")
    confirm = input("Approve this test plan? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    # Step 3: Execute
    print("\n--- EXECUTING ---\n")
    exec_messages = [
        {
            "role": "user",
            "content": f"Test task: {task}\nTarget URL: {url}\n\nApproved test plan:\n{plan}",
        }
    ]
    try:
        result = _run_loop(EXECUTE_PROMPT, exec_messages)
        print(f"\n{result}")
    finally:
        close_browser()
