# Graph Report - CultureForge AI  (2026-10-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 677 nodes · 1289 edges · 40 communities (34 shown, 6 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 83 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `35afa6c6`
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
- Research Run API Surface
- Comparison and Ranking Routes
- Provider Abstraction
- Shared Data Contracts
- Backend HTTP Tests
- Mock Data Generation
- API Error Handling
- Taste Seeds and Anchor Tournament
- Cultural Constellation Graph
- Front Page Script Interactions
- Agent Workflow Documentation
- Verification and Execution Scripts

## God Nodes (most connected - your core abstractions)
1. `QlooHarnessProvider` - 42 edges
2. `App()` - 31 edges
3. `QlooHarnessError` - 27 edges
4. `TraceEvent` - 21 edges
5. `_execute()` - 21 edges
6. `ProjectRequest` - 20 edges
7. `EvidenceStore` - 19 edges
8. `ResearchRun` - 18 edges
9. `compilerOptions` - 17 edges
10. `GenerateResponse` - 15 edges

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

## Communities (40 total, 6 thin omitted)

### Community 0 - "Comparison and Provenance Internals"
Cohesion: 0.10
Nodes (10): compare_audiences(), own(), rows(), safe_query(), StubProvider, test_a_comparison_needs_both_sides(), test_the_allowlist_covers_every_query_key_the_app_sends(), test_the_provenance_allowlist_drops_everything_it_does_not_know() (+2 more)

### Community 1 - "Studio Application Shell"
Cohesion: 0.10
Nodes (27): save(), audiencePresets, BarIcon(), BusinessIcon(), Button(), Compare(), ConceptModal(), Create() (+19 more)

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
Cohesion: 0.10
Nodes (18): TraceEvent, mark_reused(), _event(), _execute(), ResearchRegistry, ResearchRun, start_research(), test_the_rank_workflow_reports_the_signal_qloo_actually_sent() (+10 more)

### Community 14 - "Front Page Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 16 - "Qloo Harness Provider"
Cohesion: 0.12
Nodes (5): rank_entities(), recompose(), QlooHarnessProvider, test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it(), test_a_repeated_brief_reports_that_it_spent_nothing()

### Community 20 - "Contract Verification Tool"
Cohesion: 0.31
Nodes (9): BUSINESS_TYPES, checkObject(), checkResponse(), CONTRACT, fail(), failures, main(), notes (+1 more)

### Community 21 - "Backend HTTP Routes"
Cohesion: 0.16
Nodes (7): get_store(), health(), health_alias(), read_snapshot(), recent_runs(), run_status(), share_exploration()

### Community 22 - "Evidence Concept Composer"
Cohesion: 0.12
Nodes (16): compose(), ComposedConcept, _facet_rank(), _first_sentence(), _matches(), _number(), Recipe, _tag_name() (+8 more)

### Community 23 - "Studio Evidence Components"
Cohesion: 0.18
Nodes (15): AnchorRanking, AudienceComparison, AudienceComparisonResult, PlaceStrip(), ProvenanceDrawer(), BusinessType, Concept, CulturalSignal (+7 more)

### Community 24 - "Frontend Data Access"
Cohesion: 0.17
Nodes (12): fetchSnapshot(), resolveTaste(), shareExploration(), startResearch(), App(), applyScenario(), beginResearch(), confirmSeeds() (+4 more)

### Community 25 - "Durable Evidence Store"
Cohesion: 0.07
Nodes (11): cached_call(), canonical_key(), EvidenceStore, transport_request_count(), test_a_stored_envelope_survives_a_new_store_instance(), test_canonical_key_is_stable_and_order_independent(), test_concurrent_callers_collapse_into_one(), test_entries_expire() (+3 more)

### Community 26 - "Walkthrough Verification Tool"
Cohesion: 0.46
Nodes (7): api(), BRIEF, check(), fail(), main(), ok(), sleep()

### Community 27 - "Research Run API Surface"
Cohesion: 0.21
Nodes (14): compareAudience(), compareAudiences(), detailMessage(), fetchResearchRun(), postJson(), rankAnchors(), recompose(), ResearchRun (+6 more)

### Community 28 - "Comparison and Ranking Routes"
Cohesion: 0.14
Nodes (8): compare(), compare_audiences(), rank_anchors(), recompose_route(), resolve_taste(), start_run(), QlooHarnessError, run_workflow_cached()

### Community 29 - "Provider Abstraction"
Cohesion: 0.25
Nodes (9): generate(), GenerateResponse, ProjectRequest, create_provider(), CultureProvider, get_provider(), _is_qloo_configured(), MockCultureProvider (+1 more)

### Community 30 - "Shared Data Contracts"
Cohesion: 0.14
Nodes (15): clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive(), CompareRequest, Concept (+7 more)

### Community 31 - "Backend HTTP Tests"
Cohesion: 0.15
Nodes (3): client(), test_the_compare_endpoint_refuses_without_a_live_provider(), test_validation_errors_are_readable()

### Community 32 - "Mock Data Generation"
Cohesion: 0.36
Nodes (8): generateConcepts(), create(), audienceLens(), clamp(), fingerprint(), investment(), mockGenerate(), normalize()

### Community 34 - "Taste Seeds and Anchor Tournament"
Cohesion: 0.22
Nodes (7): react, TasteSeed, AnchorTournament(), Choice, CHOICES, guessDemographic(), TasteSeeds()

### Community 35 - "Cultural Constellation Graph"
Cohesion: 0.19
Nodes (12): CulturalConstellation(), Edge, LABEL_RING, LABEL_WIDTH, labelSpot(), Node, NODE_RADIUS, NodeKind (+4 more)

### Community 45 - "Front Page Script Interactions"
Cohesion: 0.12
Nodes (17): easeOutCubic(), init(), initBackgroundVideo(), attemptPlay(), unlock(), initCinematic(), initFramerMotionEnhancements(), initLandingNavigation() (+9 more)

### Community 90 - "Agent Workflow Documentation"
Cohesion: 0.29
Nodes (6): Delegation protocol, Maintenance, Project knowledge workflow, Qloo live data — spend quota carefully, Retrieval ladder, Tools

### Community 147 - "Verification and Execution Scripts"
Cohesion: 0.08
Nodes (15): typescript, argv, client, distDir, executor, harnessDir, MAX_ATTEMPTS, resolutionProvider (+7 more)

## Knowledge Gaps
- **25 isolated node(s):** `autoprefixer`, `motion`, `postcss`, `tailwindcss`, `@types/react` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 289 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QlooHarnessProvider` connect `Qloo Harness Provider` to `Comparison and Provenance Internals`, `Research and Comparison Internals`, `Backend HTTP Routes`, `Durable Evidence Store`, `Comparison and Ranking Routes`, `Provider Abstraction`, `Shared Data Contracts`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `QlooHarnessProvider` (e.g. with `compare()` and `resolve_taste()`) actually correct?**
  _`QlooHarnessProvider` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `autoprefixer`, `motion`, `postcss` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Comparison and Provenance Internals` be split into smaller, more focused modules?**
  _Cohesion score 0.10144927536231885 - nodes in this community are weakly interconnected._
- **Why does `EvidenceStore` connect `Durable Evidence Store` to `Backend HTTP Routes`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `QlooHarnessError` (e.g. with `compare()` and `compare_audiences()`) actually correct?**
  _`QlooHarnessError` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio Application Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.10483870967741936 - nodes in this community are weakly interconnected._