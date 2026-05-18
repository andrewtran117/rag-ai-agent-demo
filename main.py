"""CLI entrypoint for the RAG agent and QA agent."""

import sys
from dotenv import load_dotenv

load_dotenv()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        from ingest import ingest
        ingest()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "qa":
        from qa_agent import run_qa
        if len(sys.argv) < 4:
            print('Usage: python main.py qa "test description" --url https://example.com')
            return
        task = sys.argv[2]
        url = sys.argv[3].replace("--url=", "") if "=" in sys.argv[3] else (sys.argv[4] if len(sys.argv) > 4 else sys.argv[3])
        # Handle --url flag
        if "--url" in sys.argv:
            url_index = sys.argv.index("--url") + 1
            url = sys.argv[url_index] if url_index < len(sys.argv) else url
        run_qa(task, url)
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
