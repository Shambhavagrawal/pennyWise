---
description: End the current development session
argument-hint: (interactive)
---

# End Session

Before running the script, ask the user for their completion status:
- **Complete**: Work item is fully done
- **Incomplete**: Work is paused, will continue later
- **Cancel**: Abandon this session

Then run:

```bash
python scripts/session/cli.py end --complete --summary "<SUMMARY>"
# or: python scripts/session/cli.py end --incomplete --summary "<SUMMARY>"
```

Display the output to the user.

If the work item was marked complete and all quality gates passed, create a PR:

```bash
gh pr create --title "<type>: <title>" --body "## Summary\n<summary>\n\n## Quality Gates\n<gate results>"
```
