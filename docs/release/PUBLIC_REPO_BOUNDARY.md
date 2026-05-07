# Public Repository Boundary

RenaceCHESS treats the public repository as commit-eligible by default, with a small explicit private boundary.

## Private / Not Committed

The following paths are local/private and must not be committed:

- `docs/prompts/`
- `docs/foundationdocs/`
- `.cursorrules`

These paths may contain local agent prompts, foundation documents, or private workflow rules that are not part of the public release artifact.

## Public-Eligible

All other project files are public-eligible, subject to normal credential scanning and review.

## Enforcement

The repository enforces this boundary with:

- `.gitignore` entries
- Git index removal for private paths (where applicable)
- `scripts/check_public_release_boundary.py`
- CI execution of the boundary check in the lint job

## Reviewer Checklist

Before public release:

```bash
python scripts/check_public_release_boundary.py
git ls-files docs/prompts docs/foundationdocs .cursorrules
```

Both checks must confirm that no private boundary files are tracked.
