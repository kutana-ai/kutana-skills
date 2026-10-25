# When Things Go Wrong

| Refusal | What it means | What you do |
| --- | --- | --- |
| `no_meeting_context` | Your session is not tied to a meeting | Join first, then retry |
| `session_not_active` | Your agent session was stopped | Tell the person; they can start it again in Kutana |
| `wrong_meeting` | You named a meeting you are not in | Use the meeting you joined |
| A missing scope | Your grant does not include that tool | Tell the person which permission it needs |
| A rate limit | You called too often | Wait, then try once more |
| `timeout` from a confirmation | Nobody answered | Treat it as no and say so |
| `not_spoken` from `kutana_speak` | The room heard nothing | Say it again in chat, or retry once |

- Say what failed in one sentence.
- Do not retry the same call in a loop.
- Never describe a refusal as success, and never invent an id a tool did not return.
