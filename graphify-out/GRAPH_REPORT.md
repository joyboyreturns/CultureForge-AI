# Graph Report - CultureForge AI  (2026-10-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 280 nodes · 437 edges · 20 communities (15 shown, 5 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4f31a863`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Backend Provider Models
- Frontend Types and State
- Build Tooling and Dependencies
- TypeScript App Compiler Settings
- Concept Studio Prompt Templates
- Architecture and Dependency Docs
- Cultural Signal and Concept Examples
- API Connectivity Check Script
- TypeScript Node Build Settings
- Desktop Dashboard Mockup Content
- Mobile Mockup Content
- Audience and Ritual Matches
- App Shell and Metadata
- TypeScript Project References
- Prototype Script Interactions
- Agent Workflow Documentation
- Mock Verification Script

## God Nodes (most connected - your core abstractions)
1. `App()` - 18 edges
2. `compilerOptions` - 17 edges
3. `QlooHarnessProvider` - 14 edges
4. `GenerateResponse` - 13 edges
5. `ProjectRequest` - 13 edges
6. `generate_mock()` - 13 edges
7. `CultureForge Light Dashboard Screenshot` - 13 edges
8. `mockGenerate()` - 12 edges
9. `CultureForge Concept Studio Desktop Mockup` - 10 edges
10. `CultureProvider` - 9 edges

## Surprising Connections (you probably didn't know these)
- `CultureForge Concept Studio Desktop Mockup` --semantically_similar_to--> `CultureForge Concept Studio Mobile Mockup`  [INFERRED] [semantically similar]
  artifacts/cultureforge-personalized.png → artifacts/cultureforge-readable-mobile.png
- `QlooHarnessProvider` --uses--> `CulturalSignal`  [INFERRED]
  backend/providers.py → backend/models.py
- `generate()` --uses--> `GenerateResponse`  [INFERRED]
  backend/main.py → backend/models.py
- `CultureProvider` --uses--> `GenerateResponse`  [INFERRED]
  backend/providers.py → backend/models.py
- `MockCultureProvider` --uses--> `GenerateResponse`  [INFERRED]
  backend/providers.py → backend/models.py

## Import Cycles
- None detected.

## Communities (20 total, 5 thin omitted)

### Community 0 - "Backend Provider Models"
Cohesion: 0.09
Nodes (21): generate(), health(), clamp(), fingerprint(), generate_mock(), investment(), normalize(), round_positive() (+13 more)

### Community 1 - "Frontend Types and State"
Cohesion: 0.07
Nodes (42): react, react-dom, generateConcepts(), App(), applyScenario(), create(), navigate(), save() (+34 more)

### Community 2 - "Build Tooling and Dependencies"
Cohesion: 0.06
Nodes (33): dependencies, lucide-react, motion, react, react-dom, devDependencies, autoprefixer, postcss (+25 more)

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

### Community 8 - "TypeScript Node Build Settings"
Cohesion: 0.20
Nodes (9): compilerOptions, lib, module, moduleResolution, noEmit, skipLibCheck, strict, target (+1 more)

### Community 10 - "Desktop Dashboard Mockup Content"
Cohesion: 0.25
Nodes (8): Audience Understanding, Business Concept Exploration, Café and Hospitality Experience, Cultural Affinities, Cultural Connections, Cultural Insight Platform, CultureForge AI, Scenario Comparison

### Community 11 - "Mobile Mockup Content"
Cohesion: 0.39
Nodes (8): CultureForge Concept Studio Mobile Mockup, Three Cultural Connections, Cultural Connector, Design-Conscious Gen Z and Young Professionals, Food and Beverage in Brooklyn, New York, Illustrative Fit Score of 94, The Listening Room Cafe, Three Directions, One Cultural Edge

### Community 12 - "Audience and Ritual Matches"
Cohesion: 1.00
Nodes (3): Café Rituals, Shared Audience, Vinyl Culture

### Community 14 - "App Shell and Metadata"
Cohesion: 0.67
Nodes (3): CultureForge Page Metadata, React Application Root, Stored Theme Preference

### Community 45 - "Prototype Script Interactions"
Cohesion: 0.18
Nodes (10): easeOutCubic(), init(), initFramerMotionEnhancements(), initLandingNavigation(), initMobileMenu(), initPrototypeJourney(), openStudio(), initStatsObserver() (+2 more)

### Community 90 - "Agent Workflow Documentation"
Cohesion: 0.50
Nodes (3): Delegation protocol, Project knowledge workflow, Token-efficient retrieval ladder

### Community 147 - "Mock Verification Script"
Cohesion: 0.20
Nodes (6): typescript, backend, catalog, projects, serverResponses, source

## Knowledge Gaps
- **25 isolated node(s):** `autoprefixer`, `motion`, `postcss`, `tailwindcss`, `@types/react` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 129 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `Frontend Types and State` to `Build Tooling and Dependencies`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `QlooHarnessProvider` (e.g. with `CulturalSignal` and `GenerateResponse`) actually correct?**
  _`QlooHarnessProvider` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `autoprefixer`, `motion`, `postcss` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Backend Provider Models` be split into smaller, more focused modules?**
  _Cohesion score 0.09143686502177069 - nodes in this community are weakly interconnected._
- **Why does `lucide-react` connect `Build Tooling and Dependencies` to `Frontend Types and State`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `GenerateResponse` (e.g. with `generate()` and `CultureProvider`) actually correct?**
  _`GenerateResponse` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `Frontend Types and State` be split into smaller, more focused modules?**
  _Cohesion score 0.0734006734006734 - nodes in this community are weakly interconnected._