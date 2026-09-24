# Work notes: tests/test_avail.py (show-unavail-applicants branch)

Goal: make ALL tests in `tests/test_avail.py` pass, and implement the stubbed
(`: ...`) tests. Run tests with:  `just test tests/test_avail.py`
(justfile: `test` = `uv run pytest -n logical {{arguments}}` — pytest-xdist parallel).
NOTE: `just test <args>` treats extra tokens as recipe args; to pass a single
test id use:  `just test "tests/test_avail.py::test_name"` (quote it).

DATABASE: postgres is NOT running by default. Bring it up first with:
    `just run-postgres`     (docker compose -f docker-compose.dev.yml up -d)
Without it, ~38 tests ERROR with `psycopg2.OperationalError: Connection refused`.

## Current state (as of this note)
After `just run-postgres`, result: **3 failed, 48 passed** in tests/test_avail.py.
The 3 failures:

### 1. test_get_potential_applications  -> `assert 0 == 4`
- Creates an `ApplicationFormFactory()`, then
  `CrewFactory(kind=models.CrewKind.OVERRIDE_CREW, ...)`.
- BUT `tests/factories.py` `CrewFactory.kind` is
  `factory.fuzzy.FuzzyChoice(models.CrewKind)` (ALL 3 kinds, random!).
  So `CrewFactory(kind=OVERRIDE_CREW)` may yield a crew whose kind differs.
  Actually the test explicitly passes kind=OVERRIDE_CREW so crew kind is fine.
- `am.get_potential_applications(crew, game, role_group.roles.first())` returns [].
- Suspicion: `_filter_for_basic_availability` filters out everything. It only
  filters when `crew.kind == OVERRIDE_CREW` AND availability kind is
  BY_DAY/BY_GAME. `ApplicationFormFactory.application_availability_kind` is a
  FuzzyChoice over ALL 3 kinds -> often BY_DAY or BY_GAME. For BY_GAME it needs
  `game in app.availability_by_game.all()` — but the test never sets
  availability_by_game on the applications -> all filtered -> 0. THIS IS THE BUG
  (or the test is meant to force WHOLE_EVENT kind).
  => Likely fix in TEST: pin `application_form.application_availability_kind =
     WHOLE_EVENT` (so `_filter_for_basic_availability` returns all apps) OR set
     availability_by_game on each app. Confirm intent before changing.
  => Do NOT "fix" by gutting `_filter_for_basic_availability`; it's real logic.

### 2. test_set_assignment__swap_roles_one_to_one_on_override_crew_with_nonexclusive
- The test body contains a stray `breakpoint()` on line 693 (see
  `tests/test_avail.py:693`). Under xdist, hitting it raises `bdb.BdbQuit`.
  => REMOVE the `breakpoint()` (it's leftover debug). Then verify the real logic.
- Test: two users on an override CREW: user A on `role`, user B on `other_role`
  AND `nonexclusive_role`. `am.set_assignment(role, crew, other_application.user)`.
  Expected: user B now owns BOTH `role` and `nonexclusive_role` (nonexclusive
  role is KEPT because it's nonexclusive, even though user B is being moved out
  of `other_role` into `role`). User A unassigned, removed from crew.

### 3. test_set_assignment__swap_roles_static_crew_to_override_crew -> UserWarning N+1
- Fails on **django-zeal N+1** (not a logic assert). Message:
  `N+1 detected on stave.Crew.event_role_group_assignments ... in get_context`
  at `stave/models.py:599` (`Crew.get_context`).
- Root cause: Zeal counts same (model, field) from the SAME callsite.
  `Crew.get_context` (models.py:598) runs `self.event_role_group_assignments.first()`
  then `.role_group_assignments.first()` then `.role_group_override_assignments.first()`.
  Called in a loop (over multiple crews/users) -> 3 same-callsite accesses >=
  threshold -> alert.
- Zeal config: `stave/settings/development.py:74` sets `ZEAL_RAISE=False`,
  threshold=3, but `pyproject.toml [tool.pytest.ini_options].filterwarnings`
  line 79 turns `error:.*N\+1.*stave/stave:UserWarning` -> warnings become ERRORS
  in the test run for `stave/stave` files. (factories' N+1s are ignored:
  `ignore:.*N\+1.*tests/factories:UserWarning`.)
- So in the test run, ANY N+1 surfaced from a `stave/stave...` module is fatal.
- Fix options (pick the cleanest, real one):
   a) Preload the needed reverse-M2M in the queryset/prefetch in `avail.py` so
      `get_context` hits the result cache. But `get_context` reads 3 different
      reverse relations (event_role_group_assignments, role_group_assignments,
      role_group_override_assignments) — need all prefetched or use `.first()`
      caching.
   b) Cache the result of `get_context()` on the instance (compute once).
   c) Add a Zeal allowlist entry for `stave.Crew.event_role_group_assignments`
      (legitimate: it's a "look up which game this crew is assigned to" and
      `.first()` legitimately returns 1).
   NOTE: the passing test `test_set_assignment__swap_roles_one_to_one_on_override_crew`
   (no nonexclusive) does NOT hit the N+1 — it has only 2 users. The failing one
   likely loops more. Re-examine: `set_crew_assignment` loops over
   `crew.assignments.all()` calling `_swap_out_of_assignments` -> `get_context`.
- IMPORTANT: Do not just raise ZEAL threshold; the filterwarnings `error` will
  still fire. Fix the underlying prefetch/cache OR allowlist with a clear comment.

## Key files
- `stave/avail.py` — the partial new algorithm. Main classes:
  - `ConflictKind` (enum): NONE / NON_SWAPPABLE_CONFLICT / SWAPPABLE_CONFLICT
  - `UserAvailabilityEntry` dataclass: overlap() core logic
  - `AvailabilityManager`: `with_application_form()`, `static_crews`, `event_crews`,
    `user_availability`, `get_game_count_for_user`, `game_counts_by_user`,
    `user_event_availability`, `user_static_crew_availability`,
    `get_application_counts`, `get_potential_applications`, `get_application_entries`,
    `get_swappable_assignments`, `get_non_swappable_assignments`,
    `get_application_for_assignment`, `get_assignment`,
    `set_assignment`, `set_crew_assignment`, `_swap_out_of_assignments`.
- `stave/models.py`:
  - `Crew` (line 574), `CrewKind` line 558 (EVENT_CREW=1, GAME_CREW=2, OVERRIDE_CREW=3).
  - `Crew.get_context()` line 598 -> returns Game (or Event or None).
  - `CrewAssignment` line 619 (crew, user|null, role; unique [crew,role]).
  - `RoleGroupCrewAssignment` line 904: `crew` (static, nullable), `crew_overrides`
    (nullable). `effective_crew_by_role_id()` line 924 merges both.
  - `Application` line 1771: `move_status_forwards_for_assignment()` (1991),
    `move_status_backwards_for_unassignment()` (1979), `has_assignments()` (1837).
  - `ApplicationStatus` (1015), `IN_PROGRESS_STATUSES` (1031), `CLOSED_STATUSES` (1038).
  - `ApplicationKind` (1133): ASSIGN_ONLY / CONFIRM_THEN_ASSIGN.
  - `ApplicationAvailabilityKind` (1144): WHOLE_EVENT / BY_DAY / BY_GAME.
  - `Role.nonexclusive` (173): "Nonexclusive Roles can be held simultaneously
    with another Role in the same Role Group."
- `tests/factories.py`, `tests/conftest.py` (zeal_context autouse fixture, line 28).
- `stave/settings/development.py`: ZEAL config.

## Crew kinds / semantics (from tests)
- GAME_CREW  = "static crew"  -> assignable to multiple games (no start/end time
  on the entry when unassigned), kind==GAME_CREW.
- OVERRIDE_CREW = "game crew" -> a crew for a single game (a RoleGroupCrewAssignment
  with crew_overrides). Always has start/end times via its Game.
- EVENT_CREW = "event crew" -> works across the whole event (EventRoleGroupCrewAssignment).
  (Note the task text labels GAME_CREW as "static" and OVERRIDE_CREW as "game crew/override".)

## Overlap / ConflictKind semantics (from passing tests)
`existing_entry.overlaps(other, swappable_role_groups)`:
- Self-swap (same start&end & same role_group): both exclusive -> SWAPPABLE_CONFLICT;
  else NONE.
- Two override crews (times present): time overlap & role_group swappable or same ->
  SWAPPABLE_CONFLICT else NON_SWAPPABLE_CONFLICT.
- Two same-kind non-time crews (static without assignment / event crews):
  role_group in swappable -> SWAPPABLE else NON_SWAPPABLE.
- Different kinds -> NONE ("non_meaningful").
- NOTE test line 429/472 pass `self.role_groups` (a set of RoleGroup) as the
  `swappable_role_groups` arg.

## STUB TESTS to implement (line : name)
- 244 test_user_availability_entry__override_of_static_crew
- 416 test_game_crew_assignments
- 419 test_user_availability
- 422 test_user_event_availability
- 423 test_user_static_crew_availability
- 424 test_get_game_count_for_user
- 427 test_game_counts_by_user
- 430 test_get_application_counts
- 469 test_get_application_entries
- 472 test_get_swappable_assignments
- 519 test_get_application_for_assignment
- 522 test_get_assignment
- 767 test_set_assignment__swap_roles_static_crew_to_blank
- 768 test_set_assignment__swap_roles_event_crew
- 774 test_set_assignment__swap_roles_event_crew_keep_nonexclusive
- 775 test_set_assignment__static_crew_override_replace_blank_with_original
- 778 test_set_crew_assignment

## Reference passing tests to model stubs on
- `test_set_assignment__swap_roles_one_to_one_on_override_crew` (615)
- `test_set_assignment__swap_roles_static_crew_to_override_crew` (710)
- `test_set_crew_assignment__assign_crew_over_individual_assignments` (583)
- `test_set_assignment__open_slot` (525), `__replace_existing` (542),
  `__removes_existing_assignment` (565)

## Open questions / TODO before next step
1. Confirm whether `test_get_potential_applications` is a TEST bug (pin
   WHOLE_EVENT) — check git blame / intent. (Leading hypothesis: test should set
   `application_availability_kind=WHOLE_EVENT`.)
2. Decide N+1 fix strategy for `Crew.get_context` (cache vs prefetch vs allowlist).
3. Remove stray `breakpoint()` at tests/test_avail.py:693.
4. Verify `game_counts_by_user` uses `self.applications` (line 334) — fine.

## Commands
- Bring DB up: `just run-postgres`
- Run all: `just test tests/test_avail.py`
- Run one: `just test "tests/test_avail.py::test_name"`
- Lint/format: ruff is configured (dev dep). Run `uv run ruff check stave tests`
  and `uv run ruff format --check stave tests` (confirm from prek.toml).
