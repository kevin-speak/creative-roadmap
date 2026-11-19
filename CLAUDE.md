# Working in this repository

This is the hub for the Speak TW/HK creative roadmap. Read `README.md` first; `docs/notion-schema.md` has every Notion ID, property and option.

- **Runbooks are the product.** `routines/*.md` are executed verbatim by scheduled sessions. Keep them exact: real property names, exact option strings, explicit caps. When the Notion schema changes, update `docs/notion-schema.md`, the runbooks and `roadmap/naming.py` in one commit.
- **Notion SQL returns at most 100 rows per call.** Any query over the roadmap must page (`ORDER BY url LIMIT 100 OFFSET n`).
- **Names go through `roadmap/naming.py`.** Do not parse or build ad names by hand; extend the module and its tests instead.
- **Read-only on Meta and BigQuery.** Never write to either. Never delete Notion pages.
- **The repository is public.** Do not commit roadmap exports, creator lists, spend or performance data. Put working files in the session scratchpad.
- **Bulk Notion changes need a plan first.** Produce it with `python3 -m roadmap.audit …`, show the counts, and apply only after Kevin approves.
- Tests: `python3 -m unittest discover -s tests -t .` (standard library only, no install step).
- `sql/sp_score.sql` and `sql/ltv_cac.sql` anchor on the table's `MAX(date)` on purpose; do not switch them to `CURRENT_DATE()`.
