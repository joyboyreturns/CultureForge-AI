# Graph Report - CultureForge AI  (2026-10-20)

## Corpus Check
- 49 files · ~53,059 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: .css 3, (none) 2, .example 1)

## Summary
- 651 nodes · 1238 edges · 43 communities (35 shown, 8 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2391ebe2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Contract Data Models
- Studio Application Shell
- Build Tooling and Dependencies
- TypeScript App Compiler Settings
- Concept Studio Prompt Templates
- Architecture and Dependency Docs
- Cultural Signal and Concept Examples
- Vault Retrieval Tool
- TypeScript Node Build Settings
- Graph MCP Server
- Desktop Dashboard Mockup Content
- Mobile Mockup Content
- Audience and Ritual Matches
- Research Agent Execution
- App Shell and Metadata
- TypeScript Project References
- Comparison and Allowlist Tests
- Graphify MCP Wrapper
- Contract Verification Tool
- Backend API Routes
- Evidence Concept Composer
- Frontend API Contracts
- Frontend Data Access
- Durable Evidence Store Internals
- API Contract Tests
- Audience Comparison and Ranking
- Evidence Store Tests
- Evidence Cache and Transport Accounting
- Qloo Harness Provider
- Provider Selection and Mock Fallback
- Mock Data Generation
- Shared Test Fixtures
- Taste Seeds and App Entry Points
- Cultural Constellation Graph
- Anchor Tournament
- Evidence Recomposition
- Cultural Heat Grid
- Front Page Script Interactions
- Agent Workflow Documentation
- Qloo Execution Wrapper

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 40 edges
2. `App()` - 31 edges
3. `QlooHarnessError` - 27 edges
4. `_execute()` - 20 edges
5. `EvidenceStore` - 19 edges
6. `ProjectRequest` - 18 edges
7. `TraceEvent` - 18 edges
8. `ResearchRun` - 18 edges
9. `compilerOptions` - 17 edges
10. `GenerateResponse` - 15 edges

## Surprising Connections (you probably didn't know these)
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `generate()` --uses--> `GenerateResponse`  [INFERRED]
  backend/main.py → backend/models.py
- `generate()` --uses--> `ProjectRequest`  [INFERRED]
  backend/main.py → backend/models.py
- `generate()` --uses--> `QlooHarnessError`  [INFERRED]
  backend/main.py → backend/providers.py
- `compare()` --uses--> `QlooHarnessError`  [INFERRED]
  backend/main.py → backend/providers.py

## Import Cycles
- None detected.

## Communities (43 total, 8 thin omitted)

### Community 0 - "Contract Data Models"
Cohesion: 0.15
Nodes (15): clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), Concept, CulturalSignal (+7 more)

### Community 1 - "Studio Application Shell"
Cohesion: 0.13
Nodes (23): save(), audiencePresets, BarIcon(), BusinessIcon(), Button(), Compare(), ConceptModal(), Create() (+15 more)

### Community 2 - "Build Tooling and Dependencies"
Cohesion: 0.05
Nodes (35): dependencies, lucide-react, motion, react, react-dom, devDependencies, autoprefixer, postcss (+27 more)

### Community 3 - "TypeScript App Compiler Settings"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Concept Studio Prompt Templates"
Cohesion: 0.23
Nodes (14): CultureForge Light Dashboard Screenshot, Audience Cultural Affinities, Business Concept Exploration, Café Rituals, Connect Cultural Dots, From Insight to What If, A Small Change, A New Angle, Culture, Commerce, and Possibility (+6 more)

### Community 5 - "Architecture and Dependency Docs"
Cohesion: 0.15
Nodes (12): Vite API Proxy, CultureProvider Abstraction, FastAPI Backend, Shared Mock Catalog, MockCultureProvider, CultureForge AI Prototype, Qloo Hackathon Kit CLI, QlooHarnessProvider (+4 more)

### Community 6 - "Cultural Signal and Concept Examples"
Cohesion: 0.32
Nodes (11): CultureForge Concept Studio Desktop Mockup, CultureForge Concept Studio Mobile Mockup, Audience Lens Scenario Exploration, Cultural Signals and Experience Blueprint Panel, Family Market Day Makers Market, Flexible Timing Cultural Signal, Hand-Me-Down House Repair and Resale Shop, Little & Local Concept Store (+3 more)

### Community 7 - "Vault Retrieval Tool"
Cohesion: 0.08
Nodes (26): load_qloo_config(), main(), mask(), read_budget_log(), analyze(), _boxes(), _child(), _find() (+18 more)

### Community 8 - "TypeScript Node Build Settings"
Cohesion: 0.20
Nodes (9): compilerOptions, lib, module, moduleResolution, noEmit, skipLibCheck, strict, target (+1 more)

### Community 9 - "Graph MCP Server"
Cohesion: 0.15
Nodes (12): codemode, command, cwd, enabled, timeout, type, mcp, servers (+4 more)

### Community 10 - "Desktop Dashboard Mockup Content"
Cohesion: 0.25
Nodes (8): Audience Understanding, Business Concept Exploration, Café and Hospitality Experience, Cultural Affinities, Cultural Connections, Cultural Insight Platform, CultureForge AI, Scenario Comparison

### Community 11 - "Mobile Mockup Content"
Cohesion: 0.39
Nodes (8): CultureForge Concept Studio Mobile Mockup, Three Cultural Connections, Cultural Connector, Design-Conscious Gen Z and Young Professionals, Food and Beverage in Brooklyn, New York, Illustrative Fit Score of 94, The Listening Room Cafe, Three Directions, One Cultural Edge

### Community 12 - "Audience and Ritual Matches"
Cohesion: 1.00
Nodes (3): Café Rituals, Shared Audience, Vinyl Culture

### Community 13 - "Research Agent Execution"
Cohesion: 0.10
Nodes (16): TraceEvent, _event(), _execute(), ResearchRegistry, ResearchRun, start_research(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent(), _trace_event() (+8 more)

### Community 14 - "App Shell and Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Comparison and Allowlist Tests"
Cohesion: 0.12
Nodes (6): safe_query(), StubProvider, test_the_allowlist_covers_every_query_key_the_app_sends(), test_the_provenance_allowlist_drops_everything_it_does_not_know(), test_the_rank_workflow_is_asked_without_a_limit(), test_the_shared_tags_carry_the_score_and_the_hit_counts()

### Community 20 - "Contract Verification Tool"
Cohesion: 0.31
Nodes (9): BUSINESS_TYPES, checkObject(), checkResponse(), CONTRACT, fail(), failures, main(), notes (+1 more)

### Community 21 - "Backend API Routes"
Cohesion: 0.09
Nodes (13): compare(), compare_audiences(), generate(), health(), health_alias(), read_snapshot(), recent_runs(), resolve_taste() (+5 more)

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.12
Nodes (16): compose(), ComposedConcept, _facet_rank(), _first_sentence(), _matches(), _number(), Recipe, _tag_name() (+8 more)

### Community 23 - "Frontend API Contracts"
Cohesion: 0.16
Nodes (20): AnchorRanking, AudienceComparison, AudienceComparisonResult, fetchResearchRun(), ResearchRun, TasteResolution, AgentTrace(), poll() (+12 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.13
Nodes (18): compareAudience(), compareAudiences(), fetchSnapshot(), postJson(), recompose(), resolveTaste(), shareExploration(), startResearch() (+10 more)

### Community 26 - "API Contract Tests"
Cohesion: 0.14
Nodes (6): GenerateResponse, MockCultureProvider, client(), test_a_valid_request_answers_with_the_contract(), test_the_compare_endpoint_refuses_without_a_live_provider(), test_validation_errors_are_readable()

### Community 27 - "Audience Comparison and Ranking"
Cohesion: 0.16
Nodes (8): compare_audiences(), own(), rows(), rank_entities(), rank_anchors(), QlooHarnessError, test_a_comparison_needs_both_sides(), run_workflow_cached()

### Community 28 - "Evidence Store Tests"
Cohesion: 0.17
Nodes (6): canonical_key(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one(), test_entries_expire(), test_evidence_that_was_already_held_costs_nothing(), test_the_provider_reports_zero_for_a_cached_workflow()

### Community 29 - "Evidence Cache and Transport Accounting"
Cohesion: 0.19
Nodes (4): cached_call(), get_store(), transport_request_count(), test_transport_requests_counts_the_real_http_calls()

### Community 31 - "Provider Selection and Mock Fallback"
Cohesion: 0.27
Nodes (4): create_provider(), CultureProvider, get_provider(), _is_qloo_configured()

### Community 32 - "Mock Data Generation"
Cohesion: 0.31
Nodes (9): detailMessage(), generateConcepts(), create(), audienceLens(), clamp(), fingerprint(), investment(), mockGenerate() (+1 more)

### Community 33 - "Shared Test Fixtures"
Cohesion: 0.24
Nodes (3): entities(), recommend_places(), store()

### Community 34 - "Taste Seeds and App Entry Points"
Cohesion: 0.22
Nodes (4): react, react-dom, TasteSeed, TasteSeeds()

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.29
Nodes (7): CulturalConstellation(), Edge, Node, NODE_RADIUS, NodeKind, polar(), VIEW

### Community 36 - "Anchor Tournament"
Cohesion: 0.33
Nodes (6): rankAnchors(), AnchorTournament(), run(), Choice, CHOICES, guessDemographic()

### Community 38 - "Cultural Heat Grid"
Cohesion: 1.00
Nodes (3): CulturalHeat(), heat(), tile()

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.12
Nodes (17): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+9 more)

### Community 90 - "Agent Workflow Documentation"
Cohesion: 0.29
Nodes (6): Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, Tools

### Community 147 - "Qloo Execution Wrapper"
Cohesion: 0.08
Nodes (15): typescript, argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider (+7 more)

## Knowledge Gaps
- **25 isolated node(s):** `motion`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 279 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `Qloo Harness Provider` to `Contract Data Models`, `Evidence Recomposition`, `Research Agent Execution`, `Backend API Routes`, `API Contract Tests`, `Audience Comparison and Ranking`, `Evidence Store Tests`, `Evidence Cache and Transport Accounting`, `Provider Selection and Mock Fallback`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `QlooHarnessProvider` (e.g. with `compare()` and `resolve_taste()`) actually correct?**
  _`QlooHarnessProvider` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `motion`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.12535612535612536 - nodes in this community are weakly interconnected._
- **Why does `EvidenceStore` connect `Durable Evidence Store Internals` to `Evidence Store Tests`, `Evidence Cache and Transport Accounting`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `QlooHarnessError` (e.g. with `compare()` and `compare_audiences()`) actually correct?**
  _`QlooHarnessError` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `Build Tooling and Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._