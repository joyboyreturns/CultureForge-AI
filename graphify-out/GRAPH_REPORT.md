# Graph Report - CultureForge AI  (2026-10-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 866 nodes · 1746 edges · 45 communities (36 shown, 9 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 129 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e1606082`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Comparison and Provenance Internals
- Studio Application Shell
- Build Tooling and Dependencies
- TypeScript App Compiler Settings
- Front Page Marketing Copy
- Architecture and Dependency Docs
- Personalised Mockups
- Maintenance and Retrieval Scripts
- TypeScript Node Build Settings
- OpenCode Configuration
- Audience and Concept Copy
- Studio Concept Mockups
- Cafe Ritual Mockup Detail
- Research and Comparison Internals
- Front Page Metadata
- TypeScript Project References
- Qloo Harness Provider
- Graphify MCP Wrapper
- Contract Verification Tool
- Backend HTTP Routes
- Evidence Concept Composer
- Studio Evidence Components
- Frontend Data Access
- Durable Evidence Store
- Walkthrough Verification Tool
- Frontend Investigation Client
- Qloo Workflow Routes
- HTTP Request Contracts
- Shared Data Contracts
- Platform Layer
- Mock Data Generation
- API Error Handling
- Confirmed Taste Seeds
- Cultural Constellation Graph
- Investigation Module
- Endpoint Verification Tool
- Anchor Tournament
- Frontend Entry Points
- Ranking Request and Route
- Front Page Script Interactions
- Agent Workflow Documentation
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 56 edges
2. `App()` - 32 edges
3. `Platform` - 27 edges
4. `QlooHarnessError` - 25 edges
5. `ProjectRequest` - 23 edges
6. `_execute()` - 23 edges
7. `TraceEvent` - 21 edges
8. `EvidenceStore` - 20 edges
9. `ResearchRun` - 19 edges
10. `canonical_key()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `StubProvider` --uses--> `TraceEvent`  [INFERRED]
  backend/tests/test_comparison.py → backend/models.py
- `QlooHarnessProvider` --uses--> `TraceEvent`  [INFERRED]
  backend/providers.py → backend/models.py
- `ResearchRun` --uses--> `ProjectRequest`  [INFERRED]
  backend/research.py → backend/models.py
- `StubProvider` --uses--> `QlooHarnessError`  [INFERRED]
  backend/tests/test_research.py → backend/providers.py

## Import Cycles
- None detected.

## Communities (45 total, 9 thin omitted)

### Community 0 - "Comparison and Provenance Internals"
Cohesion: 0.12
Nodes (6): safe_query(), StubProvider, test_the_allowlist_covers_every_query_key_the_app_sends(), test_the_provenance_allowlist_drops_everything_it_does_not_know(), test_the_rank_workflow_is_asked_without_a_limit(), test_the_shared_tags_carry_the_score_and_the_hit_counts()

### Community 1 - "Studio Application Shell"
Cohesion: 0.10
Nodes (30): listExplorations(), SavedExploration, save(), audiencePresets, BarIcon(), BusinessIcon(), Button(), Compare() (+22 more)

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

### Community 7 - "Maintenance and Retrieval Scripts"
Cohesion: 0.06
Nodes (30): entities(), recommend_places(), store(), fake(), load_qloo_config(), main(), mask(), read_budget_log() (+22 more)

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

### Community 13 - "Research and Comparison Internals"
Cohesion: 0.06
Nodes (31): cached_call(), canonical_key(), known_location(), transport_request_count(), TraceEvent, mark_reused(), _event(), _execute() (+23 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Qloo Harness Provider"
Cohesion: 0.08
Nodes (11): compare_audiences(), own(), rows(), rank_entities(), recompose(), Delivery, QlooHarnessError, QlooHarnessProvider (+3 more)

### Community 20 - "Contract Verification Tool"
Cohesion: 0.31
Nodes (9): BUSINESS_TYPES, checkObject(), checkResponse(), CONTRACT, fail(), failures, main(), notes (+1 more)

### Community 21 - "Backend HTTP Routes"
Cohesion: 0.09
Nodes (21): get_store(), export_exploration(), health(), health_alias(), list_explorations(), list_facets(), list_keys(), meter_requests() (+13 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.12
Nodes (16): compose(), ComposedConcept, _facet_rank(), _first_sentence(), _matches(), _number(), Recipe, _tag_name() (+8 more)

### Community 23 - "Studio Evidence Components"
Cohesion: 0.15
Nodes (20): AnchorRanking, AudienceComparison, AudienceComparisonResult, GeoPoint, Investigation, InvestigationTool, ResearchRun, TasteResolution (+12 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.13
Nodes (19): compareAudience(), compareAudiences(), fetchExploration(), fetchSnapshot(), postJson(), recompose(), resolveTaste(), shareExploration() (+11 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Frontend Investigation Client"
Cohesion: 0.17
Nodes (14): react, Facet, fetchResearchRun(), investigate(), listFacets(), AgentTrace(), poll(), GeoLayer (+6 more)

### Community 28 - "Qloo Workflow Routes"
Cohesion: 0.09
Nodes (11): qloo_audience_demographics(), qloo_describe(), qloo_entity_tags(), qloo_trends(), _workflow_response(), audience_demographics_payload(), describe_payload(), entity_tags_payload() (+3 more)

### Community 29 - "HTTP Request Contracts"
Cohesion: 0.09
Nodes (11): compare(), compare_audiences(), create_workspace(), investigate_route(), issue_key(), recompose_route(), resolve_taste(), start_run() (+3 more)

### Community 30 - "Shared Data Contracts"
Cohesion: 0.06
Nodes (28): generate(), count(), total(), clamp(), fingerprint(), generate_mock(), investment(), normalize() (+20 more)

### Community 31 - "Platform Layer"
Cohesion: 0.08
Nodes (14): hash_key(), Platform, platform(), test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(), test_a_key_is_issued_and_never_stored_in_the_clear(), test_a_new_version_is_added_when_an_exploration_is_saved_again(), test_a_revoked_key_stops_working(), test_a_shared_snapshot_is_reachable_and_revocable() (+6 more)

### Community 32 - "Mock Data Generation"
Cohesion: 0.31
Nodes (9): detailMessage(), generateConcepts(), create(), audienceLens(), clamp(), fingerprint(), investment(), mockGenerate() (+1 more)

### Community 33 - "API Error Handling"
Cohesion: 0.22
Nodes (5): error_response(), http_error_handler(), qloo_error_handler(), validation_exception_handler(), ErrorBody

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 36 - "Investigation Module"
Cohesion: 0.22
Nodes (8): _bounds(), _call_for(), _demographics(), _geography_points(), investigate(), _now(), _workflow_for(), qloo_where_popular()

### Community 37 - "Endpoint Verification Tool"
Cohesion: 0.36
Nodes (8): api(), BRIEF, check(), fail(), main(), ok(), readableDetail(), seen

### Community 38 - "Anchor Tournament"
Cohesion: 0.33
Nodes (6): rankAnchors(), AnchorTournament(), run(), Choice, CHOICES, guessDemographic()

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.12
Nodes (17): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+9 more)

### Community 90 - "Agent Workflow Documentation"
Cohesion: 0.25
Nodes (7): Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, The shape of the codebase, Tools

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (15): typescript, argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider (+7 more)

## Knowledge Gaps
- **25 isolated node(s):** `autoprefixer`, `motion`, `postcss`, `tailwindcss`, `@types/react` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 355 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `Qloo Harness Provider` to `Investigation Module`, `Research and Comparison Internals`, `Backend HTTP Routes`, `Qloo Workflow Routes`, `HTTP Request Contracts`, `Shared Data Contracts`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `QlooHarnessProvider` (e.g. with `_call_for()` and `compare()`) actually correct?**
  _`QlooHarnessProvider` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `autoprefixer`, `motion`, `postcss` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Comparison and Provenance Internals` be split into smaller, more focused modules?**
  _Cohesion score 0.12280701754385964 - nodes in this community are weakly interconnected._
- **Why does `Platform` connect `Platform Layer` to `Backend HTTP Routes`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `QlooHarnessError` (e.g. with `qloo_error_handler()` and `test_a_comparison_needs_both_sides()`) actually correct?**
  _`QlooHarnessError` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.10160427807486631 - nodes in this community are weakly interconnected._