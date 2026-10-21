# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1174 nodes · 2457 edges · 61 communities (52 shown, 9 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 184 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b34f7016`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Provider Internals
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
- Shared API Contracts
- Front Page Metadata
- TypeScript Project References
- Evidence Test Client
- Graphify MCP Wrapper
- Evidence Store Tests
- API Workflow Routes
- Evidence Concept Composer
- Studio API Contracts
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Frontend Investigation Client
- Evidence Challenge Logic
- Request Metering
- Typed Request Models
- Platform Layer
- Research Run Orchestration
- API Error Handling
- Build Tooling and Entry Points
- Cultural Constellation Graph
- Free Model Transport
- Endpoint Verification Tool
- Evidence Presentation
- Free Naming Layer
- Evidence Test Wiring
- Naming Guard and Budget
- Provider and Comparison Internals
- Workflow Budgets and Direction Naming
- Front Page Script Interactions
- Free Naming Layer Tests
- Shared Contracts and Heat Map
- Free Naming Layer
- Venue Ranking and Recomposition
- Qloo Provider Workflows
- Platform Security Tests
- Audience Comparison Logic
- Investigation Decision Loop
- Qloo Request Metering
- Evidence Cache and Provider Tests
- Evidence Test Module
- Provider and Comparison Contracts
- Qloo Workflow Capabilities
- Challenge API Routes
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 71 edges
2. `App()` - 42 edges
3. `ProjectRequest` - 35 edges
4. `QlooHarnessError` - 29 edges
5. `Platform` - 27 edges
6. `_execute()` - 26 edges
7. `GenerateResponse` - 23 edges
8. `TraceEvent` - 23 edges
9. `challenge_directions()` - 22 edges
10. `EvidenceStore` - 21 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `_compare_with_other_places()` --uses--> `Evidence`  [INFERRED]
  backend/challenge.py → backend/models.py

## Import Cycles
- None detected.

## Communities (61 total, 9 thin omitted)

### Community 0 - "Provider Internals"
Cohesion: 0.11
Nodes (6): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing(), test_without_a_model_the_rules_still_name_the_directions()

### Community 1 - "Studio Application Shell"
Cohesion: 0.10
Nodes (26): listExplorations(), TasteSeed, save(), audiencePresets, BarIcon(), BusinessIcon(), Button(), Compare() (+18 more)

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
Cohesion: 0.06
Nodes (30): entities(), no_model_calls(), store(), load_qloo_config(), main(), mask(), read_budget_log(), analyze() (+22 more)

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

### Community 13 - "Shared API Contracts"
Cohesion: 0.15
Nodes (13): The shape of the codebase, _challenge_one(), _venues(), Evidence, GenerateResponse, ProjectRequest, create_provider(), CultureProvider (+5 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.21
Nodes (10): ChallengedDirection, ChallengeResult, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge() (+2 more)

### Community 20 - "Evidence Store Tests"
Cohesion: 0.12
Nodes (12): cached_call(), canonical_key(), known_location(), transport_request_count(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one(), test_entries_expire() (+4 more)

### Community 21 - "API Workflow Routes"
Cohesion: 0.18
Nodes (7): qloo_describe(), qloo_entity_tags(), qloo_trends(), _workflow_response(), describe_payload(), entity_tags_payload(), trends_payload()

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.09
Nodes (21): compose(), ComposedConcept, _facet_rank(), by_organisation(), _first_sentence(), _is_organisation(), _matches(), _number() (+13 more)

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

### Community 28 - "Evidence Challenge Logic"
Cohesion: 0.29
Nodes (4): _compare_with_other_places(), _is_cultural_signal(), _tag_family(), test_a_signal_family_is_cultural_and_a_type_family_is_not()

### Community 29 - "Request Metering"
Cohesion: 0.24
Nodes (3): _records(), select(), validate()

### Community 30 - "Typed Request Models"
Cohesion: 0.07
Nodes (18): ChallengeRequest, ChallengeRevision, CompareAudiencesRequest, CompareRequest, Concept, Decision, EntityListRequest, EntityRequest (+10 more)

### Community 31 - "Platform Layer"
Cohesion: 0.09
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "Research Run Orchestration"
Cohesion: 0.06
Nodes (25): TraceEvent, mark_reused(), QlooHarnessError, _event(), _execute(), announce(), ResearchRegistry, ResearchRun (+17 more)

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
Cohesion: 0.11
Nodes (10): _api_key(), _asserts_an_unverified_locality(), _build_user_prompt(), _clean_text(), _load_env_once(), _numbers_are_allowed(), _post(), _source_names() (+2 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Evidence Presentation"
Cohesion: 0.14
Nodes (9): excerpt(), group_tags(), is_organisation(), present_evidence(), present_place(), presentation_key(), split_sentences(), tag_bucket() (+1 more)

### Community 40 - "Free Naming Layer"
Cohesion: 0.13
Nodes (11): _ask_model(), LlmUnavailable, _parse_json(), test_a_gone_model_falls_through_to_the_next(), fake_post(), test_a_model_that_answers_with_nothing_falls_through(), fake_post(), test_an_answer_that_is_not_json_is_not_used() (+3 more)

### Community 41 - "Evidence Test Wiring"
Cohesion: 0.07
Nodes (28): compare(), compare_audiences(), create_workspace(), evidence_presentation_route(), export_exploration(), generate(), health(), health_alias() (+20 more)

### Community 42 - "Naming Guard and Budget"
Cohesion: 0.15
Nodes (11): healthy_models(), _mark_healthy(), _mark_outcome(), _mark_unhealthy(), _read_health(), _write_health(), test_a_model_in_cooldown_is_asked_last_and_then_retried(), test_a_quick_model_is_asked_before_a_slow_one() (+3 more)

### Community 43 - "Provider and Comparison Internals"
Cohesion: 0.22
Nodes (8): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The free naming layer, Tools

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
Cohesion: 0.11
Nodes (22): AnchorRanking, AudienceComparison, AudienceComparisonResult, AnchorTournament(), Choice, CHOICES, guessDemographic(), CulturalHeat() (+14 more)

### Community 48 - "Free Naming Layer"
Cohesion: 0.17
Nodes (7): budget_state(), _model(), status(), test_a_model_entry_without_a_cooldown_is_read(), test_a_paid_model_is_refused(), test_the_health_reads_a_half_written_file(), main()

### Community 49 - "Venue Ranking and Recomposition"
Cohesion: 0.21
Nodes (5): _rank_venues(), rank_entities(), recompose(), _without(), get_store()

### Community 51 - "Platform Security Tests"
Cohesion: 0.11
Nodes (5): client(), test_a_key_cannot_be_revoked_from_another_workspace(), test_a_malformed_workflow_body_is_a_readable_422(), test_the_compare_endpoint_refuses_without_a_live_provider(), test_validation_errors_are_readable()

### Community 52 - "Audience Comparison Logic"
Cohesion: 0.22
Nodes (6): compare_audiences(), own(), rows(), test_a_comparison_needs_both_sides(), test_the_shared_tags_carry_the_score_and_the_hit_counts(), test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it()

### Community 53 - "Investigation Decision Loop"
Cohesion: 0.11
Nodes (13): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for(), investigate_route() (+5 more)

### Community 55 - "Evidence Cache and Provider Tests"
Cohesion: 0.33
Nodes (4): recommend_places(), test_a_repeated_brief_reports_that_it_spent_nothing(), fake(), fake()

### Community 56 - "Evidence Test Module"
Cohesion: 0.12
Nodes (18): challenge_directions(), guess_demographic(), _concept(), _evidence(), FakeProvider, _response(), test_a_direction_can_be_held_to_a_different_place(), test_a_direction_with_only_type_tags_is_unproven() (+10 more)

### Community 57 - "Provider and Comparison Contracts"
Cohesion: 0.15
Nodes (6): Delivery, safe_query(), RecomposeProvider, test_removing_a_venue_rebuilds_the_directions_without_it(), test_the_allowlist_covers_every_query_key_the_app_sends(), test_the_provenance_allowlist_drops_everything_it_does_not_know()

### Community 60 - "Challenge API Routes"
Cohesion: 0.23
Nodes (10): challenge_directions_route(), _revision_response(), clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive() (+2 more)

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (21): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+13 more)

## Knowledge Gaps
- **26 isolated node(s):** `autoprefixer`, `motion`, `postcss`, `tailwindcss`, `@types/react` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 492 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `Qloo Provider Workflows` to `Research Run Orchestration`, `Provider Internals`, `Evidence Test Wiring`, `Workflow Budgets and Direction Naming`, `Shared API Contracts`, `Challenge API Routes`, `Free Naming Layer Tests`, `Venue Ranking and Recomposition`, `Audience Comparison Logic`, `Investigation Decision Loop`, `API Workflow Routes`, `Evidence Store Tests`, `Evidence Test Module`, `Provider and Comparison Contracts`, `Evidence Cache and Provider Tests`, `Evidence Challenge Logic`, `Typed Request Models`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 24 INFERRED edges - model-reasoned connections that need verification._
- **What connects `autoprefixer`, `motion`, `postcss` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Provider Internals` be split into smaller, more focused modules?**
  _Cohesion score 0.10507246376811594 - nodes in this community are weakly interconnected._
- **Why does `ProjectRequest` connect `Shared API Contracts` to `Provider Internals`, `Research Run Orchestration`, `Evidence Test Wiring`, `Free Naming Layer Tests`, `Venue Ranking and Recomposition`, `Qloo Provider Workflows`, `Evidence Store Tests`, `Investigation Decision Loop`, `Evidence Cache and Provider Tests`, `Evidence Test Module`, `Provider and Comparison Contracts`, `Challenge API Routes`, `Typed Request Models`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.10227272727272728 - nodes in this community are weakly interconnected._