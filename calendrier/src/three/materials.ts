import { CanvasTexture, MeshStandardMaterial, Vector4, type Texture } from 'three';

export const sparkleTime = { value: 0 };

/** Matériau de neige commun : blanc bleuté, scintillement selon le regard. */
export function createSnowMaterial(color = '#d3deec', prints?: { map: Texture; rect: Vector4 }): MeshStandardMaterial {
  const mat = new MeshStandardMaterial({ color, roughness: 0.88, metalness: 0 });
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = sparkleTime;
    if (prints) {
      shader.defines = { ...shader.defines, USE_PRINTS: '' };
      shader.uniforms.uPrints = { value: prints.map };
      shader.uniforms.uPrintRect = { value: prints.rect };
    }
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vSnowPos;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvSnowPos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        '#include <common>\nvarying vec3 vSnowPos;\nuniform float uTime;\n#ifdef USE_PRINTS\nuniform sampler2D uPrints;\nuniform vec4 uPrintRect;\n#endif\nfloat snowHash(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,37.719))) * 43758.5453); }',
      )
      .replace(
        '#include <color_fragment>',
        `#include <color_fragment>
        #ifdef USE_PRINTS
        // Empreintes : creux bleutés lus dans une texture posée sur le sol (rect = x, z, largeur, profondeur).
        vec2 printUv = (vSnowPos.xz - uPrintRect.xy) / uPrintRect.zw + 0.5;
        if (all(greaterThan(printUv, vec2(0.0))) && all(lessThan(printUv, vec2(1.0)))) {
          float print = texture2D(uPrints, printUv).a;
          diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.55, 0.64, 0.82), print * 0.75);
        }
        #endif`,
      )
      .replace(
        '#include <emissivemap_fragment>',
        `#include <emissivemap_fragment>
        vec3 cellP = floor(vSnowPos * 22.0);
        float h = snowHash(cellP);
        vec3 viewDirW = normalize(cameraPosition - vSnowPos);
        float facing = snowHash(cellP + floor(viewDirW * 6.0));
        float glint = step(0.993, h) * step(0.6, facing) * (0.6 + 0.4 * sin(uTime * 3.0 + h * 50.0));
        totalEmissiveRadiance += vec3(0.85, 0.92, 1.0) * glint * 1.6;`,
      );
  };
  return mat;
}

/** Empreintes de Sherlock : une piste qui sort de la forêt et s'arrête à sa place (point 0,0 de la texture = sa position). */
export function createFootprints(): { map: CanvasTexture; rect: Vector4 } {
  const size = 1024;
  const span = 16;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    const toPx = (x: number, z: number) => [(x / span + 0.5) * size, (z / span + 0.5) * size] as const;
    // Courbe : de l'arrière-gauche (forêt) jusqu'à Sherlock.
    const path = (t: number) => {
      const x = -7.5 * (1 - t) * (1 - t) - 1.5 * 2 * t * (1 - t);
      const z = -7.5 * (1 - t) * (1 - t) + 1.5 * 2 * t * (1 - t) - 0.6 * t;
      return [x, z] as const;
    };
    const steps = 30;
    for (let i = 0; i < steps; i++) {
      const t = i / steps;
      const [x, z] = path(t);
      const [x2, z2] = path(t + 0.01);
      const a = Math.atan2(z2 - z, x2 - x);
      const side = i % 2 ? 1 : -1;
      const ox = -Math.sin(a) * 0.22 * side;
      const oz = Math.cos(a) * 0.22 * side;
      const [px, pz] = toPx(x + ox, z + oz);
      ctx.save();
      ctx.translate(px, pz);
      ctx.rotate(a);
      const grad = ctx.createRadialGradient(0, 0, 2, 0, 0, 16);
      grad.addColorStop(0, 'rgba(0,0,0,0.9)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.scale(1.5, 1);
      ctx.beginPath();
      ctx.arc(0, 0, 14, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }
  const map = new CanvasTexture(canvas);
  return { map, rect: new Vector4(0, 0, span, span) };
}
