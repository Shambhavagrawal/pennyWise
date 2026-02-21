---
description: Create a new work item with spec template
argument-hint: (interactive)
---

# Create Work Item

Before running the script, gather the following from the user via questions:
- **Type**: feature, bug, refactor, security, integration_test, or deployment
- **Title**: Human-readable title
- **Priority**: critical, high, medium, or low
- **Dependencies**: (optional) IDs of work items this depends on
- **Urgent**: (optional) whether to mark as urgent

Then run:

```bash
python scripts/session/cli.py work-new --type <TYPE> --title "<TITLE>" --priority <PRIORITY> [--dependencies <ID1> <ID2>] [--urgent]
```

Display the output to the user. After creation, prompt the user to fill out the generated spec file.
