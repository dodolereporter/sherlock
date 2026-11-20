# Sherlock 3D : modèle et animations

Sherlock en 3D temps réel pour le navigateur (three.js, `GLTFLoader`). Tout est produit par script dans Blender 5.3 ; rien n'est retouché à la main.

## Fichiers

| Fichier | Rôle |
|---|---|
| `sherlock.glb` | Le modèle, son squelette et les 30 animations. C'est le seul fichier à charger. |
| `animations.json` | Liste des animations : famille, type, durée, os animés. |
| `verification-animations.md` | Tableau OK / KO produit par `scripts/sherlock_check.py`. |
| `planches/planche-*.png` | Images 0, milieu et fin de chaque animation, par famille. |
| `comparaison-face-trois-quarts.png` | Référence 2D, modèle de face et de trois-quarts (pose neutre, 512 px). |
| `video/sherlock-presentation.mp4` | Vidéo de présentation (19 s, 1280 × 720). Le montage est dans `scripts/sherlock_presentation.py`. |
| `sherlock-repos.blend` | Scène Blender (une piste NLA par animation). |
| `reference-tpose.png` | Planche de référence (face, dos, profils, dessus, dessous). |
| `scripts/` | Scripts qui reconstruisent tout. |

## Squelette (30 os)

La pose de liaison est une T-pose. La pose neutre **N** est l'image 0 de `repos` (bras baissés).

| Os | Rôle |
|---|---|
| `root`, `body`, `head` | Racine, corps (écrasement et étirement), tête. L'origine de `head` est au centre de la tête. |
| `eye_L`, `eye_R` | Regard, piloté par le code : une rotation fait glisser l'œil sur le visage. Aucune animation ne les touche. |
| `eyelid_L`, `eyelid_R` | Portent l'œil. Échelle Z (hauteur) de 1 à 0,07 : clignement. Rotation autour de Y : yeux en biais. |
| `eye_happy_L`, `eye_happy_R` | Arcs des yeux fermés, rentrés sous la peau. Translation Y de 0,14 : visibles. Retournés de 180° autour de Y : yeux endormis. |
| `mouth` | Le sourire. Échelle Z négative : moue. |
| `mouth_open` | Bouche ouverte et langue, rentrées sous la peau. Translation Y de 0,14 : visibles ; échelles X et Z : forme. |
| `arm_L`, `arm_R`, `forearm_L`, `forearm_R` | Bras à deux os. Le coude peut s'éloigner de l'épaule : le bras s'étire comme de la pâte à modeler. |
| `leg_L`, `leg_R` | Jambes. |
| `hat_flap_L`, `hat_flap_R` | Rabats de la casquette. |
| `scarf_end_1`, `scarf_end_1_tip`, `scarf_end_2`, `scarf_end_2_tip` | Les deux pans de l'écharpe. |
| `prop_loupe`, `prop_exclamation`, `prop_ampoule`, `prop_coche`, `prop_z`, `prop_z_2`, `prop_z_3` | Accessoires. Échelle 0 : caché ; échelle 1 : visible. |

Trois os s'ajoutent aux 20 d'origine en plus des accessoires : `forearm_L`, `forearm_R` et `mouth_open`.

## Jouer les animations

- **États et réactions** : passer de l'une à l'autre par fondu (0,25 s). Chaque action de corps contient toute la pose du corps et met les accessoires à l'échelle 0 ; aucun accessoire ne reste donc affiché par erreur.
- **Entrées et sorties** : `<état>_entree` va de N à la première image de la boucle, `<état>_sortie` en revient. Pour `souleve`, la sortie s'appelle `atterrit`.
- **Couches** (`cligne`, `yeux_fermes`, `bouche_parle`) : à jouer **par-dessus** l'action en cours, sans fondu depuis elle. Elles ne contiennent que des os du visage ; si le code fait un fondu vers une couche seule, le corps retombe en T-pose et le personnage « saute ».
- `yeux_fermes` se termine yeux fermés : le code tient la dernière image, puis revient par fondu.
- Tant qu'aucune action de corps ne joue, les accessoires sont visibles (pose de liaison). Lancer `repos` dès le chargement.
- Les ombres douces sont cuites dans les couleurs de sommets (`COLOR_0`) : three.js les applique sans réglage.

## Reconstruire

Dans Blender, exécuter les scripts dans le même espace de noms, dans cet ordre :

```python
ns = {}
for f in ("sherlock_build.py", "sherlock_rig.py", "sherlock_anim.py"):
    exec(open(f, encoding="utf-8").read(), ns)
```

Puis `sherlock_export.py` (export du `.glb`), `sherlock_check.py` (vérification, Python pur, utilisable hors Blender), `sherlock_sheets.py` et `assembler-planches.ps1` (planches). Les rendus se lancent par `bpy.app.timers`, sinon le connecteur expire.

Les poses se règlent dans `sherlock_anim.py` : chaque image clé est une pose décrite en clair (cibles des mains, penché du corps, expression).
