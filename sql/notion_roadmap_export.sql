-- Notion SQL (notion-query-data-sources, sql mode) — full roadmap export for roadmap/audit.py.
-- Notion returns at most 100 rows per call: run this with OFFSET 0, 100, 200, ... until a
-- page comes back with fewer than 100 rows, and concatenate the "results" arrays into one
-- JSON list. Column names are the Notion property names; do not alias them.
SELECT url, "Item", "Production Status", "Description", "Ad ID(s)", "Reference",
       "Market", "Format", "Campaign Type", "Production Type", "Version", "Creator Name",
       "Language Pair", "Legacy Cate.", "Category", "Element", "Product Feature",
       "date:Production Date:start", "date:Launch date:start", "date:Paused date:start",
       "Pause reason", "SP status", "SP score", "Spend to date", "Owner",
       "Relation to Influencer Licenses", "Parent creative", createdTime
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
ORDER BY url
LIMIT 100 OFFSET 0
