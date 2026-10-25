# Build and Share: Refusals and Limits

## Build Refusals (from `kutana_build_screen_image`)

| Code | What you do |
| --- | --- |
| `build_directive_refused`, `build_dockerfile_refused` | Remove the named instruction (privileged steps, host networking, host mounts and build secrets are never allowed) |
| `build_database_workload_refused` | Do not run a database as the app; connect to the datastores that already exist (`egress_policy="existing-datastores"`) |
| `build_base_not_permitted` | Use a base image from the returned `allowlist` |
| `build_request_invalid` | Fix the named `fields` and send it again |
| `share_screen_build_in_progress` | Wait on the build it names; it has not failed |
| `share_screen_build_rate_limited`, `share_screen_build_circuit_open` | Stop and talk to the room |
| `share_screen_build_budget_exhausted` | The workspace is out of agent minutes; tell the person |
| `build_not_available`, `share_screen_build_not_permitted` | Building is not on here; use a listed profile |

## Build Failures (from `kutana_get_screen_build`)

- The `failure` block carries `code`, `instruction`, `line`, `exit_code` and `log_tail`.
- `build_instruction_failed`: your recipe. Fix it.
- `build_timeout`: the recipe is too slow, not wrong.
- `build_substrate_unavailable`: not your fault. Say so.
- `upstream_transient`: the check did not get through. The build is still going: poll again.
- `reused: true`: this exact image was built before. Share it now.

## Share Refusals (from `kutana_share_screen`)

| Code | What you do |
| --- | --- |
| `share_screen_unknown_profile`, `share_screen_unknown_size` | Pick a name from the returned list |
| `share_screen_profile_unavailable` | Try again shortly, or use another profile |
| `share_screen_no_capacity` | Stop one of your `live_shares`, or share without `additional` |
| `share_screen_budget_exhausted` | Out of agent minutes; tell the person |
| `share_screen_blocked` | The approver declined or did not answer |
| `share_screen_not_configured` | Screens are not available here; publish a file with `kutana_artifact` instead |
| `share_screen_dials_unknown` | Fix the `dials` names; nothing was claimed |

## Configuration Inside Your App

- Sibling addresses and any datastore settings arrive as JSON at the path in the
  `KUTANA_WORKLOADS_CONFIG` environment variable. Read the variable; never hard-code it.
- A port that does not answer like a web server is shared as an in-cluster address,
  not a page. Say "it is listening on <port>" rather than offering a link.
