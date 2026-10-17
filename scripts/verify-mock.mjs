import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import ts from 'typescript'

const catalog = JSON.parse(readFileSync(new URL('../shared/mockCatalog.json', import.meta.url), 'utf8'))
const source = readFileSync(new URL('../src/mockData.ts', import.meta.url), 'utf8').replace("import catalog from '../shared/mockCatalog.json'", `const catalog = ${JSON.stringify(catalog)}`)
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText
const { mockGenerate } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)
const projects = Object.keys(catalog.businesses).flatMap(businessType => ['Young families', 'Independent creatives', 'Mindful professionals', 'Budget-conscious students', 'Remote workers', 'Adventure travelers', 'Design-conscious Gen Z & young professionals', 'Neighborhood history enthusiasts'].flatMap(audience => ['Under $25k', '$25k – $50k', '$50k – $100k'].map(budget => ({ businessType, audience, budget, location: 'Bengaluru, India', objectives: ['Build a loyal community'] }))))
const python = existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python3'
const backend = spawnSync(python, ['-B', '-c', `import json,sys\nfrom backend.models import ProjectRequest\nfrom backend.mock_generator import generate_mock\nprint(json.dumps([generate_mock(ProjectRequest(**item)).model_dump() for item in json.load(sys.stdin)]))`], { input: JSON.stringify(projects), encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 })
assert.equal(backend.status, 0, backend.stderr)
const serverResponses = JSON.parse(backend.stdout)
projects.forEach((project, index) => {
  const client = mockGenerate(project)
  const server = serverResponses[index]
  delete client.projectId; delete server.projectId
  assert.deepEqual(client, server, `Frontend/backend drift: ${project.businessType} / ${project.audience} / ${project.budget}`)
  assert.equal(client.dataMode, 'mock')
  assert.equal(client.provenance.source, 'Mock')
  assert.equal(client.concepts.length, 3)
  assert.equal(new Set(client.concepts.map(concept => concept.name)).size, 3)
  assert.equal(new Set(client.concepts.map(concept => concept.id)).size, 3)
  client.concepts.forEach(concept => {
    assert.equal(concept.moments.length, 3)
    assert.ok(concept.implementationNote.includes(project.location))
    assert.ok(concept.implementationNote.includes(project.objectives[0]))
    assert.ok(concept.audienceFit >= 65 && concept.audienceFit <= 96)
    if (project.budget === 'Under $25k') assert.ok(Number(concept.investment.match(/–(\d+)k/)[1]) < 25)
    if (project.businessType !== 'Food & beverage') assert.doesNotMatch(JSON.stringify(concept), /coffee|caf[ée]|supper|vinyl/i)
  })
})
for (const businessType of Object.keys(catalog.businesses)) {
  const variants = projects.filter(project => project.businessType === businessType && project.budget === '$25k – $50k').map(project => mockGenerate(project))
  assert.equal(new Set(variants.map(result => result.concepts.map(concept => concept.name).join('|'))).size, 7, `${businessType}: expected distinct named directions for all seven catalog lenses`)
  assert.notEqual(variants[0].concepts[0].description, variants[1].concepts[0].description)
}
console.log(`Passed ${projects.length} cross-runtime cases: five business types, eight audience briefs, three budgets; mock provenance, diversity, blueprints, and pilot costs.`)
