# Décisions

## 0. Le modèle à utiliser

La consigne laissait le chemin du modèle à compléter (`[CHEMIN_DU_MODELE]`). Le dépôt contient un modèle de base (`sherlock.glb`) et dix déclinaisons de saison. Aucun thème Noël n'existe encore (voir `saisons/REPRISE.md`).

**Décision : la pièce centrale est `saisons/sherlock-hiver.glb`**, Sherlock en tenue d'hiver (écharpe verte tricotée), avec ses deux animations propres au thème : il ramasse de la neige (`theme_objet`) et lance une boule de neige vers la caméra (`theme_special`). C'est la tenue la plus juste pour décembre et ses animations servent directement des surprises du calendrier.

Ce qu'il représente : Sherlock, la mascotte-détective de l'assistant d'ITHome, en pâte à modeler, casquette bleue et écharpe verte.

## 1. Analyse du modèle (`saisons/sherlock-hiver.glb`)

Inspection faite avec `@gltf-transform` (`scripts/inspect.mjs`).

| Propriété | Valeur |
|---|---|
| Format | glTF 2.0 binaire (`.glb`), sans extension |
| Poids | 1 612 008 octets |
| Géométrie | 1 maillage skinné, 16 primitives (une par matériau), **30 978 triangles** |
| Attributs | POSITION, NORMAL, TEXCOORD_0, COLOR_0 (ombres douces cuites), JOINTS_0, WEIGHTS_0 |
| Squelette | 1 skin, 32 os (30 de la base + `prop_boule`, `prop_neige`) |
| Matériaux | 16 PBR simples, non métalliques, rugosité 0,3 à 0,95 : pâte blanche, casquette bleue, couture, écharpe verte (texturée), bouche, langue, yeux, reflets, accessoires (marine, orange, jaune, gris, vert), neige (deux blancs) |
| Textures | 2 JPEG 256 × 256 : tricot couleur (4,8 Ko) et tricot normale (11 Ko) |
| Animations | **32** : 7 boucles (`repos`, `reflechit`, `enquete`, `parle`, `inquiet`, `dort`, `souleve`), 12 entrées/sorties, 8 réactions (`salut`, `reussite`, `alerte`, `desole`, `idee`, `ploc`, deux variantes de repos), 3 couches de visage (`cligne`, `yeux_fermes`, `bouche_parle`), 2 de thème (`theme_objet` 3,08 s, `theme_special` 2,79 s) |
| Échelle | Unités Blender (mètres) : environ 4,2 unités de haut, pieds à y = −0,23 |
| Orientation | Y vers le haut, Sherlock regarde vers +Z (glTF standard) |
| Pose de liaison | T-pose, accessoires visibles tant qu'aucune action de corps ne joue : `repos` est lancé dès le chargement |

**Optimisation** (`npm run optimize-model`) : dédoublonnage, rééchantillonnage des courbes, quantification (positions 14 bits, normales 10 bits) et compression **Meshopt**. Résultat : **573 564 octets** (−64 %). Aucune décimation : le maillage, les couleurs de sommets et les textures restent identiques. Le fichier optimisé est dans `public/models/` et chargé en différé derrière l'écran de chargement.

Toutes les animations sont utilisées par le calendrier (voir §4).

## 2. Direction artistique : « Veillée bleue en Savoie »

1. **Lieu et heure** : un replat de montagne à l'heure bleue, nuit tombée ; crêtes en silhouette dans la brume, sapins noyés de brouillard, une lune basse. Sherlock veille au pied d'un « sapin » fait de 24 boîtes empilées, l'étoile est la case 24.
2. **Palette** : encre de nuit `#0B1626` → bleu ardoise `#1D3250` pour le ciel et le brouillard ; neige `#EEF3F8` aux ombres bleutées `#8CA6C4` ; une seule chaleur, l'ambre des lanternes `#FFB45E` ; boîtes en canneberge `#8E2A36`, sapin `#2B5547` et crème `#E7DAC2` ; dorure des chiffres `#E8B964`.
3. **Lumière** : clair de lune froid et rasant qui porte les ombres douces, contre-jour ambre qui sort des cases ouvertes. Le chaud ne vient que des cases : ouvrir une case réchauffe l'image.
4. **Typographie** : Fraunces (serif à empattements doux, axe « SOFT ») pour les chiffres, titres et messages, Inter pour les libellés courts. Chiffres elzéviriens dorés, grandes capitales espacées pour les titres.
5. **Rythme** : lent et feutré au repos (neige, respiration de Sherlock, parallaxe), vif et rebondi à l'interaction (anticipation courte, détente en `back.out`, retombée en `elastic`/`expo.out`). Pas de mouvement linéaire, décalages en cascade de 30 à 80 ms.

## 3. Choix techniques

- **Projet** dans `calendrier/` pour ne pas mélanger l'application et les sources Blender du dépôt.
- **Versions** : three 0.187, React 19, R3F 9, drei 10, postprocessing 6 (via `@react-three/postprocessing`), GSAP 3, Vite 8. TypeScript est épinglé en 5.9 : `typescript-eslint` ne prend pas encore TypeScript 7.
- **Cases en instanciation** : les 24 caisses, portes, chiffres, poignées, intérieurs lumineux et chapeaux de neige sont six `InstancedMesh`. Les 24 cases coûtent six appels de dessin au lieu de plus d'une centaine. Les chiffres viennent d'un atlas dessiné en canevas avec Fraunces une fois la police chargée ; un attribut d'instance décale les UV.
- **Animations pilotées hors React** : GSAP anime des objets mutables (plan de caméra, état de chaque case, ambiance) que les composants lisent dans `useFrame`. Aucun rendu React par image.
- **Caméra** : pas d'`OrbitControls`. Un « plan » (position, cible, focale) animé par GSAP, plus un parallaxe borné à la souris ou au gyroscope, coupé en mouvement réduit.
- **Neige** : `Points` en shader, trois couches (loin, milieu, près) pour 7 000 flocons sur ordinateur, 3 500 sur mobile. Le vent est un champ qui change dans le temps (somme de sinus), les flocons proches sont gros et flous (disque à bord doux dont le flou dépend de la distance à la caméra). Accumulation : sol enneigé à congères, chapeaux de neige sur chaque case, butte sous le sapin, givre peint sur les portes.
- **Date** : l'année du calendrier est fixée à 2026 (le titre dit « Décembre 2026 »). La case *n* s'ouvre à partir du *n* décembre 2026 ; après le 24, tout reste ouvrable. `?date=AAAA-MM-JJ` simule la date, `?demo=1` déverrouille tout.
- **Persistance** : `localStorage`, clé `sherlock-avent-2026`. Les sessions `?demo=1` ou `?date=` utilisent une clé séparée (`…:essai`) pour ne pas salir le vrai calendrier ; un bouton « Tout refermer » apparaît dans ces modes.
- **Son** : pas de son. Une piste audio générée à la volée demanderait un geste d'activation et ajouterait un risque d'avertissement console pour un bénéfice faible.
- **Accessibilité** : 24 boutons réels, invisibles mais focalisables, sont positionnés sur la projection écran de chaque case. La navigation se fait au Tab et aux flèches (grille du sapin). Le focus est visible (anneau doré autour de la case et état survolé en 3D). La souris et le tactile passent par le lancer de rayon sur les instances.

## 4. Mise en scène et contenu

**Le sapin de cases.** Les 24 cases forment un sapin : un tronc de 3 cases, cinq étages de 6 à 2 cases posés sur des branches enneigées, et la case 24 en étoile dorée au sommet. Les numéros sont mélangés comme dans un calendrier traditionnel. Une guirlande d'ampoules ondule le long des branches.

**Sherlock est l'hôte, pas un décor.** Il suit la souris des yeux et de la tête, regarde la case survolée, sort sa loupe pendant l'anticipation de chaque ouverture, réagit à chaque surprise et se désole devant une case verrouillée. Les 32 animations du modèle sont réparties ainsi :

| Usage | Animations |
|---|---|
| Vie au repos | `repos`, `repos_variante_1/2`, `cligne` (toutes les 2 à 6 s) |
| Intro, sorties de surprise | `salut` |
| Anticipation d'une ouverture, énigmes, bonhomme de neige | `enquete_entree`, `enquete`, `enquete_sortie` (loupe) |
| Réactions | `reussite`, `alerte`, `idee` (ampoule, réponse d'énigme), `desole` (refus) |
| Message typographique | `parle_entree`, `parle`, `parle_sortie` |
| Aurore, ciel étoilé, final | `reflechit_entree`, `reflechit`, `reflechit_sortie` |
| Blizzard | `inquiet_entree`, `inquiet`, `inquiet_sortie` |
| Feu d'artifice, éclat du final | `souleve_entree`, `souleve`, `atterrit` |
| Case 3 | `theme_objet` (il ramasse de la neige) |
| Case 10 | `theme_special` (boule de neige lancée vers la caméra, qui s'écrase sur l'écran à 2,02 s, instant mesuré dans les clés de `prop_boule`), puis `ploc` et `desole` |
| Case 20 | `dort_entree`, `dort` (les « Z » du modèle), `dort_sortie` |

Les couches `yeux_fermes` et `bouche_parle` ne sont pas jouées seules : `cligne` suffit aux paupières, et `parle` porte déjà la bouche.

**Neuf types de surprises** sur les 24 cases (`src/content/days.ts`) :

| Type | Cases | Ce qui se passe |
|---|---|---|
| Message typographique | 1, 9, 17 | Trois lignes en Fraunces géante, lettres qui montent en cascade, filets dorés qui se tracent |
| Objet 3D | 2, 7, 11, 15, 19, 23 | Boule de Noël, sucre d'orge, flocon de glace, étoile en pain d'épices, cloche qui sonne (ondes dorées), chocolat chaud qui fume ; tous modélisés en code |
| Sherlock en action | 3, 10, 20 | Animations de thème, plan rapproché sur lui |
| Changement de ciel | 4, 12, 18 | Aurore boréale, blizzard (vent, brouillard blanc, caméra qui tremble), nuit étoilée avec étoile filante |
| Énigme | 5, 13, 22 | Question, bouton « Révéler la réponse », Sherlock passe de la loupe à l'ampoule |
| Petite scène | 6, 16 | Le train qui pose ses rails puis tourne autour du sapin en fumant ; le bonhomme de neige qui se construit seul |
| Lumières | 8, 21 | 40 lanternes de papier qui s'envolent (Fête des Lumières le 8, solstice le 21) |
| Feu d'artifice | 14 | Fusées et gerbes en quatre palettes, éclairs sur la scène |
| Final | 24 | Voir ci-dessous |

**Le final (case 24)**, 8 secondes : la scène s'éteint et la neige se fige en l'air ; une vague de lumière monte le sapin case par case jusqu'à l'étoile ; la case 24 se tasse et tremble ; éclat blanc, onde de choc qui repousse les flocons, aurore, toutes les portes s'ouvrent en cascade de l'étoile vers le tronc ; une grande étoile rayonnante sort de la case, feu d'artifice continu ; la caméra recule en grue ; « Joyeux Noël » arrive lettre par lettre.

**Ouverture d'une case**, en trois temps : anticipation (0 à 1 s : travelling, Sherlock sort sa loupe, la case se tasse puis frémit), action (porte sur une courbe à dépassement, détente de la case, gerbe de particules, éclat de lumière chaude, micro-secousse), retombée (rebond élastique, réaction de Sherlock, carte et typographie en cascade, caméra qui continue de respirer).

**Courbes** : quatre courbes dessinées avec `CustomEase` (`camera`, `door`, `settle`, `anticipate`) en plus de `back`, `elastic` et `expo` choisis par mouvement. Aucune interpolation linéaire.

## 5. Choix techniques ajoutés en cours de route

- **three 0.182 au lieu de 0.187** : R3F 9.8 crée un `THREE.Clock`, déprécié depuis three r183, ce qui affiche un avertissement console à chaque chargement. La 0.182 est la dernière sans cet avertissement.
- **`postprocessing` utilisé directement**, sans `@react-three/postprocessing` : ce dernier embarque n8ao et maath même inutilisés (+40 Ko gzip). Même chose pour le chargement du modèle : `GLTFLoader` et `MeshoptDecoder` de three plutôt que `useGLTF` de drei (qui tire three-stdlib). drei reste utilisé pour `useAnimations` et `useProgress`.
- **Découpage du JS** : la scène (R3F, postprocessing, composants 3D) est un chunk chargé derrière l'écran de chargement ; le final est un chunk à part. JS initial : environ 315 Ko gzip (React, GSAP, interface, three). Total : environ 410 Ko gzip.
- **ESLint** : configuration recommandée de `eslint-plugin-react-hooks` 7, sauf la règle `react-hooks/immutability` désactivée dans `src/three/` : elle interdit de muter des valeurs issues de hooks, alors que R3F mute par construction matériaux et uniformes dans `useFrame`.
- **Comptage du mode debug** : `renderer.info` est remis à zéro une fois par image (et non par passe), donc les chiffres incluent l'ombre, la scène et le post-traitement.
- **Captures** : Chromium headless avec SwiftShader (`--use-angle=swiftshader --enable-unsafe-swiftshader`) et horloge Playwright figée (`clock.install` + `pauseAt`, puis `fastForward` par pas) pour photographier des instants précis malgré 4 à 15 images par seconde. Quand `navigator.webdriver` est vrai, le lissage des à-coups de GSAP est coupé pour que la chronologie suive l'horloge pilotée.
- **Temps des animations longues** : lanternes et feu d'artifice suivent le temps écoulé réel ; les pas plafonnés à 50 ms ne servent qu'aux intégrations physiques (vent, neige), où un saut serait visible.
- **Tone mapping Neutral (Khronos PBR Neutral)** plutôt qu'AgX : AgX désaturait les hautes lumières, si bien que l'ambre des lanternes et des cases ouvertes virait au crème. Neutral garde la teinte des lumières chaudes et creuse la nuit.
- **Qualité réduite** sur écran tactile, petit écran ou processeur à 4 cœurs ou moins : DPR max 1,5 (2 sinon), ombres 1024 (2048), 3 500 flocons (7 000), pas de MSAA, forêt allégée.
