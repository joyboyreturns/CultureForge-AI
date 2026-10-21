# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- 94 files · ~114,101 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 5, .css 4, .example 1)

## Summary
- 1368 nodes · 3031 edges · 83 communities (70 shown, 13 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 235 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e78780aa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_a_failure_is_not_held
- Studio Application Shell
- Build Tooling and Dependencies
- TypeScript App Compiler Settings
- Front Page Marketing Copy
- Devpost text draft
- Personalised Mockups
- Local Retrieval and Media Utilities
- TypeScript Node Build Settings
- OpenCode Configuration
- Audience and Concept Copy
- Studio Concept Mockups
- Cafe Ritual Mockup Detail
- HTTP Contract Verification
- Front Page Metadata
- TypeScript Project References
- Evidence Test Client
- Graphify MCP Wrapper
- Durable Evidence Cache
- post
- Evidence Concept Composer
- lucide-react
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Evidence
- Export and Notebook Regression Tests
- test_a_repeated_brief_reports_that_it_spent_nothing
- HTTP Workflow Surface
- Platform Layer
- run_agent
- typing
- Evidence Dependence Comparison
- Cultural Constellation Graph
- Vercel Gateway Naming
- Endpoint Verification Tool
- Evidence Presentation
- _ask_model
- get_platform
- Evidence Generation and Recomposition
- HTTP Surface and Health
- name_directions
- Front Page Script Interactions
- Free Naming Layer Tests
- Studio Response Contracts
- Provider Readiness Diagnostics
- Typed Request Models
- Cached Workflow Retrieval
- GenerateResponse
- Audience Comparison Tests
- Investigation Workflow Routing
- QlooHarnessProvider
- Cited Evidence Selection
- Evidence Test Module
- Production Frontend Serving
- rank_entities
- run_agent
- Bounded Evidence Analysis
- Bounded Evidence Analysis
- scripts
- error_response
- Studio Error Recovery
- Guided Studio Tour
- Bounded Naming and Metering
- devDependencies
- CultureForge AI Prototype
- Alternative Anchor Ranking
- dependencies
- Submission Packaging Checks
- Frontend Build and Proxy
- Publish the complete application
- CultureProvider Abstraction
- Competitive review — 21 October 2026
- Judge assessment and remaining sprint
- Compare
- FastAPI Backend
- Final local review — 21 October 2026
- Judge Journey Documentation
- Third Party Asset Notices
- Qloo Timeout Transport

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 77 edges
2. `App()` - 52 edges
3. `ProjectRequest` - 42 edges
4. `QlooHarnessError` - 38 edges
5. `GenerateResponse` - 31 edges
6. `run_agent()` - 29 edges
7. `TraceEvent` - 29 edges
8. `_execute()` - 29 edges
9. `canonical_key()` - 27 edges
10. `Platform` - 27 edges

## Surprising Connections (you probably didn't know these)
- `The shape of the codebase` --references--> `get_provider()`  [INFERRED]
  AGENTS.md → backend/providers.py
- `The shape of the codebase` --references--> `MockCultureProvider`  [INFERRED]
  AGENTS.md → backend/providers.py
- `main()` --calls--> `name_directions()`  [EXTRACTED]
  scripts/llm_check.py → backend/llm.py
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `_payload()` --uses--> `GenerateResponse`  [INFERRED]
  backend/agent.py → backend/models.py

## Import Cycles
- None detected.

## Communities (83 total, 13 thin omitted)

### Community 0 - "test_a_failure_is_not_held"
Cohesion: 0.18
Nodes (6): _stub_qloo(), test_a_failure_is_not_held(), test_the_model_names_the_directions(), fake_name(), test_the_names_are_held_so_a_repeat_costs_nothing(), test_without_a_model_the_rules_still_name_the_directions()

### Community 1 - "Studio Application Shell"
Cohesion: 0.07
Nodes (31): BackendStatus, EvidenceAnalysisResult, listExplorations(), SavedExploration, TasteSeed, save(), audiencePresets, BarIcon() (+23 more)

### Community 2 - "Build Tooling and Dependencies"
Cohesion: 0.14
Nodes (13): engines, node, license, name, private, type, version, autoprefixer (+5 more)

### Community 3 - "TypeScript App Compiler Settings"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Front Page Marketing Copy"
Cohesion: 0.23
Nodes (14): CultureForge Light Dashboard Screenshot, Audience Cultural Affinities, Business Concept Exploration, Café Rituals, Connect Cultural Dots, From Insight to What If, A Small Change, A New Angle, Culture, Commerce, and Possibility (+6 more)

### Community 5 - "Devpost text draft"
Cohesion: 0.18
Nodes (10): Challenges and accomplishments, Devpost text draft, Final review sequence, How it works, Inspiration, Release requirements, Submission handoff, What it does (+2 more)

### Community 6 - "Personalised Mockups"
Cohesion: 0.32
Nodes (11): CultureForge Concept Studio Desktop Mockup, CultureForge Concept Studio Mobile Mockup, Audience Lens Scenario Exploration, Cultural Signals and Experience Blueprint Panel, Family Market Day Makers Market, Flexible Timing Cultural Signal, Hand-Me-Down House Repair and Resale Shop, Little & Local Concept Store (+3 more)

### Community 7 - "Local Retrieval and Media Utilities"
Cohesion: 0.08
Nodes (25): entities(), isolated_runtime(), no_model_calls(), analyze(), _boxes(), _child(), _find(), is_faststart() (+17 more)

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

### Community 13 - "HTTP Contract Verification"
Cohesion: 0.20
Nodes (12): BUSINESS_TYPES, checkObject(), checkResponse(), CONTRACT, fail(), failures, main(), notes (+4 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Evidence Test Client"
Cohesion: 0.24
Nodes (9): ChallengedDirection, Verdict, ConceptModal(), ChallengePanel(), VERDICT_NOTES, VERDICT_WORDS, VerdictBadge(), VerdictStep (+1 more)

### Community 20 - "Durable Evidence Cache"
Cohesion: 0.13
Nodes (10): canonical_key(), transport_request_count(), test_a_location_with_no_places_is_not_offered(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one(), test_entries_expire(), test_evidence_that_was_already_held_costs_nothing(), test_the_provider_reports_zero_for_a_cached_workflow() (+2 more)

### Community 21 - "post"
Cohesion: 0.09
Nodes (13): analyze_evidence_route(), challenge_directions_route(), challenge_probe_route(), compare(), compare_audiences(), evidence_presentation_route(), investigate_route(), rank_anchors() (+5 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.09
Nodes (23): compose(), ComposedConcept, _facet_rank(), by_organisation(), _first_sentence(), _is_organisation(), _matches(), _number() (+15 more)

### Community 23 - "lucide-react"
Cohesion: 0.33
Nodes (5): lucide-react, fetchResearchRun(), Progress(), AgentTrace(), poll()

### Community 24 - "Frontend Data Access"
Cohesion: 0.08
Nodes (47): analyzeEvidence(), briefKey(), ChallengeCheck, challengeDirections(), challengeReplacementProbe(), compareAudience(), compareAudiences(), detailMessage() (+39 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Evidence"
Cohesion: 0.16
Nodes (17): react, AudienceComparisonResult, Facet, investigate(), Investigation, listFacets(), ReplacementProbeResult, GeoLayer (+9 more)

### Community 28 - "Export and Notebook Regression Tests"
Cohesion: 0.15
Nodes (10): typescript, challenge, changed, concept, evidence, keyedResult, original, record (+2 more)

### Community 29 - "test_a_repeated_brief_reports_that_it_spent_nothing"
Cohesion: 0.33
Nodes (4): recommend_places(), test_a_repeated_brief_reports_that_it_spent_nothing(), fake(), fake()

### Community 30 - "HTTP Workflow Surface"
Cohesion: 0.15
Nodes (10): _demographics(), qloo_audience_demographics(), qloo_describe(), qloo_entity_tags(), qloo_trends(), _workflow_response(), audience_demographics_payload(), describe_payload() (+2 more)

### Community 31 - "Platform Layer"
Cohesion: 0.10
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "run_agent"
Cohesion: 0.09
Nodes (23): AgentReport, TraceEvent, _event(), _execute(), announce(), ResearchRegistry, ResearchRun, _save_exploration() (+15 more)

### Community 34 - "Evidence Dependence Comparison"
Cohesion: 0.26
Nodes (10): DependenceSummary, EvidenceDependenceMap(), labels, Rebuild, RemovalRow, CellState, compareDirection(), compositionKey() (+2 more)

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "Vercel Gateway Naming"
Cohesion: 0.22
Nodes (12): _api_key(), budget_state(), _clean_text(), is_configured(), _load_env_once(), _model(), _numbers_are_allowed(), _post() (+4 more)

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Evidence Presentation"
Cohesion: 0.15
Nodes (9): excerpt(), group_tags(), is_organisation(), present_evidence(), present_place(), presentation_key(), split_sentences(), tag_bucket() (+1 more)

### Community 40 - "_ask_model"
Cohesion: 0.14
Nodes (10): _ask_model(), _build_user_prompt(), LlmUnavailable, _parse_json(), test_an_answer_that_is_not_json_is_not_used(), test_gateway_failure_is_not_retried(), fail(), test_json_wrapped_in_a_fence_is_read() (+2 more)

### Community 41 - "get_platform"
Cohesion: 0.13
Nodes (15): create_workspace(), export_exploration(), generate(), issue_key(), list_explorations(), list_keys(), meter_requests(), read_exploration() (+7 more)

### Community 43 - "HTTP Surface and Health"
Cohesion: 0.15
Nodes (8): health(), health_alias(), qloo_workflows(), read_snapshot(), recent_runs(), run_status(), usage(), capabilities()

### Community 44 - "name_directions"
Cohesion: 0.24
Nodes (10): _check_budget(), name_directions(), _read_calls(), _record_call(), select_source_items(), _timeout(), _write_calls(), test_disabled_gateway_never_attempts_a_naming_call() (+2 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.11
Nodes (21): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+13 more)

### Community 46 - "Free Naming Layer Tests"
Cohesion: 0.11
Nodes (12): _asserts_an_unverified_locality(), _source_names(), validate_directions(), test_a_citation_is_dropped(), test_a_claim_about_a_locality_qloo_did_not_establish_is_dropped(), test_a_direction_with_nothing_usable_is_not_returned(), test_a_name_that_is_a_qloo_name_may_keep_its_digits(), test_a_number_qloo_returned_somewhere_else_is_still_dropped() (+4 more)

### Community 47 - "Studio Response Contracts"
Cohesion: 0.12
Nodes (26): AudienceComparison, CacheEntry, ChallengeResult, ResearchRun, exportBrief(), renderBrief(), AgentOutcome(), DecisionNotebook() (+18 more)

### Community 48 - "Provider Readiness Diagnostics"
Cohesion: 0.18
Nodes (5): load_qloo_config(), main(), mask(), read_budget_log(), _load_env()

### Community 49 - "Typed Request Models"
Cohesion: 0.09
Nodes (17): AgentObservation, ChallengeRequest, CompareAudiencesRequest, Decision, EntityListRequest, EntityRequest, ErrorBody, ErrorResponse (+9 more)

### Community 50 - "Cached Workflow Retrieval"
Cohesion: 0.13
Nodes (6): cached_call(), get_store(), known_location(), _is_qloo_configured(), mark_reused(), store()

### Community 51 - "GenerateResponse"
Cohesion: 0.05
Nodes (32): Caching, and what it costs, Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The shape of the codebase, The Vercel model layer (+24 more)

### Community 52 - "Audience Comparison Tests"
Cohesion: 0.07
Nodes (14): compare_audiences(), own(), rows(), Delivery, safe_query(), RecomposeProvider, StubProvider, test_a_comparison_needs_both_sides() (+6 more)

### Community 53 - "Investigation Workflow Routing"
Cohesion: 0.16
Nodes (9): _bounds(), _call_for(), _geography_points(), investigate(), _now(), _workflow_for(), list_facets(), qloo_where_popular() (+1 more)

### Community 55 - "Cited Evidence Selection"
Cohesion: 0.32
Nodes (3): _records(), select(), validate()

### Community 56 - "Evidence Test Module"
Cohesion: 0.05
Nodes (43): challenge_directions(), _challenge_one(), _compare_with_other_places(), guess_demographic(), _is_cultural_signal(), challenge_probe(), _primary_anchor(), _tag_family() (+35 more)

### Community 57 - "Production Frontend Serving"
Cohesion: 0.16
Nodes (4): published(), test_an_incomplete_build_fails_before_deployment(), FrontendFiles, mount_frontend()

### Community 58 - "rank_entities"
Cohesion: 0.22
Nodes (3): _rank_venues(), rank_entities(), test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it()

### Community 59 - "run_agent"
Cohesion: 0.13
Nodes (13): _event(), _payload(), _recipe(), run_agent(), _validate_action(), AgentAction, EvidenceAnalysisResult, reflection() (+5 more)

### Community 60 - "Bounded Evidence Analysis"
Cohesion: 0.22
Nodes (18): EvidenceAnalysisDirection, EvidenceAnalysisOutput, EvidenceAnalysisRequest, analyze(), _cache_key(), _call(), _deterministic_fields(), _prompt() (+10 more)

### Community 61 - "Bounded Evidence Analysis"
Cohesion: 0.25
Nodes (6): AnalysisUnavailable, call_structured(), _calls(), configured(), _daily_limit(), _reserve()

### Community 62 - "scripts"
Cohesion: 0.17
Nodes (12): scripts, build, check:api, check:release, check:submission, dev, preview, test:backend (+4 more)

### Community 63 - "error_response"
Cohesion: 0.24
Nodes (4): error_response(), http_error_handler(), qloo_error_handler(), validation_exception_handler()

### Community 65 - "Guided Studio Tour"
Cohesion: 0.33
Nodes (4): GuidedTour(), savedStep(), TOUR_STEPS, tourNeedsEvidence()

### Community 67 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, autoprefixer, postcss, tailwindcss, @types/react, @types/react-dom, typescript, vite (+1 more)

### Community 68 - "CultureForge AI Prototype"
Cohesion: 0.43
Nodes (3): Vite API Proxy, CultureForge AI Prototype, React TypeScript Vite Frontend

### Community 69 - "Alternative Anchor Ranking"
Cohesion: 0.40
Nodes (5): AnchorRanking, AnchorTournament(), Choice, CHOICES, guessDemographic()

### Community 70 - "dependencies"
Cohesion: 0.40
Nodes (5): dependencies, lucide-react, motion, react, react-dom

### Community 71 - "Submission Packaging Checks"
Cohesion: 0.29
Nodes (3): manifest, release, root

### Community 72 - "Frontend Build and Proxy"
Cohesion: 0.50
Nodes (3): vite, @vitejs/plugin-react, apiProxy

### Community 73 - "Publish the complete application"
Cohesion: 0.33
Nodes (5): Build and rehearse, Hosting configuration, Publish the complete application, Release verification, Without Docker

### Community 74 - "CultureProvider Abstraction"
Cohesion: 0.40
Nodes (5): CultureProvider Abstraction, Shared Mock Catalog, MockCultureProvider, Qloo Hackathon Kit CLI, QlooHarnessProvider

### Community 75 - "Competitive review — 21 October 2026"
Cohesion: 0.40
Nodes (5): Competitive review — 21 October 2026, Judge-facing evidence, Positioning decision, Previous results and closest alternatives, What would improve the entry beyond this audit

### Community 76 - "Judge assessment and remaining sprint"
Cohesion: 0.40
Nodes (5): Founder validation protocol, Highest-value work before the deadline, Judge assessment and remaining sprint, What I would look for as a judge, Would this beat the previous winners?

### Community 77 - "Compare"
Cohesion: 0.40
Nodes (4): apply(), takeHandoff(), Compare(), AudienceComparison()

### Community 78 - "FastAPI Backend"
Cohesion: 0.50
Nodes (4): FastAPI Backend, FastAPI Dependency, python-dotenv Dependency, Uvicorn Dependency

### Community 79 - "Final local review — 21 October 2026"
Cohesion: 0.50
Nodes (4): Changes made, Final local review — 21 October 2026, Remaining owner steps, Verification

### Community 147 - "Qloo Timeout Transport"
Cohesion: 0.12
Nodes (9): argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider, resolved (+1 more)

## Knowledge Gaps
- **25 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 560 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `QlooHarnessProvider` to `run_agent`, `test_a_failure_is_not_held`, `Bounded Naming and Metering`, `Evidence Generation and Recomposition`, `Free Naming Layer Tests`, `Typed Request Models`, `Cached Workflow Retrieval`, `GenerateResponse`, `Audience Comparison Tests`, `Investigation Workflow Routing`, `post`, `Durable Evidence Cache`, `Evidence Test Module`, `rank_entities`, `test_a_repeated_brief_reports_that_it_spent_nothing`, `HTTP Workflow Surface`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `QlooHarnessProvider` (e.g. with `_challenge_one()` and `_compare_with_other_places()`) actually correct?**
  _`QlooHarnessProvider` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.07439024390243902 - nodes in this community are weakly interconnected._
- **Why does `Platform` connect `Platform Layer` to `get_platform`, `Cached Workflow Retrieval`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `App()` (e.g. with `startNewExploration()` and `takeHandoff()`) actually correct?**
  _`App()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Build Tooling and Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._