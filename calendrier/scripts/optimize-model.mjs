// Optimise le modèle fourni (saisons/sherlock-hiver.glb) pour le web :
// dédoublonnage, rééchantillonnage des animations, quantification et compression Meshopt.
// L'apparence n'est pas modifiée (pas de décimation, textures conservées en 256 px).
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { dedup, prune, resample, quantize, meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import { mkdirSync, statSync } from 'node:fs';

const SRC = new URL('../../saisons/sherlock-hiver.glb', import.meta.url);
const OUT = new URL('../public/models/sherlock-hiver.glb', import.meta.url);

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });

const doc = await io.read(SRC.pathname);
await doc.transform(
  dedup(),
  resample({ tolerance: 1e-4 }),
  prune({ keepAttributes: true }),
  quantize({ quantizePosition: 14, quantizeNormal: 10, quantizeTexcoord: 12 }),
  meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
);
doc.createExtension(EXTMeshoptCompression).setRequired(true);
mkdirSync(new URL('../public/models/', import.meta.url), { recursive: true });
await io.write(OUT.pathname, doc);
console.log(`${statSync(SRC).size} -> ${statSync(OUT).size} octets`);
