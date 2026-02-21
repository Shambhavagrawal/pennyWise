---
description: Capture learnings from the current session
argument-hint: (interactive)
---

# Capture Learnings

This is the interactive learning capture command.

1. Analyze the current session's work (git diff, files changed, problems solved)
2. Generate 2-3 learning suggestions based on what was accomplished
3. Present them to the user as a multi-select list with auto-categorized categories
4. For each selected learning, run:

```bash
python scripts/session/cli.py learn-add --content "<CONTENT>" --category <CATEGORY> [--tags <TAG1> <TAG2>] [--session <N>]
```

Valid categories: architecture_patterns, gotchas, best_practices, technical_debt, performance_insights, security

Display the output for each added learning.
