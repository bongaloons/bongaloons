# Bugs
- Slider for number of notes when creating a beatmap is not working.
- When >500 notes, the game starts to lag because we are rendering all the dots at once.
- Remove all our print statements.
- Notes matching is not very ergonomic: sometimes you miss a few notes and you're behind or do too many and you're ahead.
- Frontend: the super track is not responsive.
- Leaderboard: if you don't want to enter your score, you should not be required to.

# Improvements
- I am quite unhappy with the way we modeled our backend, especially notes matching/resolution and how the DS is stored. I feel it is inefficient and needs to be refactored.
- Move all of our jank state management into a clean state machine.
- There are some global variables in the backend that is not how i would have done this code.
  - The one-worker fix should not be a patch in the first place. This is because of mediapipe global var loading.
- What in the cursor? Get rid of all jank AI code.