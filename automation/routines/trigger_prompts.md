# Trigger prompts (fresh-session routines)

These are the exact prompts stored on the fresh-session ("auto") Claude Routines. They are
deliberately standalone: a fired session starts from nothing, clones this repo at its default
branch, and follows the runbook file named in the prompt. Edit the runbook to change behaviour;
edit the prompt here (and on the routine) only if the pointer or the connector list changes.

Each prompt carries a **DRY RUN** clause: firing the routine with text beginning `DRY RUN`
(from the Routines UI **Run now** box, or `fire_trigger` with `text`) makes the session verify
connector access with read-only calls and stop, writing nothing to Notion or Slack. Use it to
confirm connectors are attached before enabling a routine.

## Cutover from the session-bound routines (2026-09-03)

Fresh-session triggers created from inside a session **cannot carry MCP connector grants** for
this organization (`create_trigger` rejects the `connectors` parameter, and the trigger is
stored with `mcp_connections: []`). Connectors have to be attached from the web UI:

1. Open [claude.ai/code/routines](https://claude.ai/code/routines) and click the new routine
   (IDs below). Click the pencil icon (**Edit routine**).
2. Under **Connectors**, add the connectors listed for that routine, then save.
3. Click **Run now**, type `DRY RUN` in the text box, and confirm the run reports every
   connector as reachable.
4. Flip the **Repeats** toggle on for the new routine and off for the old session-bound one
   (or use `update_trigger` with `enabled`). Delete the old routine once the first real run
   looks right.

| Routine | New fresh-session trigger | Old session-bound trigger | Connectors to attach |
|---|---|---|---|
| TW Creative Roadmap nightly sync | `trig_01Mu2vcfPW9zXbT9N1s9nXn8` | `trig_01EZ44tzBdZfTfJy1scvf128` | Notion, Slack, Meta-Ads, BigQuery, Hex |
| TW Creative pipeline sync | `trig_01Bz5iWJZ9cBkXjhd2YeCaF4` | `trig_011EhN2rJaHcNoAKHPAY8it3` | Notion, Slack |
| TW winning creative iteration analyst | `trig_01NJznSip628rN38F1f1jHAL` | `trig_01JqGLRu34KTW38yFpWNpDDt` | Notion, Slack, Motion-Creative-Analytics, Meta-Ads |

Schedules are unchanged (UTC cron): nightly sync `0 2 * * *`, pipeline sync `0 1,7 * * *`,
iteration analyst `30 2 * * 1`.

## 1. TW Creative Roadmap nightly sync

```text
ROUTINE FIRE: TW Creative Roadmap nightly sync. You are in a fresh session with the kevin-speak/creative-roadmap repo cloned at its default branch. Execute the runbook at automation/routines/routine1_nightly_sync.md exactly as written (if the file is missing, run `git fetch origin claude/speak-tw-creative-automation-1w6h9d && git checkout claude/speak-tw-creative-automation-1w6h9d` first).

Summary of the job (the runbook is the source of truth): reconcile the Notion TW Creative Roadmap (collection://46a9a0c5-2240-4576-8574-ce81793d224b) against live Meta ads (account 1148917790153640) and the BigQuery SP score query (project speak-v2-2a1f1, SQL embedded in the runbook and also at automation/sp_score.sql); update SP score / SP status / CPFT / Spend to date / Last synced; create rows for unknown live ads; handle Hit Ad transitions (checkbox + post to #hit-ads-library via the hit-ad-to-slack skill if available, otherwise follow the runbook's manual post format); pause detection with owner pings; watch flags; archive hygiene; then post the Slack report to #tw-creative (C0ASFA5F1B3), silent if nothing changed. Respect the sample-row guard (only rows with real 15+ digit Meta ad IDs, or active-status rows created after 2026-08-16). Use the Notion, Meta Ads, BigQuery and Slack connectors; load their tools with ToolSearch. Never write to Meta or BigQuery.

DRY RUN mode: if a routine-fire-payload block is present and its text begins with "DRY RUN", do NOT write anything to Notion or Slack. Instead, verify that the Notion, Meta Ads, BigQuery and Slack connector tools are reachable by making one read-only call to each (e.g. query the roadmap data source, list the ad account's active ads, run a `SELECT 1` in BigQuery, read the last message in #tw-creative), then report which connectors worked and which failed, and stop.

Do this work now, then stop.
```

## 2. TW Creative pipeline sync

```text
ROUTINE FIRE: TW Creative pipeline sync. You are in a fresh session with the kevin-speak/creative-roadmap repo cloned at its default branch. Execute the runbook at automation/routines/routine2_pipeline_sync.md exactly as written (if the file is missing, run `git fetch origin claude/speak-tw-creative-automation-1w6h9d && git checkout claude/speak-tw-creative-automation-1w6h9d` first).

Summary of the job (the runbook is the source of truth): sync the Ideas board (collection://921b7b9b-effe-411d-9fc2-ca99eb48f328, Status = In progress) into the TW Creative Roadmap (collection://46a9a0c5-2240-4576-8574-ce81793d224b) as Plan rows with Reference = idea page URL as the dedupe key; back-sync roadmap rows at Ready-to-Test or later to mark their source idea Done; post Ready-to-Test pings to #tw-creative (C0ASFA5F1B3) tagging <@U0A1E7WENQ6> with an rt-ping-sent Notion comment as the dedupe marker; report design-board-completed hints; post the Slack summary only if something happened. Respect the sample-row guard and the Pillar↔Category number-prefix mapping in the runbook. Use the Notion and Slack connectors; load their tools with ToolSearch. Never delete anything.

DRY RUN mode: if a routine-fire-payload block is present and its text begins with "DRY RUN", do NOT write anything to Notion or Slack. Instead, verify that the Notion and Slack connector tools are reachable by making one read-only call to each (e.g. query the Ideas data source, read the last message in #tw-creative), then report which connectors worked and which failed, and stop.

Do this work now, then stop.
```

## 3. TW winning creative iteration analyst

```text
ROUTINE FIRE: TW winning creative iteration analyst (weekly). You are in a fresh session with the kevin-speak/creative-roadmap repo cloned at its default branch. Execute the runbook at automation/routines/routine3_winner_iteration.md exactly as written (if the file is missing, run `git fetch origin claude/speak-tw-creative-automation-1w6h9d && git checkout claude/speak-tw-creative-automation-1w6h9d` first).

Summary of the job (the runbook is the source of truth): find TW Creative Roadmap rows (collection://46a9a0c5-2240-4576-8574-ce81793d224b) with SP status Hit Ad or P2 Loser and real Meta ad IDs; skip ads that already have a Winning Iteration idea (dedupe on Ad id / Ref in collection://921b7b9b-effe-411d-9fc2-ca99eb48f328); analyze at most 5 (highest spend first) using Motion Creative Analytics (get_auth_context first, then insightType=SPEND before other insight calls, with graceful fallback when Motion lacks coverage); write an iteration brief per the runbook template and create one "Winning Iteration" idea per ad in the Ideas board; post the weekly Slack summary to #tw-creative (C0ASFA5F1B3) tagging <@U0A1E7WENQ6>, silent if no candidates. Use the Notion, Motion Creative Analytics, Meta Ads and Slack connectors; load their tools with ToolSearch. Do not modify parent roadmap rows.

DRY RUN mode: if a routine-fire-payload block is present and its text begins with "DRY RUN", do NOT write anything to Notion or Slack. Instead, verify that the Notion, Motion Creative Analytics, Meta Ads and Slack connector tools are reachable by making one read-only call to each (e.g. query the roadmap data source, call Motion get_auth_context, list the ad account's active ads, read the last message in #tw-creative), then report which connectors worked and which failed, and stop.

Do this work now, then stop.
```
