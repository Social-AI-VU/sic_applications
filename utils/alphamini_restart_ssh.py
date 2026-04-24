"""
Utility script for manual AlphaMini SSH daemon lifecycle testing.

Purpose:
1) Manually restart SSH daemon behavior without SSH access:
   by sending a simple command through `mini.pkg_tool.run_py_pkg(...)`, we force
   the robot-side execution path to start a new shell context. In environments
   where shell startup triggers `sshd`, this acts as a lightweight manual
   recovery path for SSH availability.
2) Provide a way to kill the SSH daemon:
   with the kill flag, operators can stop `sshd` on demand and then verify that
   the Alphamini device recovery logic (restart-before-reinstall) behaves as
   expected.
"""

import argparse

import mini.pkg_tool as Tool
import mini.mini_sdk as MiniSdk
MiniSdk.set_robot_type(MiniSdk.RobotType.EDU)

def _run_check(robot_id: str, check_name: str, command: str) -> None:
    """Send one run_py_pkg command to the target robot and print context."""
    print(f"\n=== {check_name} ===")
    print("Command sent through Tool.run_py_pkg:")
    print(command)
    Tool.run_py_pkg(command, robot_id=robot_id, debug=True)


def main() -> None:
    """CLI entry point for kill/restart-style SSH daemon recovery checks."""
    parser = argparse.ArgumentParser(
        description="Utility script for manual AlphaMini SSH daemon lifecycle testing."
    )
    parser.add_argument(
        "--mini-id",
        required=True,
        help="Last 5 digits of AlphaMini serial number (robot_id used by mini SDK).",
    )
    parser.add_argument(
        "--kill-sshd",
        action="store_true",
        help="Kill SSH daemon.",
    )
    args = parser.parse_args()

    print("Starting AlphaMini SSH daemon diagnostics via run_py_pkg (no SSH).")
    print(f"Target mini_id: {args.mini_id}")

    if args.kill_sshd:
        _run_check(
            robot_id=args.mini_id,
            check_name="Kill sshd",
            command="pkill -f sshd",
        )
        print("\nDone. sshd kill command sent. Re-run this script without --kill-sshd to verify status.")
        return

    # Simple command to start a shell (and the SSH daemon again)
    _run_check(
        robot_id=args.mini_id,
        check_name="Simple echo hello",
        command=(
            "if echo hello >/dev/null 2>&1; then exit 0; else exit 21; fi"
        ),
    )

    print("\nDone. SSH daemon should be running now.")


if __name__ == "__main__":
    main()
