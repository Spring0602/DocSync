"""Thin entry point for the metrics shared with the installed benchmark command."""

from docsync.metrics import evaluate, main

__all__ = ["evaluate", "main"]

if __name__ == "__main__":
    main()
