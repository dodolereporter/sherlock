import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { getBounds } from '@gltf-transform/functions';
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(process.argv[2]);
const root = doc.getRoot();
let tris = 0;
for (const mesh of root.listMeshes()) {
  for (const p of mesh.listPrimitives()) {
    const idx = p.getIndices();
    const pos = p.getAttribute('POSITION');
    const t = idx ? idx.getCount() / 3 : pos.getCount() / 3;
    tris += t;
    console.log('mesh', mesh.getName(), 'tris', t, 'attrs', p.listSemantics().join(','), 'mat', p.getMaterial()?.getName());
  }
}
console.log('total tris', tris);
console.log('nodes', root.listNodes().length, 'skins', root.listSkins().length, 'anims', root.listAnimations().length);
for (const m of root.listMaterials())
  console.log(
    'material',
    m.getName(),
    m
      .getBaseColorFactor()
      .map((v) => v.toFixed(2))
      .join(','),
    'rough',
    m.getRoughnessFactor(),
    'metal',
    m.getMetallicFactor(),
    'tex',
    !!m.getBaseColorTexture(),
    'ext',
    m.listExtensions().map((e) => e.extensionName),
  );
for (const t of root.listTextures()) console.log('texture', t.getName(), t.getMimeType(), t.getSize(), t.getImage()?.byteLength);
console.log(
  'extensions',
  root.listExtensionsUsed().map((e) => e.extensionName),
);
console.log('scene bounds', JSON.stringify(getBounds(root.listScenes()[0])));
for (const n of root.listNodes()) if (!n.getSkin() && n.getMesh()) console.log('node', n.getName(), n.getTranslation(), n.getScale());
console.log(
  'anim names',
  root
    .listAnimations()
    .map((a) => a.getName())
    .join(' '),
);
for (const n of root.listNodes()) if (n.getName().startsWith('prop_')) console.log('prop bone', n.getName());
