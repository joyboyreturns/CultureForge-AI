# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- 62 files · ~89,506 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .css 4, (none) 2, .example 1)

## Summary
- 1070 nodes · 2218 edges · 62 communities (54 shown, 8 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 167 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e720728e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .generate
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
- QlooHarnessProvider
- Request Metering
- models.py
- Platform Layer
- ResearchRun
- API Error Handling
- Build Tooling and Entry Points
- Cultural Constellation Graph
- Free Model Transport
- Endpoint Verification Tool
- platform.py
- Free Naming Layer
- Evidence Test Wiring
- Naming Guard and Budget
- name_directions
- _check_budget
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- Comparison Tests
- ProjectRequest
- test_api.py
- providers.py
- Investigation Module
- GenerateResponse
- conftest.py
- test_challenge.py
- compare_audiences
- QlooHarnessError
- ResearchRegistry
- _build_user_prompt
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 70 edges
2. `App()` - 40 edges
3. `ProjectRequest` - 34 edges
4. `QlooHarnessError` - 29 edges
5. `Platform` - 27 edges
6. `_execute()` - 24 edges
7. `TraceEvent` - 22 edges
8. `EvidenceStore` - 21 edges
9. `ResearchRun` - 20 edges
10. `challenge_directions()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `_rank_venues()` --uses--> `QlooHarnessProvider`  [INFERRED]
  backend/challenge.py → backend/providers.py

## Import Cycles
- None detected.

## Communities (62 total, 8 thin omitted)

### Community 0 - ".generate"
Cohesion: 0.11
Nodes (6): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing(), test_without_a_model_the_rules_still_name_the_directions()

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
Cohesion: 0.11
Nodes (22): analyze(), _boxes(), _child(), _find(), is_faststart(), main(), _patch_co64(), _patch_stco() (+14 more)

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
Cohesion: 0.11
Nodes (9): TraceEvent, safe_query(), StubProvider, test_the_allowlist_covers_every_query_key_the_app_sends(), test_the_provenance_allowlist_drops_everything_it_does_not_know(), test_the_rank_workflow_is_asked_without_a_limit(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event() (+1 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.21
Nodes (10): ChallengedDirection, ChallengeResult, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge() (+2 more)

### Community 20 - "Evidence Store Tests"
Cohesion: 0.12
Nodes (10): canonical_key(), transport_request_count(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one(), test_entries_expire(), test_evidence_that_was_already_held_costs_nothing(), test_the_provider_reports_zero_for_a_cached_workflow() (+2 more)

### Community 21 - "Workspace and Exploration Routes"
Cohesion: 0.10
Nodes (20): export_exploration(), generate(), health(), health_alias(), list_explorations(), list_keys(), meter_requests(), qloo_workflows() (+12 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.12
Nodes (16): compose(), ComposedConcept, _facet_rank(), _first_sentence(), _matches(), _number(), Recipe, _tag_name() (+8 more)

### Community 23 - "Studio API Contracts"
Cohesion: 0.16
Nodes (22): briefKey(), CacheEntry, ChallengeCheck, compareAudience(), compareAudiences(), detailMessage(), generateConcepts(), GeoPoint (+14 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.10
Nodes (23): challengeDirections(), fetchExploration(), fetchHealth(), fetchSnapshot(), fetchUsage(), rememberLiveResult(), resolveTaste(), shareExploration() (+15 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Frontend Investigation Client"
Cohesion: 0.22
Nodes (11): Facet, Investigation, listFacets(), GeoLayer, GeoMap(), GeoPoint, project(), Investigation() (+3 more)

### Community 28 - "QlooHarnessProvider"
Cohesion: 0.08
Nodes (12): rank_entities(), qloo_audience_demographics(), qloo_describe(), qloo_entity_tags(), qloo_trends(), _workflow_response(), audience_demographics_payload(), describe_payload() (+4 more)

### Community 29 - "Request Metering"
Cohesion: 0.22
Nodes (3): begin(), count(), total()

### Community 30 - "models.py"
Cohesion: 0.15
Nodes (8): ChallengeRequest, CompareAudiencesRequest, Decision, Delivery, ErrorResponse, RankRequest, RecomposeRequest, ShareRequest

### Community 31 - "Platform Layer"
Cohesion: 0.10
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "ResearchRun"
Cohesion: 0.23
Nodes (8): _install(), StubProvider, test_a_known_location_is_offered_as_the_way_out(), test_needs_input_becomes_a_clarification(), test_no_local_evidence_becomes_a_clarification(), test_no_resolved_tags_becomes_a_clarification(), test_the_run_records_real_trace_events(), test_the_run_stops_at_its_allowance()

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
Cohesion: 0.15
Nodes (7): _allowed_numbers(), _api_key(), _clean_text(), _load_env_once(), _numbers_are_allowed(), _post(), _word_count()

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "platform.py"
Cohesion: 0.13
Nodes (5): load_qloo_config(), main(), mask(), read_budget_log(), _load_env()

### Community 40 - "Free Naming Layer"
Cohesion: 0.13
Nodes (11): _ask_model(), LlmUnavailable, _parse_json(), test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post(), test_an_answer_that_is_not_json_is_not_used() (+3 more)

### Community 41 - "Evidence Test Wiring"
Cohesion: 0.22
Nodes (6): mark_reused(), _event(), _execute(), ResearchRun, _save_exploration(), start_research()

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 43 - "name_directions"
Cohesion: 0.22
Nodes (5): is_configured(), name_directions(), _timeout(), test_the_suite_never_reaches_the_model(), test_without_a_key_nothing_is_attempted()

### Community 44 - "_check_budget"
Cohesion: 0.27
Nodes (6): _check_budget(), _read_calls(), _record_call(), _write_calls(), test_a_refusal_is_not_charged(), test_the_budget_guard_stops_the_calls()

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (18): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+10 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.17
Nodes (9): validate_directions(), test_a_citation_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_number_qloo_returned_is_allowed(), test_a_number_the_model_invented_is_dropped(), test_a_placeholder_field_is_dropped_but_the_rest_stays(), test_a_placeholder_is_not_used(), test_every_model_in_the_chain_is_free() (+1 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.12
Nodes (21): AnchorRanking, AudienceComparison, AudienceComparisonResult, AnchorTournament(), Choice, CHOICES, guessDemographic(), CulturalHeat() (+13 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "Comparison Tests"
Cohesion: 0.10
Nodes (11): challenge_directions_route(), compare(), compare_audiences(), create_workspace(), investigate_route(), issue_key(), rank_anchors(), recompose_route() (+3 more)

### Community 50 - "ProjectRequest"
Cohesion: 0.15
Nodes (12): challenge_directions(), _challenge_one(), _compare_with_neighbourhood(), guess_demographic(), _is_cultural_signal(), _rank_venues(), _tag_family(), _venues() (+4 more)

### Community 51 - "test_api.py"
Cohesion: 0.08
Nodes (14): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, The shape of the codebase (+6 more)

### Community 52 - "providers.py"
Cohesion: 0.15
Nodes (8): recompose(), cached_call(), get_store(), known_location(), create_provider(), CultureProvider, current_provider(), _is_qloo_configured()

### Community 53 - "Investigation Module"
Cohesion: 0.18
Nodes (9): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for(), list_facets() (+1 more)

### Community 54 - "GenerateResponse"
Cohesion: 0.20
Nodes (11): clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), Concept, CulturalSignal (+3 more)

### Community 55 - "conftest.py"
Cohesion: 0.15
Nodes (7): entities(), no_model_calls(), recommend_places(), store(), test_a_repeated_brief_reports_that_it_spent_nothing(), fake(), fake()

### Community 56 - "test_challenge.py"
Cohesion: 0.18
Nodes (11): _concept(), _evidence(), FakeProvider, _response(), test_a_direction_can_be_held_to_a_different_place(), test_a_direction_with_only_type_tags_is_unproven(), test_the_coverage_is_disclosed(), test_the_profile_that_was_ranked_is_reported() (+3 more)

### Community 57 - "compare_audiences"
Cohesion: 0.22
Nodes (6): compare_audiences(), own(), rows(), test_a_comparison_needs_both_sides(), test_the_shared_tags_carry_the_score_and_the_hit_counts(), test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it()

### Community 58 - "QlooHarnessError"
Cohesion: 0.33
Nodes (3): QlooHarnessError, test_a_provider_failure_is_reported_not_crashed(), run_workflow_cached()

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 441 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `.generate`, `Evidence Test Wiring`, `name_directions`, `QlooHarnessError`, `Free Naming Layer Tests`, `Comparison Tests`, `ProjectRequest`, `providers.py`, `Workspace and Exploration Routes`, `Investigation Module`, `GenerateResponse`, `Evidence Store Tests`, `compare_audiences`, `conftest.py`, `models.py`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_neighbourhood()`) actually correct?**
  _`QlooHarnessProvider` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.generate` be split into smaller, more focused modules?**
  _Cohesion score 0.11067193675889328 - nodes in this community are weakly interconnected._
- **Why does `ProjectRequest` connect `ProjectRequest` to `.generate`, `ResearchRun`, `Evidence Test Wiring`, `Free Naming Layer Tests`, `Comparison Tests`, `test_api.py`, `providers.py`, `Workspace and Exploration Routes`, `Investigation Module`, `GenerateResponse`, `test_challenge.py`, `Evidence Store Tests`, `conftest.py`, `QlooHarnessProvider`, `models.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.09982174688057041 - nodes in this community are weakly interconnected._