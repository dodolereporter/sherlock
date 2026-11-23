# Le calendrier de Sherlock

Calendrier de l'Avent interactif en 3D : Sherlock, la mascotte du dépôt, veille au pied d'un sapin fait de 24 cases, dans une nuit de neige en Savoie. Chaque soir de décembre 2026, une case s'ouvre sur une surprise différente ; la case 24 déclenche le grand final.

Le modèle animé est `../saisons/sherlock-hiver.glb` (version optimisée dans `public/models/`). Tout le reste (décor, cases, neige, objets, textures) est généré en code.

## Lancer

```bash
npm install
```

```bash
npm run dev
```

Puis ouvrir l'adresse affichée par Vite (par défaut http://localhost:5173).

Autres commandes :

| Commande | Rôle |
|---|---|
| `npm run build` | Typecheck puis build de production dans `dist/` (site statique, chemins relatifs) |
| `npm run preview` | Sert `dist/` sur http://localhost:4173 |
| `npm run lint` | ESLint, zéro avertissement toléré |
| `npm run typecheck` | TypeScript strict |
| `npm run optimize-model` | Régénère `public/models/sherlock-hiver.glb` depuis `../saisons/sherlock-hiver.glb` (Meshopt) |
| `npm run check` | Contrôle fonctionnel Playwright : clavier, persistance après rechargement, repli sans WebGL (après `npm run preview`) |
| `npm run captures` | Captures de contrôle Playwright dans `captures/` (lancer `npm run preview` avant). `-- --extra` ajoute une capture par type de surprise |

## Paramètres d'URL

| Paramètre | Effet |
|---|---|
| `?date=2026-12-14` | Simule la date du jour : les cases 1 à 14 sont ouvrables |
| `?demo=1` | Déverrouille les 24 cases |
| `?debug=1` | Affiche FPS, appels de dessin, triangles, géométries et textures |
| `?intro=0` | Passe directement l'introduction |

Les paramètres se combinent (`?demo=1&debug=1`). En mode `demo` ou `date`, les cases ouvertes sont mémorisées sous une clé séparée et un bouton « Tout refermer » apparaît.

## Utilisation

- Cliquer ou toucher une case. Avant sa date, elle tremble, refuse, et un message dit combien de jours attendre.
- Clavier : `Tab` pour entrer dans le sapin, flèches pour se déplacer de case en case, `Entrée` pour ouvrir, `Échap` pour refermer ou passer l'introduction.
- Les cases ouvertes restent ouvertes (localStorage) ; les rouvrir rejoue leur surprise.
- `prefers-reduced-motion` : introduction en fondu, caméra sans parallaxe ni secousse, neige ralentie, surprises jouées en fondus. Tout le contenu reste accessible.

## Structure

```
src/
  main.tsx              Démarrage, test WebGL 2, message de repli
  App.tsx               Couches d'interface, chargement différé de la scène
  Stage.tsx             Canvas R3F (chunk séparé, chargé derrière l'écran de chargement)
  director.ts           Mise en scène GSAP : intro, survol, refus, ouverture, fermeture, courbes
  finale.ts             Séquence de la case 24 (chargée à la demande)
  store.ts              État applicatif (zustand) : phase, cases ouvertes, case active
  content/days.ts       Les 24 contenus et leurs 9 types de surprise
  lib/                  Paramètres d'URL, dates, persistance, qualité par appareil
  three/
    Experience.tsx      Lumières, brouillard, reflets procéduraux, assemblage de la scène
    Sherlock.tsx        Modèle, mixeur d'animations, regard (tête et yeux) piloté par le code
    AdventTree.tsx      Les 24 cases en instanciation (caisses, portes, chiffres, neige, guirlande)
    Snow.tsx            Neige en shader : 3 plans, vent variable, flou de proximité, onde de choc
    Sky.tsx             Ciel en shader : dégradé, étoiles, lune, aurore, étoile filante
    Landscape.tsx       Sol à congères, butte, crêtes, forêt instanciée, lanternes
    Effects.tsx         Post-traitement (postprocessing) : bloom, AgX, vignettage, grain
    CameraRig.tsx       Caméra mise en scène + parallaxe souris/gyroscope
    surprises/          Objets 3D, train, bonhomme de neige, lanternes, feu d'artifice, étoile finale
  ui/                   Chargement, titre d'intro, HUD, carte, messages, effets d'écran, boutons accessibles
scripts/
  optimize-model.mjs    Optimisation du modèle
  inspect.mjs           Inspection d'un .glb
  captures.mjs          Captures Playwright à horloge pilotée
  checks.mjs            Contrôle fonctionnel scripté
captures/               Captures finales
```

Voir `DECISIONS.md` pour l'analyse du modèle et les choix, `ITERATIONS.md` pour le journal de mise au point.
