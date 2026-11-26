// Apply the native Vue source overrides to the matching oj_2.7.5 source release.
// Usage: node frontend/prepare.js /path/to/OnlineJudgeFE-oj_2.7.5
const fs = require('fs')
const path = require('path')

const target = path.resolve(process.argv[2] || '')
if (!process.argv[2] || !fs.existsSync(path.join(target, 'src/pages/oj/components/NavBar.vue'))) {
  throw new Error('Pass the extracted OnlineJudgeFE oj_2.7.5 source directory')
}
for (const directory of ['src', 'config']) {
  fs.cpSync(path.join(__dirname, directory), path.join(target, directory), {recursive: true})
}
// Bound the legacy minifier's worker count for the course VM, and allow repeat builds on Node 22.
for (const name of ['webpack.prod.conf.js', 'webpack.dll.conf.js']) {
  const file = path.join(target, 'build', name)
  let source = fs.readFileSync(file, 'utf8')
  source = source.replace('parallel: true', 'parallel: 2').replace('fs.unlink(f)', 'fs.unlinkSync(f)')
  fs.writeFileSync(file, source)
}
// Webpack 3 may retain worker handles on current Node after reporting success.
// The callback runs after all assets are written and already exits on stats.hasErrors().
const buildFile = path.join(target, 'build/build.js')
let buildSource = fs.readFileSync(buildFile, 'utf8')
if (!buildSource.includes('process.exit(0)')) {
  buildSource = buildSource.replace(/\r?\n  \}\)\r?\n\}\)\s*$/, '\n    process.exit(0)\n  })\n})\n')
  fs.writeFileSync(buildFile, buildSource)
}
