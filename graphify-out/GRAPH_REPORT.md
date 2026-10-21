# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- 65 files · ~100,984 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .css 4, (none) 2, .example 1)

## Summary
- 1182 nodes · 2473 edges · 58 communities (50 shown, 8 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 184 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c7602070`
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
- providers.py
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
- Frontend Investigation Client
- Evidence Challenge Logic
- TraceEvent
- Typed Request Models
- Platform Layer
- Research Run Orchestration
- cached_call
- EvidenceDependenceMap.tsx
- Cultural Constellation Graph
- Free Model Transport
- Endpoint Verification Tool
- Evidence Presentation
- Free Naming Layer
- Evidence Test Wiring
- Naming Guard and Budget
- StubProvider
- Workflow Budgets and Direction Naming
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- QlooHarnessProvider
- AnchorTournament.tsx
- Platform Security Tests
- .run_workflow_cached
- Qloo Request Metering
- Evidence Test Module
- Challenge API Routes
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 71 edges
2. `App()` - 43 edges
3. `ProjectRequest` - 35 edges
4. `QlooHarnessError` - 29 edges
5. `Platform` - 27 edges
6. `_execute()` - 26 edges
7. `TraceEvent` - 23 edges
8. `GenerateResponse` - 23 edges
9. `challenge_directions()` - 22 edges
10. `canonical_key()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `_rank_venues()` --uses--> `Evidence`  [INFERRED]
  backend/challenge.py → backend/models.py

## Import Cycles
- None detected.

## Communities (58 total, 8 thin omitted)

### Community 0 - "test_a_failure_is_not_held"
Cohesion: 0.22
Nodes (5): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing()

### Community 1 - "Studio Application Shell"
Cohesion: 0.09
Nodes (26): listExplorations(), save(), audiencePresets, BarIcon(), Button(), Compare(), ConceptModal(), Create() (+18 more)

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

### Community 7 - "Media Remuxing Utility"
Cohesion: 0.05
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

### Community 13 - "providers.py"
Cohesion: 0.14
Nodes (8): qloo_workflows(), present_evidence(), capabilities(), create_provider(), CultureProvider, current_provider(), get_provider(), _is_qloo_configured()

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.27
Nodes (9): ChallengedDirection, ChallengeResult, Verdict, ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge(), VerdictStep (+1 more)

### Community 20 - "test_evidence_store.py"
Cohesion: 0.17
Nodes (7): canonical_key(), known_location(), test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_entries_expire(), test_the_store_knows_where_it_already_has_places()

### Community 21 - "post"
Cohesion: 0.10
Nodes (9): get_store(), challenge_directions_route(), compare(), compare_audiences(), evidence_presentation_route(), investigate_route(), rank_anchors(), recompose_route() (+1 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.07
Nodes (23): compose(), ComposedConcept, _facet_rank(), by_organisation(), _first_sentence(), _is_organisation(), _matches(), _number() (+15 more)

### Community 23 - "Studio API Contracts"
Cohesion: 0.12
Nodes (24): BackendStatus, briefKey(), CacheEntry, ChallengeCheck, compareAudience(), compareAudiences(), detailMessage(), EvidenceSelection (+16 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.10
Nodes (26): challengeDirections(), fetchExploration(), fetchHealth(), fetchSnapshot(), fetchUsage(), postJson(), rememberLiveResult(), resolveTaste() (+18 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Frontend Investigation Client"
Cohesion: 0.22
Nodes (12): Facet, investigate(), Investigation, listFacets(), GeoLayer, GeoMap(), GeoPoint, project() (+4 more)

### Community 28 - "Evidence Challenge Logic"
Cohesion: 0.20
Nodes (7): _challenge_one(), _compare_with_other_places(), _is_cultural_signal(), _tag_family(), _venues(), Evidence, test_a_signal_family_is_cultural_and_a_type_family_is_not()

### Community 29 - "TraceEvent"
Cohesion: 0.18
Nodes (6): TraceEvent, mark_reused(), _event(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event(), test_a_reused_step_does_not_claim_the_original_calls_duration()

### Community 30 - "Typed Request Models"
Cohesion: 0.07
Nodes (19): ChallengeRequest, ChallengeRevision, CompareAudiencesRequest, CompareRequest, Concept, Decision, Delivery, EntityListRequest (+11 more)

### Community 31 - "Platform Layer"
Cohesion: 0.10
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "Research Run Orchestration"
Cohesion: 0.10
Nodes (15): _execute(), announce(), ResearchRegistry, ResearchRun, _save_exploration(), start_research(), _install(), StubProvider (+7 more)

### Community 33 - "cached_call"
Cohesion: 0.18
Nodes (5): cached_call(), transport_request_count(), test_concurrent_callers_collapse_into_one(), test_evidence_that_was_already_held_costs_nothing(), test_transport_requests_counts_the_real_http_calls()

### Community 34 - "EvidenceDependenceMap.tsx"
Cohesion: 0.15
Nodes (13): lucide-react, react, react-dom, recompose(), CellState, compareDirection(), compositionKey(), EvidenceDependenceMap() (+5 more)

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "Free Model Transport"
Cohesion: 0.11
Nodes (10): _api_key(), _asserts_an_unverified_locality(), _build_user_prompt(), _clean_text(), _load_env_once(), _numbers_are_allowed(), _post(), _source_names() (+2 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Evidence Presentation"
Cohesion: 0.11
Nodes (11): excerpt(), group_tags(), is_organisation(), present_place(), presentation_key(), split_sentences(), tag_bucket(), tag_family() (+3 more)

### Community 40 - "Free Naming Layer"
Cohesion: 0.13
Nodes (11): _ask_model(), LlmUnavailable, _parse_json(), test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post(), test_an_answer_that_is_not_json_is_not_used() (+3 more)

### Community 41 - "Evidence Test Wiring"
Cohesion: 0.07
Nodes (26): create_workspace(), error_response(), export_exploration(), generate(), health(), health_alias(), http_error_handler(), issue_key() (+18 more)

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 44 - "Workflow Budgets and Direction Naming"
Cohesion: 0.13
Nodes (12): _check_budget(), is_configured(), name_directions(), _read_calls(), _record_call(), select_source_items(), _timeout(), _write_calls() (+4 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (21): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+13 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.13
Nodes (11): validate_directions(), test_a_citation_is_dropped(), test_a_claim_about_a_locality_qloo_did_not_establish_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_name_that_is_a_qloo_name_may_keep_its_digits(), test_a_number_qloo_returned_somewhere_else_is_still_dropped(), test_a_number_the_model_invented_is_dropped(), test_a_placeholder_field_is_dropped_but_the_rest_stays() (+3 more)

### Community 47 - "Shared Contracts and Heat Map"
Cohesion: 0.16
Nodes (15): AnchorRanking, AudienceComparison, AudienceComparisonResult, PlaceStrip(), ProvenanceDrawer(), BusinessType, Concept, CulturalSignal (+7 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "QlooHarnessProvider"
Cohesion: 0.08
Nodes (15): _rank_venues(), compare_audiences(), own(), rows(), rank_entities(), recompose(), _without(), QlooHarnessError (+7 more)

### Community 50 - "AnchorTournament.tsx"
Cohesion: 0.33
Nodes (6): rankAnchors(), AnchorTournament(), run(), Choice, CHOICES, guessDemographic()

### Community 51 - "Platform Security Tests"
Cohesion: 0.07
Nodes (16): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, The shape of the codebase (+8 more)

### Community 53 - ".run_workflow_cached"
Cohesion: 0.06
Nodes (20): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for(), list_facets() (+12 more)

### Community 54 - "Qloo Request Metering"
Cohesion: 0.17
Nodes (3): begin(), count(), total()

### Community 56 - "Evidence Test Module"
Cohesion: 0.12
Nodes (18): challenge_directions(), guess_demographic(), _concept(), _evidence(), FakeProvider, _response(), test_a_direction_can_be_held_to_a_different_place(), test_a_direction_with_only_type_tags_is_unproven() (+10 more)

### Community 60 - "Challenge API Routes"
Cohesion: 0.16
Nodes (13): _revision_response(), clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), CulturalSignal (+5 more)

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 497 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `Research Run Orchestration`, `test_a_failure_is_not_held`, `Workflow Budgets and Direction Naming`, `providers.py`, `Challenge API Routes`, `Free Naming Layer Tests`, `test_evidence_store.py`, `post`, `.run_workflow_cached`, `Qloo Request Metering`, `Evidence Test Module`, `Evidence Challenge Logic`, `TraceEvent`, `Typed Request Models`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 24 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.08912655971479501 - nodes in this community are weakly interconnected._
- **Why does `ProjectRequest` connect `Challenge API Routes` to `Research Run Orchestration`, `test_a_failure_is_not_held`, `Evidence Test Wiring`, `providers.py`, `Free Naming Layer Tests`, `QlooHarnessProvider`, `Platform Security Tests`, `test_evidence_store.py`, `.run_workflow_cached`, `Evidence Concept Composer`, `Evidence Test Module`, `Evidence Challenge Logic`, `TraceEvent`, `Typed Request Models`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Build Tooling and Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05263157894736842 - nodes in this community are weakly interconnected._