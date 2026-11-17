"""Interactive approval for sensitive tool operations."""

class TerminalApproval:

    def __call__(self, tool_name: str, arguments: dict) -> bool:

        print("\n" + "=" * 45)
        print("XENOCODE APPROVAL REQUIRED")
        print("=" * 45)

        print(f"Operation: {tool_name}")

        for key, value in arguments.items():

            if key == "content":
                preview = value[:160].replace("\n", " ")
                print(f"content preview: {preview!r}")
                print(f"content length: {len(value)}")

            else:
                print(f"{key}: {value}")

        try:
            answer = input(
                "\nApprove this operation? [y/N]: "
            ).strip().lower()

        except (EOFError, KeyboardInterrupt):
            return False

        return answer in {"y", "yes"}
