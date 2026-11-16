"""Try the assistant: python ask.py "Can the passenger fly tomorrow for free?" UA100"""

import argparse

from assistant.graph import ask


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the rebooking assistant one question about one flight.")
    parser.add_argument("question")
    parser.add_argument("flight", help="flight number, e.g. UA100 (UA9xx simulates a booking-system outage)")
    args = parser.parse_args()

    result = ask(args.question, args.flight)
    print("answer: ", result.get("answer"))
    print("sources:", result.get("sources", []))


if __name__ == "__main__":
    main()
