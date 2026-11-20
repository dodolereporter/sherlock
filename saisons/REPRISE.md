# Sherlock, saisons et fêtes : où on en est (pause du 20/11/2026)

Tout se fait en direct dans le Blender ouvert, par le connecteur MCP. Rien n'est commité.

## Ce qui est fait

- **Accessoires refaits** d'après les images de référence (`references/`) : masque vénitien à manche, couronne à pierres, plumes, toque, oreilles de lapin, chapeau de sorcière, etc. Formes dans `scripts/sherlock_saisons.py` (partie haute).
- **Vert de l'écharpe** (`#85C595`) pour les accessoires de saison : bottes, gilet, monture des lunettes.
- **Prise des objets** : l'objet a son origine au point de prise, ce point est au centre du poing, et l'objet suit l'avant-bras. Règle : seul un manche fin traverse le poing, tout ce qui est large commence au-dessus. Les objets portés à deux mains sont calés entre les poings (table `PORTE`).
- **Planches de validation** à jour : `planche-fetes-1..3.png`, `planche-saisons.png` (images dans `images/`).
- **Animation « souleve »** refaite (panique : bras en moulinets, pieds qui battent, bouche qui crie). Elle est dans `../sherlock.glb`, vérifié conforme (30 os, 30 animations). L'ancienne version est dans `../sauvegarde-avant-20-11/`.
- **Fichiers par thème** (`sherlock-<thème>.glb` + `.json`, tous vérifiés conformes) : printemps, ete, automne, hiver, nouvel_an, epiphanie, chandeleur, saint_valentin, mardi_gras, paques.

## Ce qui reste

1. **Thèmes à produire** : musique, quatorze_juillet, halloween, noel, et **premier_mai à refaire** (son fichier date d'avant la correction du muguet qui traversait la main).
2. **Verre de la loupe** (effet grossissant) : la lentille est écrite dans `sherlock_build.py` mais **désactivée** (`LOUPE_VERRE = False`).
   - Le `.glb` exporté porte bien les extensions de verre (`KHR_materials_transmission`, `_ior`, `_volume`), que three.js sait rendre.
   - Dans Eevee la lentille sort **blanche** : la réfraction ne trouve pas le visage derrière, quels que soient le mode (SLAB, SPHERE), l'épaisseur (0 à 0,4) et l'indice. Cause non trouvée.
   - Pas encore testé dans three.js. Piste de secours : grossir l'œil (os `eyelid_R`) quand la loupe passe devant.
3. **Contrôle image par image** des animations de thème (images dans `images-animations/`), puis **vidéo de contrôle** (`scripts/video-themes.ps1`, `scripts/direct/job_video.py`).
4. **Notice d'intégration** : calendrier des périodes, noms des clips (`theme_objet`, `theme_special`), os `prop_*` par thème, poids des fichiers (1,6 à 2,0 Mo). La boule de neige part droit devant : c'est le code du site qui tourne Sherlock vers la souris.
5. **À rafraîchir** : `../planches/` (l'image de « souleve » montre l'ancienne animation), `../sherlock-repos.blend` (correct mais alourdi par des données inutilisées), et la copie du dossier dans `ithome-sherlock-java`, qui n'a aucune de ces nouveautés.

## Reprendre

1. Ouvrir Blender. Le pont MCP démarre seul (préférences enregistrées le 20/11). S'il ne répond pas : console Python de Blender, `exec(open(r"...\scripts\activer_pont_mcp.py", encoding="utf-8").read())`.
2. Les outils du travail en direct sont dans `scripts/direct/` : `shl_boot.py` (à exécuter une fois dans Blender), puis `job_planches.py`, `job_themes.py` (liste dans `shl.todo`), `job_base.py`. Ils contiennent encore le chemin du dossier temporaire de la session du 20/11 : le remplacer par `scripts/direct`.
3. Un thème prend environ 80 secondes (construction, deux animations, export, vérification, images de contrôle).

`sherlock-en-cours.blend` est la scène telle qu'elle était à la pause (base avec la lentille blanche). `sherlock-saisons.blend` date du matin, avec les anciens accessoires.
