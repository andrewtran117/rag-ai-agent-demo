"""CLI entrypoint for the RAG agent."""

import sys
from dotenv import load_dotenv

load_dotenv()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        from ingest import ingest
        ingest()
        return

    from agent import run_agent

    print("RAG Agent (type 'quit' to exit)")
    print("-" * 40)

    while True:
        try:
            question = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        print("\nAgent: ", end="", flush=True)
        answer = run_agent(question)
        print(answer)


if __name__ == "__main__":
    main()
