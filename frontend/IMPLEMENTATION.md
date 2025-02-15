# Implementation Logic
This document describes the game logic and implementation details.

# USER LEVEL FEATURE (frontend <> backend)
## Feature:
### Part 1
- User slaps left hand
[after 100ms]
- Bongo cat slaps left to mirror user
- User gets "Good" and some points added

### Inputs (from frontend)
- Video stream(?)
- Current time

### Outputs (from backend)
- What pose you're doing (render bongo cat mirror)
    - Left hand raise | Right hand raised | both hand raised | ..
- Accuracy ("Good" vs "Bad" vs "Perfect" vs "Miss")

### Implementation note
- If note A at time 0, and note B at time 10. A hit at time 4.9 registers to A and a hit at 5.1 registers to note B.
- Misses is if there is not hit in the duration that counts for the note (time X +- our tolerance delta)


### Part 2
- If a dot passes without being hit
- User gets "Miss" and some points lost


### Implementation note
- Backend runs a thread loop that checks on not. If note is not hit, backend tells to frontend there is a miss.


# GABE LEVEL FEATURE (backend <> GiB)

## Input (from backend to video stream)
- Live video stream to gabe (at most 2s interval)

## Output (from video stream to backend)
- Gabe sends back what the current pose is 

