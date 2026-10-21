# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- 64 files · ~99,563 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .css 4, (none) 2, .example 1)

## Summary
- 1171 nodes · 2453 edges · 61 communities (51 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 182 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5c3cb61d`
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
- _execute
- Front Page Metadata
- TypeScript Project References
- Evidence Test Client
- Graphify MCP Wrapper
- Evidence Store Tests
- main.py
- Evidence Concept Composer
- Studio API Contracts
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Frontend Investigation Client
- challenge_directions
- selector.py
- models.py
- Platform Layer
- _execute
- API Error Handling
- Build Tooling and Entry Points
- Cultural Constellation Graph
- Free Model Transport
- Endpoint Verification Tool
- presentation.py
- Free Naming Layer
- get_platform
- Naming Guard and Budget
- Provider and Comparison Internals
- name_directions
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- CompareRequest
- QlooHarnessProvider
- ProjectRequest
- CompareAudiencesRequest
- providers.py
- health
- TrendsRequest
- Evidence Test Module
- QlooHarnessError
- _build_user_prompt
- challenge_directions_route
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 71 edges
2. `App()` - 42 edges
3. `ProjectRequest` - 35 edges
4. `QlooHarnessError` - 29 edges
5. `Platform` - 27 edges
6. `_execute()` - 24 edges
7. `GenerateResponse` - 23 edges
8. `challenge_directions()` - 22 edges
9. `TraceEvent` - 22 edges
10. `canonical_key()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `fake()` --indirect_call--> `recommend_places()`  [INFERRED]
  backend/tests/test_evidence_store.py → backend/tests/conftest.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png

## Import Cycles
- None detected.

## Communities (61 total, 10 thin omitted)

### Community 0 - ".generate"
Cohesion: 0.08
Nodes (10): is_configured(), count(), test_a_repeated_brief_reports_that_it_spent_nothing(), fake(), _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name() (+2 more)

### Community 1 - "Studio Application Shell"
Cohesion: 0.09
Nodes (30): listExplorations(), TasteSeed, save(), audiencePresets, BarIcon(), BusinessIcon(), Button(), Compare() (+22 more)

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
Nodes (32): entities(), no_model_calls(), recommend_places(), store(), fake(), load_qloo_config(), main(), mask() (+24 more)

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

### Community 13 - "_execute"
Cohesion: 0.17
Nodes (9): TraceEvent, mark_reused(), _event(), _execute(), _save_exploration(), start_research(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event() (+1 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.21
Nodes (10): ChallengedDirection, ChallengeResult, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge() (+2 more)

### Community 20 - "Evidence Store Tests"
Cohesion: 0.11
Nodes (13): cached_call(), canonical_key(), get_store(), known_location(), transport_request_count(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one() (+5 more)

### Community 21 - "main.py"
Cohesion: 0.08
Nodes (16): _demographics(), evidence_presentation_route(), qloo_audience_demographics(), qloo_describe(), qloo_entity_tags(), qloo_trends(), qloo_workflows(), rank_anchors() (+8 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.08
Nodes (22): compose(), ComposedConcept, _facet_rank(), by_organisation(), _first_sentence(), _is_organisation(), _matches(), _number() (+14 more)

### Community 23 - "Studio API Contracts"
Cohesion: 0.13
Nodes (26): BackendStatus, briefKey(), CacheEntry, ChallengeCheck, compareAudience(), compareAudiences(), detailMessage(), EvidenceSelection (+18 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.10
Nodes (23): challengeDirections(), fetchExploration(), fetchHealth(), fetchSnapshot(), fetchUsage(), rememberLiveResult(), resolveTaste(), shareExploration() (+15 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Frontend Investigation Client"
Cohesion: 0.22
Nodes (12): Facet, investigate(), Investigation, listFacets(), GeoLayer, GeoMap(), GeoPoint, project() (+4 more)

### Community 28 - "challenge_directions"
Cohesion: 0.13
Nodes (11): challenge_directions(), _challenge_one(), _compare_with_other_places(), guess_demographic(), _is_cultural_signal(), _tag_family(), _venues(), Evidence (+3 more)

### Community 29 - "selector.py"
Cohesion: 0.28
Nodes (3): _records(), select(), validate()

### Community 30 - "models.py"
Cohesion: 0.08
Nodes (23): clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), ChallengeRevision, Concept (+15 more)

### Community 31 - "Platform Layer"
Cohesion: 0.09
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "_execute"
Cohesion: 0.13
Nodes (11): ResearchRegistry, ResearchRun, _install(), StubProvider, test_a_known_location_is_offered_as_the_way_out(), test_a_provider_failure_is_reported_not_crashed(), test_needs_input_becomes_a_clarification(), test_no_local_evidence_becomes_a_clarification() (+3 more)

### Community 33 - "API Error Handling"
Cohesion: 0.24
Nodes (4): error_response(), http_error_handler(), qloo_error_handler(), validation_exception_handler()

### Community 34 - "Build Tooling and Entry Points"
Cohesion: 0.18
Nodes (6): lucide-react, react, react-dom, fetchResearchRun(), AgentTrace(), poll()

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "Free Model Transport"
Cohesion: 0.13
Nodes (8): _api_key(), _asserts_an_unverified_locality(), _clean_text(), _load_env_once(), _numbers_are_allowed(), _post(), _source_names(), _word_count()

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "presentation.py"
Cohesion: 0.14
Nodes (9): excerpt(), group_tags(), is_organisation(), present_evidence(), present_place(), presentation_key(), split_sentences(), tag_bucket() (+1 more)

### Community 40 - "Free Naming Layer"
Cohesion: 0.13
Nodes (11): _ask_model(), LlmUnavailable, _parse_json(), test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post(), test_an_answer_that_is_not_json_is_not_used() (+3 more)

### Community 41 - "get_platform"
Cohesion: 0.12
Nodes (19): create_workspace(), export_exploration(), generate(), issue_key(), list_explorations(), list_keys(), meter_requests(), read_exploration() (+11 more)

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 43 - "Provider and Comparison Internals"
Cohesion: 0.20
Nodes (9): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, The shape of the codebase (+1 more)

### Community 44 - "name_directions"
Cohesion: 0.17
Nodes (10): _check_budget(), name_directions(), _read_calls(), _record_call(), select_source_items(), _timeout(), _write_calls(), test_a_refusal_is_not_charged() (+2 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (21): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+13 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.11
Nodes (12): validate_directions(), test_a_citation_is_dropped(), test_a_claim_about_a_locality_qloo_did_not_establish_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_name_that_is_a_qloo_name_may_keep_its_digits(), test_a_number_qloo_returned_somewhere_else_is_still_dropped(), test_a_number_the_model_invented_is_dropped(), test_a_placeholder_field_is_dropped_but_the_rest_stays() (+4 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.13
Nodes (19): AnchorRanking, AudienceComparison, AudienceComparisonResult, AnchorTournament(), Choice, CHOICES, guessDemographic(), PlaceStrip() (+11 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "CompareRequest"
Cohesion: 0.33
Nodes (3): compare(), resolve_taste(), CompareRequest

### Community 50 - "QlooHarnessProvider"
Cohesion: 0.08
Nodes (6): _rank_venues(), rank_entities(), recompose(), _without(), QlooHarnessProvider, test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it()

### Community 51 - "ProjectRequest"
Cohesion: 0.09
Nodes (10): GenerateResponse, ProjectRequest, CultureProvider, MockCultureProvider, client(), test_a_key_cannot_be_revoked_from_another_workspace(), test_a_malformed_workflow_body_is_a_readable_422(), test_a_valid_request_answers_with_the_contract() (+2 more)

### Community 53 - "providers.py"
Cohesion: 0.08
Nodes (16): _bounds(), _call_for(), _geography_points(), investigate(), _now(), _workflow_for(), investigate_route(), list_facets() (+8 more)

### Community 56 - "Evidence Test Module"
Cohesion: 0.15
Nodes (14): _concept(), _evidence(), FakeProvider, _response(), test_a_direction_can_be_held_to_a_different_place(), test_a_direction_with_only_type_tags_is_unproven(), test_a_re_anchored_direction_is_labelled_as_a_counterfactual(), test_a_tag_returned_for_both_sides_is_never_called_exclusive() (+6 more)

### Community 57 - "QlooHarnessError"
Cohesion: 0.08
Nodes (13): compare_audiences(), own(), rows(), QlooHarnessError, safe_query(), StubProvider, test_a_comparison_needs_both_sides(), test_removing_a_venue_rebuilds_the_directions_without_it() (+5 more)

### Community 60 - "challenge_directions_route"
Cohesion: 0.40
Nodes (3): challenge_directions_route(), _revision_response(), ChallengeRequest

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 490 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `.generate`, `_execute`, `challenge_directions_route`, `Free Naming Layer Tests`, `CompareRequest`, `ProjectRequest`, `Evidence Store Tests`, `main.py`, `providers.py`, `QlooHarnessError`, `challenge_directions`, `models.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 24 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.generate` be split into smaller, more focused modules?**
  _Cohesion score 0.07956989247311828 - nodes in this community are weakly interconnected._
- **Why does `ProjectRequest` connect `ProjectRequest` to `.generate`, `_execute`, `get_platform`, `_execute`, `Free Naming Layer Tests`, `QlooHarnessProvider`, `Evidence Store Tests`, `main.py`, `providers.py`, `Evidence Test Module`, `QlooHarnessError`, `challenge_directions`, `models.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.09309309309309309 - nodes in this community are weakly interconnected._