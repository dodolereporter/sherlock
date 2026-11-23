import { ExtrudeGeometry, Shape, type BufferGeometry } from 'three';

function starShape(outer: number, inner: number): Shape {
  const shape = new Shape();
  for (let i = 0; i < 10; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (i / 10) * Math.PI * 2 + Math.PI / 2;
    const x = Math.cos(a) * r;
    const y = Math.sin(a) * r;
    if (i === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  }
  shape.closePath();
  return shape;
}

export function starGeometry(outer = 0.5, inner = 0.22, depth = 0.14): BufferGeometry {
  const g = new ExtrudeGeometry(starShape(outer, inner), {
    depth,
    bevelEnabled: true,
    bevelThickness: 0.06,
    bevelSize: 0.05,
    bevelSegments: 3,
  });
  g.center();
  return g;
}
