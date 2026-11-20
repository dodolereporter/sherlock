# Sherlock 3D : les modèles

Sherlock, la mascotte de l'assistant d'ITHome chez OPAC SAVOIE, en 3D temps réel pour le navigateur (three.js, `GLTFLoader`). Ce dépôt contient les modèles dans leur état du 20/11/2026.

## Contenu

| Fichier | Rôle |
|---|---|
| `sherlock.glb` | Le modèle de base, son squelette (30 os) et ses 30 animations. |
| `animations.json` | Liste des animations : famille, type, durée, os animés. |
| `verification-animations.md` | Contrôle automatique du `.glb` : les 30 animations sont conformes. |
| `sherlock-repos.blend` | La scène Blender 5.3 du modèle de base (une piste NLA par animation). |
| `textures/` | Le tricot de l'écharpe (couleur et relief), utilisé par les scènes Blender. |
| `LISEZ-MOI.md` | Squelette, règles pour jouer les animations. Il cite aussi des dossiers (`scripts`, `planches`, `video`) qui ne sont pas dans ce dépôt. |
| `saisons/sherlock-<thème>.glb` | Un modèle par saison ou fête : la tenue, les objets, les 30 animations de base et deux animations propres au thème, `theme_objet` et `theme_special`. |
| `saisons/sherlock-<thème>.json` | Liste des animations du thème. |
| `saisons/blend/` | La scène Blender de chaque thème. |
| `saisons/planche-*.png` | Aperçus : tenue, objet sorti, pose clé de l'animation spéciale. |

## Thèmes présents

Printemps, été, automne, hiver, Nouvel An, Épiphanie, Chandeleur, Saint-Valentin, Mardi gras, Pâques. Les dix fichiers passent le contrôle automatique.

## Pas encore là

- Quatre thèmes restent à produire : Fête de la musique, 14 juillet, Halloween, Noël.
- Le 1er mai est à refaire, son fichier n'est donc pas publié.
- La loupe n'a pas encore de verre grossissant.
- Les animations de thème n'ont pas toutes été relues image par image.
