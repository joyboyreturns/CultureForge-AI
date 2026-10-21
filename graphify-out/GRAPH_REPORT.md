# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- 62 files · ~87,713 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .css 4, (none) 2, .example 1)

## Summary
- 1066 nodes · 2210 edges · 58 communities (49 shown, 9 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 166 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3869ce67`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- QlooHarnessProvider
- Studio Application Shell
- Build Tooling and Dependencies
- TypeScript App Compiler Settings
- Front Page Marketing Copy
- Architecture and Dependency Docs
- Personalised Mockups
- Media Remuxing Utility
- TypeScript Node Build Settings
- OpenCode Configuration
- Audience and Concept Copy
- Studio Concept Mockups
- Cafe Ritual Mockup Detail
- QlooHarnessError
- Front Page Metadata
- TypeScript Project References
- Evidence Test Client
- Graphify MCP Wrapper
- Evidence Store Tests
- Workspace and Exploration Routes
- Evidence Concept Composer
- Studio API Contracts
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Frontend Investigation Client
- Provider Internals and Metering
- Request Metering
- ProjectRequest
- Platform Layer
- ResearchRun
- API Error Handling
- Build Tooling and Entry Points
- Cultural Constellation Graph
- Free Model Transport
- Endpoint Verification Tool
- Anchor Tournament
- Free Naming Layer
- _execute
- Naming Guard and Budget
- ._name_directions
- Naming Layer Tests
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- post
- main.py
- test_api.py
- get_provider
- Investigation Module
- Project knowledge workflow
- Naming Layer Tests
- Evidence Test Module
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 70 edges
2. `App()` - 38 edges
3. `ProjectRequest` - 34 edges
4. `QlooHarnessError` - 29 edges
5. `Platform` - 27 edges
6. `_execute()` - 24 edges
7. `TraceEvent` - 22 edges
8. `EvidenceStore` - 21 edges
9. `ResearchRun` - 20 edges
10. `challenge_directions()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `_rank_venues()` --uses--> `Evidence`  [INFERRED]
  backend/challenge.py → backend/models.py

## Import Cycles
- None detected.

## Communities (58 total, 9 thin omitted)

### Community 0 - "QlooHarnessProvider"
Cohesion: 0.08
Nodes (9): _rank_venues(), rank_entities(), recompose(), Decision, Delivery, QlooHarnessProvider, test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it(), test_a_repeated_brief_reports_that_it_spent_nothing() (+1 more)

### Community 1 - "Studio Application Shell"
Cohesion: 0.10
Nodes (29): BackendStatus, listExplorations(), SavedExploration, TasteSeed, save(), audiencePresets, BarIcon(), BusinessIcon() (+21 more)

### Community 2 - "Build Tooling and Dependencies"
Cohesion: 0.05
Nodes (36): dependencies, lucide-react, motion, react, react-dom, devDependencies, autoprefixer, postcss (+28 more)

### Community 3 - "TypeScript App Compiler Settings"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Front Page Marketing Copy"
Cohesion: 0.23
Nodes (14): CultureForge Light Dashboard Screenshot, Audience Cultural Affinities, Business Concept Exploration, Café Rituals, Connect Cultural Dots, From Insight to What If, A Small Change, A New Angle, Culture, Commerce, and Possibility (+6 more)

### Community 5 - "Architecture and Dependency Docs"
Cohesion: 0.15
Nodes (12): Vite API Proxy, CultureProvider Abstraction, FastAPI Backend, Shared Mock Catalog, MockCultureProvider, CultureForge AI Prototype, Qloo Hackathon Kit CLI, QlooHarnessProvider (+4 more)

### Community 6 - "Personalised Mockups"
Cohesion: 0.32
Nodes (11): CultureForge Concept Studio Desktop Mockup, CultureForge Concept Studio Mobile Mockup, Audience Lens Scenario Exploration, Cultural Signals and Experience Blueprint Panel, Family Market Day Makers Market, Flexible Timing Cultural Signal, Hand-Me-Down House Repair and Resale Shop, Little & Local Concept Store (+3 more)

### Community 7 - "Media Remuxing Utility"
Cohesion: 0.06
Nodes (33): entities(), no_model_calls(), recommend_places(), store(), fake(), fake(), load_qloo_config(), main() (+25 more)

### Community 8 - "TypeScript Node Build Settings"
Cohesion: 0.20
Nodes (9): compilerOptions, lib, module, moduleResolution, noEmit, skipLibCheck, strict, target (+1 more)

### Community 9 - "OpenCode Configuration"
Cohesion: 0.15
Nodes (12): codemode, command, cwd, enabled, timeout, type, mcp, servers (+4 more)

### Community 10 - "Audience and Concept Copy"
Cohesion: 0.25
Nodes (8): Audience Understanding, Business Concept Exploration, Café and Hospitality Experience, Cultural Affinities, Cultural Connections, Cultural Insight Platform, CultureForge AI, Scenario Comparison

### Community 11 - "Studio Concept Mockups"
Cohesion: 0.39
Nodes (8): CultureForge Concept Studio Mobile Mockup, Three Cultural Connections, Cultural Connector, Design-Conscious Gen Z and Young Professionals, Food and Beverage in Brooklyn, New York, Illustrative Fit Score of 94, The Listening Room Cafe, Three Directions, One Cultural Edge

### Community 12 - "Cafe Ritual Mockup Detail"
Cohesion: 1.00
Nodes (3): Café Rituals, Shared Audience, Vinyl Culture

### Community 13 - "QlooHarnessError"
Cohesion: 0.09
Nodes (12): compare_audiences(), own(), rows(), QlooHarnessError, safe_query(), StubProvider, test_a_comparison_needs_both_sides(), test_the_allowlist_covers_every_query_key_the_app_sends() (+4 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.22
Nodes (9): ChallengedDirection, ChallengeResult, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge() (+1 more)

### Community 20 - "Evidence Store Tests"
Cohesion: 0.11
Nodes (13): cached_call(), canonical_key(), get_store(), known_location(), transport_request_count(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one() (+5 more)

### Community 21 - "Workspace and Exploration Routes"
Cohesion: 0.14
Nodes (15): export_exploration(), generate(), list_explorations(), list_keys(), meter_requests(), read_exploration(), read_snapshot(), recent_runs() (+7 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.12
Nodes (16): compose(), ComposedConcept, _facet_rank(), _first_sentence(), _matches(), _number(), Recipe, _tag_name() (+8 more)

### Community 23 - "Studio API Contracts"
Cohesion: 0.18
Nodes (17): AnchorRanking, AudienceComparisonResult, briefKey(), CacheEntry, ChallengeCheck, detailMessage(), generateConcepts(), GeoPoint (+9 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.11
Nodes (24): challengeDirections(), compareAudience(), fetchExploration(), fetchHealth(), fetchSnapshot(), fetchUsage(), postJson(), recompose() (+16 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Frontend Investigation Client"
Cohesion: 0.18
Nodes (14): compareAudiences(), Facet, investigate(), Investigation, listFacets(), run(), GeoLayer, GeoMap() (+6 more)

### Community 30 - "ProjectRequest"
Cohesion: 0.11
Nodes (12): _challenge_one(), ChallengeRequest, CompareAudiencesRequest, ErrorResponse, GenerateResponse, ProjectRequest, RankRequest, RecomposeRequest (+4 more)

### Community 31 - "Platform Layer"
Cohesion: 0.09
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "ResearchRun"
Cohesion: 0.12
Nodes (11): ResearchRegistry, ResearchRun, _install(), StubProvider, test_a_known_location_is_offered_as_the_way_out(), test_a_provider_failure_is_reported_not_crashed(), test_needs_input_becomes_a_clarification(), test_no_local_evidence_becomes_a_clarification() (+3 more)

### Community 33 - "API Error Handling"
Cohesion: 0.22
Nodes (5): error_response(), http_error_handler(), qloo_error_handler(), validation_exception_handler(), ErrorBody

### Community 34 - "Build Tooling and Entry Points"
Cohesion: 0.18
Nodes (6): lucide-react, react, react-dom, fetchResearchRun(), AgentTrace(), poll()

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "Free Model Transport"
Cohesion: 0.12
Nodes (9): _allowed_numbers(), _api_key(), _clean_text(), is_configured(), _load_env_once(), _numbers_are_allowed(), _post(), _word_count() (+1 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Anchor Tournament"
Cohesion: 0.33
Nodes (6): rankAnchors(), AnchorTournament(), run(), Choice, CHOICES, guessDemographic()

### Community 40 - "Free Naming Layer"
Cohesion: 0.11
Nodes (13): _ask_model(), _build_user_prompt(), LlmUnavailable, _parse_json(), test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post() (+5 more)

### Community 41 - "_execute"
Cohesion: 0.20
Nodes (8): TraceEvent, mark_reused(), _event(), _execute(), _save_exploration(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event(), test_a_reused_step_does_not_claim_the_original_calls_duration()

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 44 - "Naming Layer Tests"
Cohesion: 0.19
Nodes (9): _check_budget(), name_directions(), _read_calls(), _record_call(), _timeout(), _write_calls(), test_a_refusal_is_not_charged(), test_the_budget_guard_stops_the_calls() (+1 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (18): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+10 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.17
Nodes (9): validate_directions(), test_a_citation_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_number_qloo_returned_is_allowed(), test_a_number_the_model_invented_is_dropped(), test_a_placeholder_field_is_dropped_but_the_rest_stays(), test_a_placeholder_is_not_used(), test_every_model_in_the_chain_is_free() (+1 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.16
Nodes (14): AudienceComparison, CulturalHeat(), heat(), tile(), PlaceStrip(), ProvenanceDrawer(), BusinessType, Concept (+6 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "post"
Cohesion: 0.15
Nodes (6): compare_audiences(), create_workspace(), investigate_route(), issue_key(), rank_anchors(), recompose_route()

### Community 50 - "main.py"
Cohesion: 0.11
Nodes (12): _demographics(), qloo_audience_demographics(), qloo_entity_tags(), qloo_trends(), qloo_workflows(), render_markdown(), _workflow_response(), audience_demographics_payload() (+4 more)

### Community 51 - "test_api.py"
Cohesion: 0.15
Nodes (3): client(), test_the_compare_endpoint_refuses_without_a_live_provider(), test_validation_errors_are_readable()

### Community 52 - "get_provider"
Cohesion: 0.11
Nodes (11): The shape of the codebase, challenge_directions_route(), compare(), health(), health_alias(), resolve_taste(), CompareRequest, create_provider() (+3 more)

### Community 53 - "Investigation Module"
Cohesion: 0.16
Nodes (9): _bounds(), _call_for(), _geography_points(), investigate(), _now(), _workflow_for(), list_facets(), qloo_where_popular() (+1 more)

### Community 54 - "Project knowledge workflow"
Cohesion: 0.22
Nodes (8): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, Tools

### Community 55 - "Naming Layer Tests"
Cohesion: 0.22
Nodes (5): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing()

### Community 56 - "Evidence Test Module"
Cohesion: 0.08
Nodes (30): challenge_directions(), _compare_with_neighbourhood(), guess_demographic(), _is_cultural_signal(), _tag_family(), _venues(), clamp(), fingerprint() (+22 more)

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 440 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `_execute`, `._name_directions`, `QlooHarnessError`, `Free Naming Layer Tests`, `main.py`, `Evidence Store Tests`, `Investigation Module`, `get_provider`, `Naming Layer Tests`, `Evidence Test Module`, `Provider Internals and Metering`, `ProjectRequest`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_neighbourhood()`) actually correct?**
  _`QlooHarnessProvider` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `QlooHarnessProvider` be split into smaller, more focused modules?**
  _Cohesion score 0.07926829268292683 - nodes in this community are weakly interconnected._
- **Why does `ProjectRequest` connect `ProjectRequest` to `QlooHarnessProvider`, `ResearchRun`, `_execute`, `Free Naming Layer Tests`, `post`, `main.py`, `Evidence Store Tests`, `Workspace and Exploration Routes`, `Investigation Module`, `Naming Layer Tests`, `Evidence Test Module`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `ProjectRequest` (e.g. with `challenge_directions()` and `_challenge_one()`) actually correct?**
  _`ProjectRequest` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.09982174688057041 - nodes in this community are weakly interconnected._