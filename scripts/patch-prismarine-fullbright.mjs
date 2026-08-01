import { readFileSync, writeFileSync, copyFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

const replacements = [
  // --- Minecraft 1.19.4 support -------------------------------------------
  // prismarine-viewer only ships assets for exact versions; a 1.19.4 server
  // otherwise falls back to the 1.19 block-state registry, which mis-parses
  // 1.19.4 chunk data (wrong textures everywhere, e.g. grass rendered as
  // fire). Registering 1.19.4 makes the browser worker parse chunks with the
  // correct registry; the 1.19 atlas/blocksStates are aliased below because
  // model lookup is by block name.
  {
    file: "node_modules/prismarine-viewer/viewer/lib/version.js",
    from: "'1.18.1', '1.19', '1.20.1'",
    to: "'1.18.1', '1.19', '1.19.4', '1.20.1'",
  },
  {
    file: "node_modules/prismarine-viewer/public/index.js",
    from: '"1.18.1","1.19","1.20.1"',
    to: '"1.18.1","1.19","1.19.4","1.20.1"',
  },
  // --- Bright shaded rendering --------------------------------------------
  // Earlier revisions removed AO, directional water tint, and Lambert
  // materials. That made caves bright but erased the visual distinction
  // between adjacent faces. Restore those depth cues; browserCapture boosts
  // ambient light separately so underground scenes remain readable.
  {
    file: "node_modules/prismarine-viewer/viewer/lib/models.js",
    from: `    if (water) {
      tint = tints.water[biome]
    }`,
    to: `    if (water) {
      let m = 1 // Fake lighting to improve lisibility
      if (Math.abs(dir[0]) > 0) m = 0.6
      else if (Math.abs(dir[2]) > 0) m = 0.8
      tint = tints.water[biome]
      tint = [tint[0] * m, tint[1] * m, tint[2] * m]
    }`,
  },
  {
    file: "node_modules/prismarine-viewer/viewer/lib/models.js",
    from: "        light = 1",
    to: "        light = (ao + 1) / 4",
  },
  {
    file: "node_modules/prismarine-viewer/viewer/lib/worldrenderer.js",
    from: "    this.material = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, alphaTest: 0.1 })",
    to: "    this.material = new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, alphaTest: 0.1 })",
  },
  {
    file: "node_modules/prismarine-viewer/viewer/lib/entity/Entity.js",
    from: "  const material = new THREE.MeshBasicMaterial({ transparent: true, skinning: true, alphaTest: 0.1 })",
    to: "  const material = new THREE.MeshLambertMaterial({ transparent: true, skinning: true, alphaTest: 0.1 })",
  },
  {
    file: "node_modules/prismarine-viewer/public/worker.js",
    from: "if(s){v=l.water[i]}",
    to: "if(s){let e=1;Math.abs(p[0])>0?e=.6:Math.abs(p[2])>0&&(e=.8),v=l.water[i],v=[v[0]*e,v[1]*e,v[2]*e]}",
  },
  {
    file: "node_modules/prismarine-viewer/public/worker.js",
    from: "m=v&&d?0:3-(v+d+b);y=1,R.push(m)}s.colors.push(W[0]*y,W[1]*y,W[2]*y)}",
    to: "m=v&&d?0:3-(v+d+b);y=(m+1)/4,R.push(m)}s.colors.push(W[0]*y,W[1]*y,W[2]*y)}",
  },
  {
    file: "node_modules/prismarine-viewer/public/index.js",
    from: "new THREE.MeshBasicMaterial({transparent:!0,skinning:!0,alphaTest:.1})",
    to: "new THREE.MeshLambertMaterial({transparent:!0,skinning:!0,alphaTest:.1})",
  },
  {
    file: "node_modules/prismarine-viewer/public/index.js",
    from: "new n.MeshBasicMaterial({vertexColors:!0,transparent:!0,alphaTest:.1})",
    to: "new n.MeshLambertMaterial({vertexColors:!0,transparent:!0,alphaTest:.1})",
  },
];

for (const replacement of replacements) {
  const path = join(root, replacement.file);
  const text = readFileSync(path, "utf8");

  if (text.includes(replacement.to) && !text.includes(replacement.from)) {
    continue;
  }

  const count = text.split(replacement.from).length - 1;
  if (count !== 1) {
    throw new Error(`${replacement.file}: expected one viewer patch target, found ${count}`);
  }

  writeFileSync(path, text.replace(replacement.from, replacement.to));
  console.log(`prismarine viewer patched ${replacement.file}`);
}

// Alias 1.19 viewer assets for 1.19.4. Block models are looked up by block
// name, so the 1.19 atlas renders a 1.19.4 world correctly; blocks added in
// 1.19.3/1.19.4 fall back to the missing texture.
const assetAliases = [
  ["node_modules/prismarine-viewer/public/textures/1.19.png", "node_modules/prismarine-viewer/public/textures/1.19.4.png"],
  ["node_modules/prismarine-viewer/public/blocksStates/1.19.json", "node_modules/prismarine-viewer/public/blocksStates/1.19.4.json"],
];

for (const [source, target] of assetAliases) {
  const sourcePath = join(root, source);
  const targetPath = join(root, target);
  if (!existsSync(targetPath)) {
    copyFileSync(sourcePath, targetPath);
    console.log(`aliased ${source} -> ${target}`);
  }
}
