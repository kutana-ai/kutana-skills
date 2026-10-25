# Turn Taking

Kutana keeps **one speaker queue** per meeting. People and agents share it.

1. **Raise your hand:** `kutana_raise_hand(meeting_id, topic="<what you will say>")`.
   A `queue_position` of 0 means the floor is yours now.
2. **Otherwise wait:** poll `kutana_get_meeting_events(event_type="turn_your_turn")`,
   and keep listening while you wait.
3. **Take the floor:** `kutana_start_speaking(meeting_id)`.
4. **Speak:** `kutana_speak(meeting_id, text)`, or post in chat if you joined without voice.
5. **Release the floor:** `kutana_mark_finished_speaking(meeting_id)` as soon as you
   are done, so the queue moves.

- **Changed your mind:** `kutana_cancel_hand_raise(meeting_id)`.
- **Who is waiting:** `kutana_get_queue_status(meeting_id)`.
- **Your own state:** `kutana_get_speaking_status(meeting_id)`.
- **Urgent only when it is:** `priority="urgent"` jumps the queue. Use it for a
  correction the room is acting on, never to be heard sooner.
- **Never talk over a person.** If someone starts speaking while you hold the floor,
  finish your sentence and release the floor.
