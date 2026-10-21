# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1298 nodes · 2898 edges · 66 communities (56 shown, 10 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 231 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e1954288`
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
- json
- TypeScript Node Build Settings
- OpenCode Configuration
- Audience and Concept Copy
- Studio Concept Mockups
- Cafe Ritual Mockup Detail
- Qloo Provider and Workflow Adapters
- Front Page Metadata
- TypeScript Project References
- Evidence Test Client
- Graphify MCP Wrapper
- test_evidence_store.py
- post
- Evidence Concept Composer
- Studio API Contracts
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Investigation.tsx
- QlooHarnessError
- mock_generator.py
- .run_workflow_cached
- Platform Layer
- TraceEvent
- typing
- EvidenceDependenceMap.tsx
- Cultural Constellation Graph
- Free Model Transport
- Endpoint Verification Tool
- Evidence Presentation
- Free Naming Layer
- get_platform
- Naming Guard and Budget
- main.py
- Workflow Budgets and Direction Naming
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- models.py
- test_agent.py
- test_api.py
- GenerateResponse
- investigation.py
- QlooHarnessProvider
- backend/__init__.py
- Evidence Test Module
- Project knowledge workflow
- rank_entities
- qloo_entity_tags
- reasoning.py
- qloo_where_popular
- compare_audiences
- error_response
- share_exploration
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 77 edges
2. `App()` - 45 edges
3. `ProjectRequest` - 42 edges
4. `QlooHarnessError` - 38 edges
5. `GenerateResponse` - 31 edges
6. `TraceEvent` - 29 edges
7. `_execute()` - 29 edges
8. `run_agent()` - 29 edges
9. `Platform` - 27 edges
10. `canonical_key()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `fake()` --indirect_call--> `recommend_places()`  [INFERRED]
  backend/tests/test_evidence_store.py → backend/tests/conftest.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png

## Import Cycles
- None detected.

## Communities (66 total, 10 thin omitted)

### Community 0 - "test_a_failure_is_not_held"
Cohesion: 0.14
Nodes (8): test_a_repeated_brief_reports_that_it_spent_nothing(), fake(), _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing(), test_without_a_model_the_rules_still_name_the_directions()

### Community 1 - "Studio Application Shell"
Cohesion: 0.07
Nodes (33): BackendStatus, EvidenceAnalysisResult, listExplorations(), SavedExploration, TasteSeed, save(), audiencePresets, BarIcon() (+25 more)

### Community 2 - "Build Tooling and Dependencies"
Cohesion: 0.05
Nodes (37): dependencies, lucide-react, motion, react, react-dom, devDependencies, autoprefixer, postcss (+29 more)

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

### Community 7 - "json"
Cohesion: 0.08
Nodes (26): load_qloo_config(), main(), mask(), read_budget_log(), analyze(), _boxes(), _child(), _find() (+18 more)

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

### Community 13 - "Qloo Provider and Workflow Adapters"
Cohesion: 0.22
Nodes (8): The shape of the codebase, ProjectRequest, create_provider(), CultureProvider, current_provider(), get_provider(), _is_qloo_configured(), MockCultureProvider

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.21
Nodes (10): ChallengedDirection, ChallengeResult, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge() (+2 more)

### Community 20 - "test_evidence_store.py"
Cohesion: 0.11
Nodes (10): cached_call(), known_location(), transport_request_count(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one(), test_entries_expire(), test_evidence_that_was_already_held_costs_nothing() (+2 more)

### Community 21 - "post"
Cohesion: 0.11
Nodes (9): challenge_directions_route(), compare(), compare_audiences(), evidence_presentation_route(), investigate_route(), rank_anchors(), recompose_route(), resolve_taste() (+1 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.09
Nodes (21): compose(), ComposedConcept, _facet_rank(), by_organisation(), _first_sentence(), _is_organisation(), _matches(), _number() (+13 more)

### Community 23 - "Studio API Contracts"
Cohesion: 0.12
Nodes (28): briefKey(), ChallengeCheck, challengeReplacementProbe(), compareAudience(), compareAudiences(), detailMessage(), EvidenceAnalysisDirection, EvidenceSelection (+20 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.08
Nodes (27): react-dom, analyzeEvidence(), challengeDirections(), fetchExploration(), fetchHealth(), fetchSnapshot(), fetchUsage(), rememberLiveResult() (+19 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Investigation.tsx"
Cohesion: 0.25
Nodes (9): investigate(), listFacets(), GeoLayer, GeoMap(), GeoPoint, project(), Investigation(), openFacets() (+1 more)

### Community 28 - "QlooHarnessError"
Cohesion: 0.13
Nodes (16): challenge_probe(), _primary_anchor(), challenge_probe_route(), ChallengeProbeRequest, ChallengeRevision, Evidence, QlooHarnessError, FakeProvider (+8 more)

### Community 29 - "mock_generator.py"
Cohesion: 0.20
Nodes (11): clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), Concept, CulturalSignal (+3 more)

### Community 30 - ".run_workflow_cached"
Cohesion: 0.12
Nodes (8): qloo_audience_demographics(), qloo_describe(), qloo_trends(), _workflow_response(), audience_demographics_payload(), describe_payload(), trends_payload(), test_the_provider_reports_zero_for_a_cached_workflow()

### Community 31 - "Platform Layer"
Cohesion: 0.10
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "TraceEvent"
Cohesion: 0.05
Nodes (31): AgentReport, TraceEvent, mark_reused(), safe_query(), _event(), _execute(), announce(), ResearchRegistry (+23 more)

### Community 33 - "typing"
Cohesion: 0.20
Nodes (3): meter_requests(), begin(), total()

### Community 34 - "EvidenceDependenceMap.tsx"
Cohesion: 0.15
Nodes (16): lucide-react, CacheEntry, ResearchRun, Progress(), AgentTrace(), CellState, compareDirection(), compositionKey() (+8 more)

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "Free Model Transport"
Cohesion: 0.11
Nodes (10): _api_key(), _asserts_an_unverified_locality(), _clean_text(), is_configured(), _load_env_once(), _numbers_are_allowed(), _post(), _source_names() (+2 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Evidence Presentation"
Cohesion: 0.14
Nodes (9): excerpt(), group_tags(), is_organisation(), present_evidence(), present_place(), presentation_key(), split_sentences(), tag_bucket() (+1 more)

### Community 40 - "Free Naming Layer"
Cohesion: 0.14
Nodes (10): _ask_model(), _build_user_prompt(), LlmUnavailable, test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post(), test_the_model_is_never_shown_a_number() (+2 more)

### Community 41 - "get_platform"
Cohesion: 0.17
Nodes (12): create_workspace(), export_exploration(), generate(), issue_key(), list_explorations(), list_keys(), read_exploration(), _require_operator() (+4 more)

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 43 - "main.py"
Cohesion: 0.12
Nodes (10): health(), health_alias(), list_facets(), qloo_workflows(), read_snapshot(), recent_runs(), render_markdown(), run_status() (+2 more)

### Community 44 - "Workflow Budgets and Direction Naming"
Cohesion: 0.17
Nodes (8): _check_budget(), name_directions(), _read_calls(), _record_call(), _write_calls(), test_a_refusal_is_not_charged(), test_the_budget_guard_stops_the_calls(), test_without_a_key_nothing_is_attempted()

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (21): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+13 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.11
Nodes (14): _parse_json(), validate_directions(), test_a_citation_is_dropped(), test_a_claim_about_a_locality_qloo_did_not_establish_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_name_that_is_a_qloo_name_may_keep_its_digits(), test_a_number_qloo_returned_somewhere_else_is_still_dropped(), test_a_number_the_model_invented_is_dropped() (+6 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.13
Nodes (22): react, AnchorRanking, AudienceComparison, AudienceComparisonResult, Investigation, ReplacementProbeResult, AnchorTournament(), Choice (+14 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "models.py"
Cohesion: 0.10
Nodes (13): AgentObservation, ChallengeRequest, CompareAudiencesRequest, EntityListRequest, EntityRequest, ErrorResponse, EvidencePresentationRequest, EvidenceVerdictInput (+5 more)

### Community 50 - "test_agent.py"
Cohesion: 0.21
Nodes (6): AgentAction, reflection(), test_agent_disabled_preserves_rules_result_without_model_call(), test_agent_executes_one_valid_removal_from_this_runs_exact_evidence(), test_agent_rejects_fabricated_tool_ids_without_execution(), test_frontier_ai_request_includes_the_pydantic_output_schema()

### Community 51 - "test_api.py"
Cohesion: 0.09
Nodes (10): _challenge_probe_body(), client(), test_a_key_cannot_be_revoked_from_another_workspace(), test_a_malformed_workflow_body_is_a_readable_422(), test_a_valid_request_answers_with_the_contract(), test_challenge_probe_route_refuses_sample_provider(), test_challenge_probe_route_rejects_malformed_or_unknown_fields(), test_challenge_probe_route_returns_probe_result_without_live_call() (+2 more)

### Community 52 - "GenerateResponse"
Cohesion: 0.18
Nodes (7): _revision_response(), Delivery, GenerateResponse, ProvenanceMetadata, response(), RecomposeProvider, test_agent_recomposition_uses_exact_run_envelopes_without_cache_lookup()

### Community 53 - "investigation.py"
Cohesion: 0.23
Nodes (7): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for()

### Community 55 - "backend/__init__.py"
Cohesion: 0.21
Nodes (5): select_source_items(), _timeout(), _records(), select(), validate()

### Community 56 - "Evidence Test Module"
Cohesion: 0.08
Nodes (24): challenge_directions(), _challenge_one(), _compare_with_other_places(), guess_demographic(), _is_cultural_signal(), _tag_family(), _venues(), _concept() (+16 more)

### Community 57 - "Project knowledge workflow"
Cohesion: 0.22
Nodes (8): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, Tools

### Community 58 - "rank_entities"
Cohesion: 0.25
Nodes (3): _rank_venues(), rank_entities(), _without()

### Community 60 - "reasoning.py"
Cohesion: 0.06
Nodes (42): _event(), _payload(), _recipe(), run_agent(), _validate_action(), recompose(), canonical_key(), get_store() (+34 more)

### Community 62 - "compare_audiences"
Cohesion: 0.29
Nodes (4): compare_audiences(), own(), rows(), test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it()

### Community 63 - "error_response"
Cohesion: 0.22
Nodes (5): error_response(), http_error_handler(), qloo_error_handler(), validation_exception_handler(), ErrorBody

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `autoprefixer`, `motion`, `postcss`, `tailwindcss`, `@types/react` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 526 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `test_a_failure_is_not_held`, `Qloo Provider and Workflow Adapters`, `test_evidence_store.py`, `post`, `QlooHarnessError`, `mock_generator.py`, `.run_workflow_cached`, `TraceEvent`, `main.py`, `Workflow Budgets and Direction Naming`, `Free Naming Layer Tests`, `test_api.py`, `GenerateResponse`, `investigation.py`, `Evidence Test Module`, `rank_entities`, `qloo_entity_tags`, `reasoning.py`, `qloo_where_popular`, `compare_audiences`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `autoprefixer`, `motion`, `postcss` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_a_failure_is_not_held` be split into smaller, more focused modules?**
  _Cohesion score 0.1437908496732026 - nodes in this community are weakly interconnected._
- **Why does `Platform` connect `Platform Layer` to `get_platform`, `reasoning.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.07317073170731707 - nodes in this community are weakly interconnected._