# CarFit Agent - Preference Understanding Spec v1

## Purpose
This document defines the categories of user preferences and inferred needs that the CarFit conversational agent should understand.

The goal is to move beyond simple keyword matching and enable the agent to:
- interpret natural language car preferences,
- ask intelligent follow-up questions,
- update user state meaningfully,
- produce recommendations that reflect the user's actual intent.

---

## 1. Hard Constraints
These are direct, explicit requirements that should act as filters or near-filters.

### Vehicle attributes
- fuel
- body
- gearbox
- year_min
- year_max
- mileage_max
- brand_include
- brand_exclude
- new_or_used

### Budget / ownership constraints
- budget_min
- budget_max
- max_running_cost
- max_repair_risk

### Geographic / market constraints
- market
- country
- road_conditions

---

## 2. Soft Preferences
These influence ranking rather than acting as strict filters.

- reliability_priority
- comfort_priority
- running_cost_priority
- practicality_priority
- performance_priority
- safety_priority
- resale_priority
- quietness_priority
- premium_feel_priority
- interior_quality_priority
- parking_ease_priority
- tech_features_priority

Each should generally be represented on a 1-10 scale where possible.

---

## 3. Inferred Needs / Lifestyle Signals
These are not always explicitly stated, but can be inferred from natural language.

### Usage patterns
- city_use
- highway_use
- mixed_use
- family_use
- work_use
- delivery_use
- commuting_use
- weekend_use
- long_trip_use

### Context / constraints
- compact_size_preference
- easy_parking_preference
- bad_roads_use
- winter_use
- low_maintenance_preference
- low_noise_preference
- premium_experience_preference

---

## 4. Human Natural-Language Signals
The agent should be able to interpret phrases like:

- "small car"
- "easy to park"
- "cheap to run"
- "comfortable on long drives"
- "family car"
- "big trunk"
- "quiet interior"
- "feels premium"
- "doesn't have expensive surprises"
- "good for city traffic"
- "good for food delivery"
- "first car"
- "fun but practical"
- "reliable but not boring"

These phrases should not be treated only as keywords. They should map to structured priorities, inferred needs, or follow-up questions.

---

## 5. Conversation Goals
Each user message may represent one of these goals:

- recommend
- refine
- compare
- explain
- broaden_search
- narrow_search
- reset_preferences

The agent should classify the user intent before deciding what to do next.

---

## 6. Missing Information the Agent May Need
The agent should detect when critical information is missing and decide whether to ask a follow-up question.

Examples:
- budget
- gearbox preference
- fuel preference
- body style preference
- city vs highway use
- whether a constraint is mandatory or flexible

The agent should prefer asking the single most useful next question rather than several generic questions at once.

---

## 7. Example Need Mappings

### Example: "I want a small car that I can deliver pizza with"
Possible interpretation:
- delivery_use = true
- city_use = true
- compact_size_preference = true
- easy_parking_preference = true
- running_cost_priority = high
- reliability_priority = high
- performance_priority = low

### Example: "I need something comfortable for long highway drives"
Possible interpretation:
- highway_use = true
- comfort_priority = high
- quietness_priority = high
- performance_priority = medium
- likely follow-up: body style or budget

### Example: "I want something cheap to buy and cheap to maintain"
Possible interpretation:
- running_cost_priority = high
- reliability_priority = high
- budget sensitivity = high
- likely follow-up: budget range

### Example: "I need a reliable family car with a big trunk"
Possible interpretation:
- family_use = true
- practicality_priority = high
- reliability_priority = high
- likely body preference = wagon or SUV

---

## 8. Design Principles
The agent should:
- understand both explicit constraints and implied needs,
- prefer meaningful clarification over generic questioning,
- explain what it understood from the user,
- show what changed after each follow-up answer,
- avoid pretending to know things it has not inferred confidently.

---

## 9. Current Known Gap
The current system is stronger at:
- explicit filters,
- deterministic scoring,
- fallback behavior,
- memory.

The current system is weaker at:
- real-world intent understanding,
- human-like follow-up conversation,
- use-case interpretation,
- meaningful adaptation after vague follow-up answers.

This specification is the foundation for improving those gaps.