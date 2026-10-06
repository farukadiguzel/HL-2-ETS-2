# City 17 Freight (working title)
Solo Half-Life 2 mod. Spawn at a depot, take a job from the board, drive a truck on one of two routes, get paid.
Required game: Half-Life 2 (version: verify). ETS2 is inspiration only: no ETS2 assets are used.

## v1 scope
1 truck, 1 job board, 2 routes, payout counter. No Combine patrols, cargo damage or extra routes yet.

## Build route
Hammer map + I/O logic, packaged in hl2/custom. No loader.

## Open items (null cells in sheets) – preflight must be clean before build
payouts, time limits, route lengths, truck model, vehicle script, HUD position, license, credits, remix choice.

## Melty steps for the agent
1. Connect, then game_info (half-life-2, euro-truck-simulator-2), search_mashups.
2. Confirm HL2 can launch straight into the map in one click (launch args); run one_click_check.
3. Build, test in HL2, capture real screenshot, then list_my_mods/create_mod, upload, submit.
Do not publish before the user tests and approves.
