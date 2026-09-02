# IBM Finance & Consulting Skills — Bob BYOS Pack

33 Finance Transformation, AR, FT assessment, FP&A, contract review, executive reporting, and document extraction skills.

## How to connect in IBM Process Studio (BYOS)

1. Go to **Settings ? Skills ? Bring Your Own Skill (BYOS)**
2. Repository URL: `https://github.com/Grace9393/grace-bob-finance-skills`
3. Branch: `main`
4. Folder: `/` (root)
5. Enter your GitHub PAT and click **Connect**

> **Note:** Each subfolder is one skill. The folder name must match the `name:` field in its `SKILL.md`.

## Author-side tooling

`tooling/<skill>/` holds QA scripts that need a browser (playwright) or an HTML
parser (bs4). They sit outside `skills/` on purpose: Process Studio scans every
file in a connected skill and disables the skill if any file imports a package
its runtime lacks. These are run locally by the author, never by the platform.
