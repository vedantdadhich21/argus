# Repo instructions

1. Before ANY work, read `APK-SENTINEL-REFERENCE.md` (full spec) and `TEAM-WORKPLAN.md` (who owns what).
2. You are assisting ONE person. Only modify files listed under their ownership in `TEAM-WORKPLAN.md` §File Ownership Map. If a needed change falls outside, STOP and tell the human to coordinate.
3. API shapes and the LLM JSON schema are frozen per Reference doc §6, §9, §11. Do not invent new fields.
4. Do not add auth, databases other than SQLite, or features listed in Reference doc §17 (out of scope).
5. After changes, run the verification command for that block from `TEAM-WORKPLAN.md` and paste results.
6. At the end of every session, add an entry to `DEVLOG.md` (newest at top) summarizing what was done, how, and any gotchas — the next person's AI reads it before starting.
