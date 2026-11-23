# Journal des itérations

Méthode : `npm run build`, `npm run lint`, `npm run typecheck`, puis `npm run captures` (Playwright, Chromium en rendu logiciel SwiftShader, horloge pilotée pour figer les instants). Les FPS mesurés en rendu logiciel (4 à 17) ne sont pas significatifs ; la performance est jugée sur les appels de dessin, les triangles et le poids du JS. Les appels de dessin et triangles comptent **toute l'image** : passe d'ombre, scène et post-traitement.

Barème : DA 20 · 3D et modèle 20 · Motion 20 · Neige et ambiance 10 · Calendrier 15 · Performance 10 · Code, accessibilité, responsive 5.

## Itération 1

Build, lint (0 avertissement), typecheck : OK. Console : aucune erreur ni avertissement (hors messages du pilote SwiftShader liés aux captures).

Mesures (`?debug=1`, 1440 × 900) : vue principale 83 appels / 224 841 triangles ; case ouverte 85 / 231 497 ; final 85 / 224 999. JS : initial 315 Ko gzip (index + three), total 410 Ko gzip (scène 3D chargée à part derrière l'écran de chargement). Modèle 574 Ko.

| Critère | Note | Justification (captures) |
|---|---|---|
| Direction artistique | 14/20 | Palette nuit bleue + ambre tenue (`1440-03`), typographie Fraunces élégante (`1440-01`). Mais intérieurs des cases ouvertes beiges et ternes (`1440-06`), butte d'aspect sableux sur mobile (`390-03`). |
| 3D et modèle | 13/20 | Sherlock entier, éclairé, animé, regard vivant (`1440-03`). Le plan rapproché d'ouverture le sort du cadre sur ordinateur (`1440-06`). |
| Motion design | 12/20 | Intro grue + titre en cascade réussie (`1440-01`, `1440-02`). Flash d'ouverture qui brûle toute l'image (`1440-05`), survol trop discret (`1440-04`), titre « Joyeux Noël » invisible (`1440-09`). |
| Neige et ambiance | 7/10 | Trois plans, flous proches, chapeaux de neige sur les cases (`1440-03`). Sol encore uniforme. |
| Calendrier | 11/15 | Ouverture, persistance (compteur 1/24 puis 2/24), final OK. Le refus d'une case verrouillée ne se déclenche pas avec `?intro=0` (`1440-12`, `390-12` : aucun message). |
| Performance | 8/10 | Budgets tenus (85 appels, 231 k triangles, 315 Ko initial). Total JS 410 Ko : au-dessus de 400 si l'on compte le chunk différé. |
| Code, a11y, responsive | 4/5 | Focus visible au clavier (`390-04`), libellés, mobile lisible. |
| **Total** | **69/100** | |

Défauts les plus visibles, du plus grave au moins grave :
1. Écran de chargement qui capte encore les clics pendant son ouverture (avec `?intro=0`, les premiers clics sont perdus).
2. Titre du final invisible (dégradé `background-clip` cassé par le découpage en lettres).
3. Flash d'ouverture surexposé (lumière 46 + bloom × 0,7).
4. Intérieur des cases ouvertes terne : la boîte lumineuse intérieure était au même endroit que les parois (z-fighting).
5. Plan rapproché d'ouverture sans Sherlock ; survol peu lisible.

Corrections :
1. `pointer-events: none` sur le chargement dès que le masque s'ouvre.
2. Titre du final en or plein avec halo par `text-shadow`, voile sombre derrière le texte.
3. Pic de lumière 46 → 26, flash 0,7 → 0,35.
4. Boîte intérieure réduite de 2 cm : elle passe devant les parois et rayonne.
5. Nouveau calcul du plan rapproché (Sherlock + case dans la partie libre de l'écran) ; survol : avancée ×1,7, porte entrouverte, chiffre lumineux, lueur chaude portée sur la case. Lanternes mobiles déplacées devant Sherlock.

## Itération 2

Build, lint, typecheck : OK. Console : aucune erreur ni avertissement sur les 41 captures (`captures/rapport.json`).

Mesures : 1440 principale 83 appels / 224 841 triangles ; ouverte 86 / 231 529 ; final 85 / 224 999. 390 : 83 / 224 841, 83 / 231 461, 85 / 224 999. JS inchangé (315 Ko initial, 410 Ko total).

| Critère | Note | Justification |
|---|---|---|
| Direction artistique | 16/20 | Ouverture lisible et chaude, aurore superbe en mouvement réduit (`1440-11`). Mais les cases ouvertes deviennent des carrés blancs surexposés quand plusieurs sont ouvertes (`extra-case-15`, `extra-case-23`), le titre du final recouvre Sherlock et le sapin (`1440-09`). |
| 3D et modèle | 15/20 | Sherlock à la loupe pendant l'anticipation (`1440-05`), sieste avec ses « Z » (`extra-case-20`), lancer de boule (`extra-case-10`). Coupé au bord gauche dans le plan d'ouverture (`1440-06`). |
| Motion design | 15/20 | Flash dosé, survol lisible avec la lueur chaude (`1440-04`), refus avec message (`1440-12`). Lanternes et feu d'artifice absents des captures. |
| Neige et ambiance | 7/10 | Inchangé ; blizzard peu spectaculaire (`extra-case-12`). |
| Calendrier | 12/15 | Refus réparé. Trois surprises ne se voient pas : lanternes (`extra-case-08`), feu d'artifice (`extra-case-14`), bonhomme de neige caché par la carte (`extra-case-16`). Objets trop petits pour les cases hautes (`extra-case-23`). |
| Performance | 8/10 | Budgets tenus. |
| Code, a11y, responsive | 4/5 | Message typographique trop large à 1000 px, il passe sous la carte. |
| **Total** | **77/100** | |

Défauts :
1. Lanternes et feu d'artifice invisibles : leur horloge avançait par pas plafonnés à 50 ms, donc au ralenti dès que la cadence baisse (1,45 s simulée pour 9 s réelles en rendu logiciel) ; le feu s'arrêtait en plus après 11 fusées.
2. Bonhomme de neige placé derrière la carte.
3. Mur de cases ouvertes surexposé.
4. Titre du final sur le sujet.
5. Objets trop petits ; Sherlock coupé dans le plan d'ouverture ; message typographique trop large.

Corrections :
1. Lanternes et feu sur le temps réel écoulé ; feu en salve puis cadence posée tant que la case reste ouverte ; lanternes sans brouillard, couleur d'instance créée au montage, 45 % plus grandes.
2. Bonhomme de neige devant le sapin, entre Sherlock et le tronc.
3. Intérieurs : braises douces pour les cases déjà ouvertes, foyer vif seulement pour la case active.
4. Final : typographie dans une colonne à droite (en bas sur mobile), caméra décalée pour garder le sapin et Sherlock à gauche.
5. Objets × 1,4 à 1,6 ; plan d'ouverture recalé (marge gauche, décalage réduit) ; message typographique plafonné à 56 vw. Ajout : neige qui s'accumule lentement sur la casquette de Sherlock.

## Itération 3

Build, lint, typecheck : OK. Console : vide sur 41 captures.

Mesures : 1440 principale 85 appels / 225 753 triangles ; ouverte 90 / 232 477 ; final 87 / 225 911. 390 : 85 / 225 753, 85 / 232 373, 87 / 225 911. JS : 315 Ko initial, 410 Ko total.

| Critère | Note | Justification |
|---|---|---|
| Direction artistique | 17/20 | Final enfin composé : sapin et Sherlock à gauche, « Joyeux Noël » doré à droite, aurore (`1440-09`). Cases ouvertes en braises au lieu de carrés blancs (`extra-case-15`). Reste : butte orangée sur mobile (`390-03`), lanternes pâles (`extra-case-08`). |
| 3D et modèle | 16/20 | Sherlock dans tous les plans d'ouverture (`1440-06`), neige sur la casquette, bonhomme de neige à côté de lui (`extra-case-16`). Plan d'ouverture trop large : la case est petite (`1440-06`). |
| Motion design | 16/20 | Séquences complètes, cascade et éclat du final (`1440-08`). Le feu d'artifice reste un petit nuage derrière le sapin (`extra-case-14`). |
| Neige et ambiance | 7/10 | Blizzard qui assombrit tout au lieu de blanchir (`extra-case-12`). |
| Calendrier | 13/15 | 9 types visibles sauf le feu d'artifice, trop discret. Persistance et refus OK (`1440-12`). |
| Performance | 8/10 | 85 à 90 appels, 232 k triangles max. |
| Code, a11y, responsive | 4/5 | Message typographique tenu dans sa colonne (`extra-case-01`, ici la case 9 à cause du minutage de la capture). |
| **Total** | **81/100** | |

Défauts :
1. Feu d'artifice minuscule : fusées à 45 unités de la caméra, gerbes de 3 unités, particules de 0,2 unité.
2. Blizzard sombre et boueux : le brouillard bleu nuit s'épaissit.
3. Lanternes pâles, butte orangée sur mobile (lanternes trop proches).
4. Plan d'ouverture trop large pour les cases hautes ; objets petits.
5. Capture « extra » : premier clic trop tôt après le chargement (la projection des cases n'était pas encore à jour).

Corrections :
1. Feu d'artifice rapproché (z −5 à −9), gerbes de rayon ×1,5, particules ×2, éclat blanc au cœur, traînées visibles.
2. Le brouillard blanchit vers un gris bleuté pendant le blizzard.
3. Lanternes de papier orangées ; lanternes mobiles à demi-intensité.
4. Plan d'ouverture resserré (Sherlock cadré à mi-jambe) ; les objets grandissent avec la hauteur de la case. Empreintes de Sherlock dans la neige, de la forêt jusqu'à sa place.
5. Le script de captures attend 0,8 s après le passage en vue principale.

## Itération 4

Build, lint, typecheck : OK. Console : vide (`captures/rapport.json`).

Mesures : 1440 principale 85 appels / 225 753 triangles ; ouverte 90 / 232 477 ; final 87 / 225 911. 390 identiques à ±5 appels. JS : 315 Ko initial, 410 Ko total.

| Critère | Note | Justification |
|---|---|---|
| Direction artistique | 17/20 | Butte mobile redevenue neige (`390-03`), final équilibré avec feu d'artifice (`1440-09`). Les lumières chaudes sortent crème (lanternes `extra-case-08`, intérieurs) : l'ambre de la palette se perd. |
| 3D et modèle | 17/20 | Sherlock présent dans chaque surprise ; plan d'ouverture resserré sur la case et lui (`1440-05`). Encore légèrement coupé à gauche après le travelling (`1440-06`). |
| Motion design | 17/20 | Feu d'artifice lisible (`extra-case-14`, `1440-09`), étoile filante (`extra-case-18`), lanternes qui montent. |
| Neige et ambiance | 8/10 | Empreintes, neige sur la casquette, blizzard qui blanchit (`extra-case-12`)… jusqu'au voile total où l'on ne voit plus Sherlock. |
| Calendrier | 14/15 | Les 9 types se voient tous dans les captures `extra-case-*` ; la case 1 s'ouvre bien sur son message (`extra-case-01`). |
| Performance | 8/10 | Budgets tenus. |
| Code, a11y, responsive | 4/5 | Final mobile : le texte couvre Sherlock (`390-09`). |
| **Total** | **85/100** | |

Défauts :
1. Tone mapping AgX : l'ambre vire au crème, la nuit manque de profondeur.
2. Blizzard en voile blanc total.
3. Final mobile : la typographie masque Sherlock.
4. Sherlock coupé au bord gauche en fin de travelling d'ouverture.
5. Sherlock un peu sombre dans la vue principale une fois la nuit creusée.

Corrections :
1. Tone mapping Neutral (Khronos) : ambre saturé, lanternes orangées, nuit plus dense.
2. Blizzard : brouillard 0,026 au lieu de 0,04, blanchiment à 60 %.
3. Final mobile : typographie en haut, sous le compteur.
4. Marge gauche du plan d'ouverture élargie.
5. Ciel et lune +15 %.

## Itération 5

Build, lint, typecheck : OK. Console : vide sur 41 captures.

Mesures : 1440 principale 85 appels / 225 753 triangles ; ouverte 90 / 232 477 ; final 87 / 225 911 ; 390 : 85 / 225 753, 85 / 232 373, 87 / 225 911. JS : 315 Ko initial, 410 Ko total.

| Critère | Note | Justification |
|---|---|---|
| Direction artistique | 18/20 | Nuit profonde, ambre saturé, cases en canneberge et sapin lisibles (`1440-03`) ; final et aurore très tenus (`1440-09`, `1440-11`). Final mobile : la typographie cache l'étoile (`390-09`). |
| 3D et modèle | 18/20 | Sherlock entier dans le plan d'ouverture (`1440-06`), loupe en anticipation (`1440-05`, `390-05`), sieste, lancer, ramassage. |
| Motion design | 18/20 | Intro, ouverture en trois temps, refus, final en cascade tous lisibles. |
| Neige et ambiance | 9/10 | Blizzard qui blanchit sans tout masquer (`extra-case-12`), empreintes (`extra-case-16`), neige sur la casquette, scintillement du sol. |
| Calendrier | 14/15 | Lanternes encore au sol à l'instant capturé (`extra-case-08`). |
| Performance | 8/10 | Budgets tenus ; total JS 410 Ko dont 95 Ko chargés en différé. |
| Code, a11y, responsive | 4/5 | Final mobile à revoir. |
| **Total** | **89/100** | |

Défauts :
1. Final mobile : texte sur l'étoile.
2. Lanternes qui partent trop tard et trop bas (délais jusqu'à 4,5 s).
3. Rien d'autre de bloquant ; quelques détails : train petit dans le plan large (`extra-case-06`).

Corrections :
1. Final mobile : texte compact en bas, caméra qui remonte la scène au-dessus.
2. Lanternes : départs en 2,6 s max, depuis 1 m, devant le sapin, plus rapides.

## Itération 6

Build, lint, typecheck : OK. Console : vide sur 41 captures et sur le contrôle fonctionnel.

Mesures : identiques à l'itération 5 (85 à 90 appels, 232 477 triangles au maximum). JS : 315 Ko initial, 410 Ko total.

Contrôle fonctionnel scripté (Playwright, `?date=2026-12-05`) : Tab amène le focus sur « Case 3 : ouvrir » ; flèche haut → « Case 15, verrouillée jusqu'au 15 décembre » ; Entrée ouvre la case 3 ; Échap referme et rend le focus à « Case 3, déjà ouverte : revoir la surprise » ; `localStorage` contient `[3]` ; après rechargement le compteur affiche 1/24. Chromium lancé avec WebGL désactivé : message de repli affiché (`captures/sans-webgl.png`).

| Critère | Note | Justification |
|---|---|---|
| Direction artistique | 18/20 | Tenue partout, y compris en mouvement réduit (`390-11`) et sans WebGL. Lanternes encore un peu plates (`extra-case-08`). |
| 3D et modèle | 18/20 | Final mobile : Sherlock au centre sous l'étoile (`390-09`). Le modèle n'a pas de matériaux à reflets : il reste mat, fidèle à la pâte à modeler. |
| Motion design | 18/20 | Toutes les séquences lisibles ; l'intro reste un mouvement de grue unique, sans second temps fort. |
| Neige et ambiance | 9/10 | Inchangé. |
| Calendrier | 15/15 | 9 types de surprises visibles (`extra-case-*`), dates, refus, persistance et clavier vérifiés. |
| Performance | 9/10 | 90 appels (< 150), 232 k triangles (< 500 k), 315 Ko de JS initial (< 400), modèle de 574 Ko en différé, DPR plafonné, qualité réduite sur mobile. Un point retenu : FPS jamais mesuré sur un vrai GPU. |
| Code, a11y, responsive | 5/5 | Clavier, focus, libellés, repli WebGL, 390 et 1440 propres. |
| **Total** | **92/100** | |

Défauts restants (mineurs) :
1. Lanternes en aplats jaunes.
2. Train petit dans son plan.
3. Total JS (410 Ko) au-dessus de 400 si l'on compte les chunks différés.

Correction :
1. Lanternes : dégradé vertical (papier plus clair près de la flamme), taille réduite.

## Itération 7

Build, lint, typecheck : OK (code formaté avec Prettier). Console : vide sur les 41 captures et le contrôle fonctionnel (`npm run check`, résultats identiques à l'itération 6).

Mesures : 1440 principale 85 appels / 225 753 triangles ; ouverte 90 / 232 477 ; final 87 / 225 911. 390 : 85 / 225 753, 85 / 232 373, 87 / 225 911. JS : 315 Ko gzip initial (index 113 + three 202), 410 Ko gzip au total.

| Critère | Note | Justification |
|---|---|---|
| Direction artistique | 18/20 | Lanternes orangées dégradées, plus de carrés plats (`extra-case-08`). Cohérence de l'intro (`1440-02`) au final (`1440-09`). Le sol reste peu modelé près du sapin. |
| 3D et modèle | 18/20 | Sherlock au centre de chaque séquence (`1440-05`, `390-05`, `390-09`). |
| Motion design | 18/20 | Intro, ouvertures, refus, final : chaîne complète et lisible à chaque instant capturé. |
| Neige et ambiance | 9/10 | Trois plans, flou proche, vent, accumulation (chapeaux, casquette, empreintes, scintillement). |
| Calendrier | 15/15 | Dates, refus, démo, persistance, 9 types de surprise, final distinct. |
| Performance | 9/10 | Budgets tenus avec marge. |
| Code, a11y, responsive | 5/5 | Clavier, focus, libellés, repli WebGL, mouvement réduit, 390 et 1440. |
| **Total** | **92/100** | |

Deuxième itération consécutive à 90 ou plus, aucun critère bloquant en échec : arrêt de la boucle.

## Rapport final

| Critère | Note |
|---|---|
| Direction artistique et cohérence visuelle | 18/20 |
| Qualité 3D et mise en valeur du modèle | 18/20 |
| Motion design | 18/20 |
| Neige et ambiance | 9/10 |
| Fonctionnement du calendrier | 15/15 |
| Performance et budgets | 9/10 |
| Code, accessibilité, responsive | 5/5 |
| **Total** | **92/100** |

Progression : 69 → 77 → 81 → 85 → 89 → 92 → 92, en 7 itérations.

Ce qui reste imparfait :
- **Aucune mesure sur un vrai GPU.** Toutes les captures sont faites en rendu logiciel (4 à 17 images/s) ; la fluidité réelle, surtout sur mobile, n'a pas été vérifiée.
- **Poids total du JS : 410 Ko gzip**, au-dessus de 400 si l'on compte les chunks chargés après l'écran de chargement (le JS initial, lui, fait 315 Ko). three.js pèse à lui seul 202 Ko, car R3F l'importe en entier.
- **Le train** reste petit dans son plan large ; **le sol** près du sapin est peu modelé (congères surtout au loin).
- **Pas de son**, par choix (voir `DECISIONS.md`).
- **Le gyroscope** n'est pas testé sur appareil réel ; sur iOS, il ne répond que si le navigateur l'autorise sans demande explicite.
- Les captures sont prises avec `?debug=1`, d'où le panneau de mesures en bas à gauche.
