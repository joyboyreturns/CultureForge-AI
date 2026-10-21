# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- 64 files · ~98,062 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .css 4, (none) 2, .example 1)

## Summary
- 1144 nodes · 2393 edges · 62 communities (52 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 177 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5526e9a0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_a_failure_is_not_held
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
- main.py
- Evidence Concept Composer
- Studio API Contracts
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Frontend Investigation Client
- .run_workflow_cached
- Request Metering
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
- Project knowledge workflow
- name_directions
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- post
- recompose
- test_api.py
- providers.py
- Investigation Module
- mock_generator.py
- QlooHarnessProvider
- test_challenge.py
- QlooHarnessError
- ProvenanceMetadata
- qloo_audience_demographics
- challenge_directions_route
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 71 edges
2. `App()` - 42 edges
3. `ProjectRequest` - 36 edges
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
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `_rank_venues()` --uses--> `Evidence`  [INFERRED]
  backend/challenge.py → backend/models.py

## Import Cycles
- None detected.

## Communities (62 total, 10 thin omitted)

### Community 0 - "test_a_failure_is_not_held"
Cohesion: 0.22
Nodes (5): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing()

### Community 1 - "Studio Application Shell"
Cohesion: 0.13
Nodes (25): listExplorations(), save(), audiencePresets, BarIcon(), BusinessIcon(), Button(), Compare(), Create() (+17 more)

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
Cohesion: 0.12
Nodes (7): TraceEvent, mark_reused(), StubProvider, test_the_rank_workflow_is_asked_without_a_limit(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event(), test_a_reused_step_does_not_claim_the_original_calls_duration()

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
Cohesion: 0.12
Nodes (12): health(), health_alias(), list_facets(), list_keys(), qloo_workflows(), read_snapshot(), recent_runs(), render_markdown() (+4 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.09
Nodes (21): compose(), ComposedConcept, _facet_rank(), by_organisation(), _first_sentence(), _is_organisation(), _matches(), _number() (+13 more)

### Community 23 - "Studio API Contracts"
Cohesion: 0.12
Nodes (27): BackendStatus, briefKey(), CacheEntry, ChallengeCheck, compareAudience(), compareAudiences(), detailMessage(), EvidenceSelection (+19 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.10
Nodes (24): challengeDirections(), fetchExploration(), fetchHealth(), fetchSnapshot(), fetchUsage(), rememberLiveResult(), resolveTaste(), shareExploration() (+16 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Frontend Investigation Client"
Cohesion: 0.22
Nodes (12): Facet, investigate(), Investigation, listFacets(), GeoLayer, GeoMap(), GeoPoint, project() (+4 more)

### Community 28 - ".run_workflow_cached"
Cohesion: 0.12
Nodes (8): qloo_describe(), qloo_entity_tags(), qloo_trends(), _workflow_response(), count(), describe_payload(), entity_tags_payload(), trends_payload()

### Community 30 - "models.py"
Cohesion: 0.12
Nodes (12): ChallengeRequest, ChallengeRevision, CompareAudiencesRequest, Concept, Decision, ErrorBody, ErrorResponse, EvidencePresentationRequest (+4 more)

### Community 31 - "Platform Layer"
Cohesion: 0.09
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "_execute"
Cohesion: 0.10
Nodes (16): _event(), _execute(), ResearchRegistry, ResearchRun, _save_exploration(), start_research(), _install(), StubProvider (+8 more)

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
Cohesion: 0.12
Nodes (9): _api_key(), _build_user_prompt(), _clean_text(), _load_env_once(), _numbers_are_allowed(), _post(), _source_names(), _word_count() (+1 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "presentation.py"
Cohesion: 0.10
Nodes (12): excerpt(), group_tags(), is_organisation(), present_evidence(), present_place(), presentation_key(), split_sentences(), tag_bucket() (+4 more)

### Community 40 - "Free Naming Layer"
Cohesion: 0.13
Nodes (11): _ask_model(), LlmUnavailable, _parse_json(), test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post(), test_an_answer_that_is_not_json_is_not_used() (+3 more)

### Community 41 - "get_platform"
Cohesion: 0.19
Nodes (10): export_exploration(), generate(), list_explorations(), meter_requests(), read_exploration(), resolve_workspace(), revoke_key(), share_exploration() (+2 more)

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 43 - "Project knowledge workflow"
Cohesion: 0.22
Nodes (8): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, Tools

### Community 44 - "name_directions"
Cohesion: 0.14
Nodes (12): _check_budget(), is_configured(), name_directions(), _read_calls(), _record_call(), select_source_items(), _timeout(), _write_calls() (+4 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (18): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+10 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.14
Nodes (10): validate_directions(), test_a_citation_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_name_that_is_a_qloo_name_may_keep_its_digits(), test_a_number_qloo_returned_somewhere_else_is_still_dropped(), test_a_number_the_model_invented_is_dropped(), test_a_placeholder_field_is_dropped_but_the_rest_stays(), test_a_placeholder_is_not_used() (+2 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.11
Nodes (22): AnchorRanking, AudienceComparison, AudienceComparisonResult, AnchorTournament(), Choice, CHOICES, guessDemographic(), CulturalHeat() (+14 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "post"
Cohesion: 0.10
Nodes (10): compare(), compare_audiences(), create_workspace(), evidence_presentation_route(), investigate_route(), issue_key(), rank_anchors(), recompose_route() (+2 more)

### Community 50 - "recompose"
Cohesion: 0.18
Nodes (5): _rank_venues(), rank_entities(), recompose(), _without(), test_removing_a_venue_rebuilds_the_directions_without_it()

### Community 51 - "test_api.py"
Cohesion: 0.15
Nodes (3): client(), test_the_compare_endpoint_refuses_without_a_live_provider(), test_validation_errors_are_readable()

### Community 52 - "providers.py"
Cohesion: 0.20
Nodes (10): The shape of the codebase, GenerateResponse, ProjectRequest, create_provider(), CultureProvider, current_provider(), get_provider(), _is_qloo_configured() (+2 more)

### Community 53 - "Investigation Module"
Cohesion: 0.16
Nodes (9): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for(), qloo_where_popular() (+1 more)

### Community 54 - "mock_generator.py"
Cohesion: 0.42
Nodes (7): clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), CulturalSignal

### Community 55 - "QlooHarnessProvider"
Cohesion: 0.11
Nodes (4): Delivery, QlooHarnessProvider, test_a_repeated_brief_reports_that_it_spent_nothing(), test_without_a_model_the_rules_still_name_the_directions()

### Community 56 - "test_challenge.py"
Cohesion: 0.08
Nodes (25): challenge_directions(), _challenge_one(), _compare_with_other_places(), guess_demographic(), _is_cultural_signal(), _tag_family(), _venues(), Evidence (+17 more)

### Community 57 - "QlooHarnessError"
Cohesion: 0.12
Nodes (10): compare_audiences(), own(), rows(), QlooHarnessError, safe_query(), test_a_comparison_needs_both_sides(), test_the_allowlist_covers_every_query_key_the_app_sends(), test_the_provenance_allowlist_drops_everything_it_does_not_know() (+2 more)

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 478 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `_execute`, `test_a_failure_is_not_held`, `.run_workflow_cached`, `QlooHarnessError`, `Free Naming Layer Tests`, `post`, `recompose`, `providers.py`, `main.py`, `Investigation Module`, `mock_generator.py`, `test_challenge.py`, `QlooHarnessError`, `ProvenanceMetadata`, `qloo_audience_demographics`, `challenge_directions_route`, `Evidence Store Tests`, `models.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 24 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._
- **Why does `EvidenceStore` connect `Durable Evidence Store` to `Evidence Store Tests`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Build Tooling and Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05263157894736842 - nodes in this community are weakly interconnected._