"""Claude agent with search_docs tool use."""

import os
import json
import anthropic
from search import search_docs

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"

TOOLS = [
    {
        "name": "search_docs",
        "description": (
            "Search the knowledge base for relevant information. "
            "Use this when you need to look up facts or context to answer the user's question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant document chunks",
                }
            },
            "required": ["query"],
        },
    }
]

SYSTEM_PROMPT = (
    "You are a helpful research assistant. You have access to a knowledge base of documents. "
    "When the user asks a question, use the search_docs tool to find relevant information, "
    "then provide a clear answer based on what you find. Always cite which source document "
    "your answer comes from."
)


def run_agent(user_question: str) -> str:
    messages = [{"role": "user", "content": user_question}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # If Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Process all tool calls in the response
            assistant_content = response.content
            tool_results = []

            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    if tool_name == "search_docs":
                        results = search_docs(tool_input["query"])
                        result_text = "\n\n".join(
                            f"[{r['source']}]: {r['text']}" for r in results
                        )
                    else:
                        result_text = f"Unknown tool: {tool_name}"

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        # If Claude is done (end_turn), return the text
        else:
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text
