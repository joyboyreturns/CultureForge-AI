# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1253 nodes · 2821 edges · 65 communities (54 shown, 11 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 229 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `84220d16`
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
- fix_mp4_faststart.py
- TypeScript Node Build Settings
- OpenCode Configuration
- Audience and Concept Copy
- Studio Concept Mockups
- Cafe Ritual Mockup Detail
- vault_query.py
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
- pathlib
- main.py
- Platform Layer
- QlooHarnessError
- typing
- EvidenceDependenceMap.tsx
- Cultural Constellation Graph
- llm.py
- Endpoint Verification Tool
- Evidence Presentation
- _ask_model
- get_platform
- Evidence
- main.py
- name_directions
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- check_api.py
- providers.py
- run_agent
- test_api.py
- test_comparison.py
- investigation.py
- QlooHarnessProvider
- backend/__init__.py
- Evidence Test Module
- TraceEvent
- StubProvider
- ResearchRegistry
- reasoning.py
- test_frontier_ai_request_includes_the_pydantic_output_schema
- llm_check.py
- error_response
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
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `start_run()` --uses--> `CompareRequest`  [INFERRED]
  backend/main.py → backend/models.py

## Import Cycles
- None detected.

## Communities (65 total, 11 thin omitted)

### Community 0 - "test_a_failure_is_not_held"
Cohesion: 0.22
Nodes (5): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing()

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

### Community 7 - "fix_mp4_faststart.py"
Cohesion: 0.21
Nodes (11): analyze(), _boxes(), _child(), _find(), is_faststart(), main(), _patch_co64(), _patch_stco() (+3 more)

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

### Community 13 - "vault_query.py"
Cohesion: 0.24
Nodes (11): _build_index(), _code_excerpt(), find_notes(), load_index(), main(), _norm(), _parse_frontmatter(), render_list() (+3 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.21
Nodes (10): ChallengedDirection, ChallengeResult, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge() (+2 more)

### Community 20 - "test_evidence_store.py"
Cohesion: 0.10
Nodes (13): cached_call(), canonical_key(), known_location(), transport_request_count(), start_research(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one() (+5 more)

### Community 21 - "post"
Cohesion: 0.09
Nodes (12): analyze_evidence_route(), challenge_directions_route(), compare(), compare_audiences(), evidence_presentation_route(), investigate_route(), rank_anchors(), recompose_route() (+4 more)

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
Cohesion: 0.18
Nodes (13): challenge_probe(), _primary_anchor(), challenge_probe_route(), ChallengeProbeRequest, ChallengeRevision, FakeProvider, _request(), test_cached_probe_reports_zero_new_requests() (+5 more)

### Community 29 - "pathlib"
Cohesion: 0.18
Nodes (6): entities(), no_model_calls(), recommend_places(), store(), fake(), fake()

### Community 30 - "main.py"
Cohesion: 0.13
Nodes (10): qloo_audience_demographics(), qloo_describe(), qloo_where_popular(), render_markdown(), _workflow_response(), EntityRequest, WherePopularRequest, audience_demographics_payload() (+2 more)

### Community 31 - "Platform Layer"
Cohesion: 0.09
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "QlooHarnessError"
Cohesion: 0.12
Nodes (15): QlooHarnessError, _execute(), ResearchRun, _save_exploration(), _install(), StubProvider, test_a_known_location_is_offered_as_the_way_out(), test_a_provider_failure_is_reported_not_crashed() (+7 more)

### Community 34 - "EvidenceDependenceMap.tsx"
Cohesion: 0.15
Nodes (16): lucide-react, CacheEntry, ResearchRun, Progress(), AgentTrace(), CellState, compareDirection(), compositionKey() (+8 more)

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "llm.py"
Cohesion: 0.19
Nodes (11): _api_key(), _asserts_an_unverified_locality(), budget_state(), _clean_text(), is_configured(), _load_env_once(), _model(), status() (+3 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Evidence Presentation"
Cohesion: 0.14
Nodes (9): excerpt(), group_tags(), is_organisation(), present_evidence(), present_place(), presentation_key(), split_sentences(), tag_bucket() (+1 more)

### Community 40 - "_ask_model"
Cohesion: 0.14
Nodes (11): _ask_model(), _build_user_prompt(), LlmUnavailable, _parse_json(), _post(), test_an_answer_that_is_not_json_is_not_used(), test_gateway_failure_is_not_retried(), fail() (+3 more)

### Community 41 - "get_platform"
Cohesion: 0.14
Nodes (14): create_workspace(), export_exploration(), generate(), issue_key(), list_explorations(), list_keys(), meter_requests(), read_exploration() (+6 more)

### Community 42 - "Evidence"
Cohesion: 0.24
Nodes (5): _challenge_one(), _compare_with_other_places(), _tag_family(), _venues(), Evidence

### Community 43 - "main.py"
Cohesion: 0.13
Nodes (9): health(), health_alias(), list_facets(), qloo_workflows(), read_snapshot(), recent_runs(), run_status(), usage() (+1 more)

### Community 44 - "name_directions"
Cohesion: 0.20
Nodes (10): _check_budget(), name_directions(), _read_calls(), _record_call(), select_source_items(), _timeout(), _write_calls(), test_disabled_gateway_never_attempts_a_naming_call() (+2 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (21): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+13 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.11
Nodes (12): _numbers_are_allowed(), _source_names(), validate_directions(), test_a_citation_is_dropped(), test_a_claim_about_a_locality_qloo_did_not_establish_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_name_that_is_a_qloo_name_may_keep_its_digits(), test_a_number_qloo_returned_somewhere_else_is_still_dropped() (+4 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.13
Nodes (22): react, AnchorRanking, AudienceComparison, AudienceComparisonResult, Investigation, ReplacementProbeResult, AnchorTournament(), Choice (+14 more)

### Community 48 - "check_api.py"
Cohesion: 0.29
Nodes (4): load_qloo_config(), main(), mask(), read_budget_log()

### Community 49 - "providers.py"
Cohesion: 0.07
Nodes (30): _revision_response(), clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), ChallengeRequest (+22 more)

### Community 50 - "run_agent"
Cohesion: 0.16
Nodes (14): _event(), _payload(), _recipe(), run_agent(), _validate_action(), AgentAction, AgentObservation, AgentReport (+6 more)

### Community 51 - "test_api.py"
Cohesion: 0.06
Nodes (20): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The shape of the codebase, The Vercel model layer (+12 more)

### Community 52 - "test_comparison.py"
Cohesion: 0.09
Nodes (13): compare_audiences(), own(), rows(), Delivery, safe_query(), RecomposeProvider, test_a_comparison_needs_both_sides(), test_agent_recomposition_uses_exact_run_envelopes_without_cache_lookup() (+5 more)

### Community 53 - "investigation.py"
Cohesion: 0.26
Nodes (7): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for()

### Community 54 - "QlooHarnessProvider"
Cohesion: 0.06
Nodes (14): _rank_venues(), rank_entities(), recompose(), _without(), get_store(), qloo_entity_tags(), qloo_trends(), count() (+6 more)

### Community 55 - "backend/__init__.py"
Cohesion: 0.32
Nodes (3): _records(), select(), validate()

### Community 56 - "Evidence Test Module"
Cohesion: 0.11
Nodes (20): challenge_directions(), guess_demographic(), _is_cultural_signal(), _concept(), _evidence(), FakeProvider, _response(), test_a_direction_can_be_held_to_a_different_place() (+12 more)

### Community 57 - "TraceEvent"
Cohesion: 0.22
Nodes (7): TraceEvent, mark_reused(), announce(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event(), test_a_reused_step_does_not_claim_the_original_calls_duration(), execute_agent()

### Community 60 - "reasoning.py"
Cohesion: 0.16
Nodes (25): EvidenceAnalysisDirection, EvidenceAnalysisOutput, EvidenceAnalysisRequest, EvidenceAnalysisResult, AnalysisUnavailable, analyze(), _cache_key(), _call() (+17 more)

### Community 63 - "error_response"
Cohesion: 0.22
Nodes (5): error_response(), http_error_handler(), qloo_error_handler(), validation_exception_handler(), ErrorBody

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `autoprefixer`, `motion`, `postcss`, `tailwindcss`, `@types/react` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 499 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `QlooHarnessError`, `test_a_failure_is_not_held`, `Evidence`, `name_directions`, `Free Naming Layer Tests`, `providers.py`, `test_api.py`, `test_comparison.py`, `investigation.py`, `post`, `test_evidence_store.py`, `Evidence Test Module`, `TraceEvent`, `QlooHarnessError`, `main.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `autoprefixer`, `motion`, `postcss` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.07317073170731707 - nodes in this community are weakly interconnected._
- **Why does `Platform` connect `Platform Layer` to `get_platform`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Build Tooling and Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05263157894736842 - nodes in this community are weakly interconnected._