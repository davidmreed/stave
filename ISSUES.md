# Scenarios

Inside a single static crew

- [X] Swap assignee from one slot to another.
  - [X]... with a nonexclusive assignment retained.

From one static crew to another

- [X] This should not make swapping available. It should be valid to place someone on multiple static crews, even across role groups

From one event crew to another

- [ ] Same

Inside a single override crew

- [X] Swap assignee from one slot to another.
  - [X]... with a nonexclusive assignment retained.

From one override crew to another on the same Role Group

- [FAIL] Swap assignee from one slot to another.
  - [ ]... with a nonexclusive assignment retained.

From one override crew to another on a different Role Group

- [X] Swap assignee from one slot to another.
  - [X]... with a nonexclusive assignment removed.

From a static crew assignment to an override crew

- [X] Swap assignee from one slot to another.
  - [X] ... with a nonexclusive assignment removed.
  - [X] ... exposing an underlying static crew assignment.

Assigning a static crew

- [FAIL] Existing override-crew assignments should be removed (should we retain override crew assignments that are not populated by the static crew?)
- [FAIL] Unavailable members should be overridden to blank
- [ ] Members newly available due to override-crew assignment removal should NOT be added to static crew assignments where they were previously blanked.
      This needs to be a user decision. (We cannot tell the difference between a user blank and our blank)

Unassigning a static crew

- [X] Should succeed, but have no other implications.

Filling an empty slot on a static crew

- [FAIL] Assigning a static crew member should override them to blank anywhere they are not available for the static crew. (It crashes)



# Bugs

- Assigning on a static crew jumps to the first game, not back to the static crew's header.
- Why is the THO page not showing Crew Builder?
- When Game 1 and Game 2 are at the same time, staffed people on the same Role Group incorrectly show Available for the other game.
  - We need to add the Game to the UserAvailabilityEntry, not just the times.
  - This is an existing bug and we can ship with it present.
- We should show a warning when the user seeks to select an already assigned static crew member on another static crew, but not block it.
- The Already Assigned banner is hideous
