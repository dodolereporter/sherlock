export type ObjectKind = 'boule' | 'sucre' | 'flocon' | 'etoile' | 'cloche' | 'chocolat';
export type Mood = 'aurore' | 'blizzard' | 'etoiles';
export type SceneKind = 'train' | 'bonhomme';

export type Surprise =
  | { kind: 'typo'; lines: readonly string[] }
  | { kind: 'objet'; object: ObjectKind }
  | { kind: 'sherlock'; action: 'theme_objet' | 'theme_special' | 'dort' }
  | { kind: 'ambiance'; mood: Mood }
  | { kind: 'enigme'; question: string; answer: string }
  | { kind: 'scene'; scene: SceneKind }
  | { kind: 'lanternes' }
  | { kind: 'feu' }
  | { kind: 'final' };

export interface DayContent {
  day: number;
  title: string;
  text: string;
  surprise: Surprise;
}

export const KIND_LABEL: Record<Surprise['kind'], string> = {
  typo: 'Message',
  objet: 'Pièce à conviction',
  sherlock: 'Sherlock en action',
  ambiance: 'Changement de ciel',
  enigme: 'Énigme',
  scene: 'Petite scène',
  lanternes: 'Lumières',
  feu: "Feu d'artifice",
  final: 'Le grand final',
};

export const DAYS: readonly DayContent[] = [
  {
    day: 1,
    title: "Ouverture de l'enquête",
    text: 'Une case par soir, un indice à chaque fois. Sherlock a sorti sa loupe.',
    surprise: { kind: 'typo', lines: ['Vingt-quatre cases.', 'Vingt-quatre indices.', 'Une seule nuit de Noël.'] },
  },
  {
    day: 2,
    title: 'La boule du sapin',
    text: 'Retrouvée sous la neige, sans une fêlure. Sherlock la garde pour le grand soir.',
    surprise: { kind: 'objet', object: 'boule' },
  },
  {
    day: 3,
    title: 'Matière première',
    text: "Sherlock ramasse de la neige. Il affirme que c'est pour une expérience.",
    surprise: { kind: 'sherlock', action: 'theme_objet' },
  },
  {
    day: 4,
    title: "Le ciel s'allume",
    text: 'Une aurore au-dessus des crêtes. Elle ne dure jamais longtemps : levez les yeux.',
    surprise: { kind: 'ambiance', mood: 'aurore' },
  },
  {
    day: 5,
    title: 'Première énigme',
    text: 'Sherlock a besoin de vous.',
    surprise: {
      kind: 'enigme',
      question: 'Je tombe sans jamais me faire mal, je suis toujours unique et je fonds dans la main. Qui suis-je ?',
      answer: 'Un flocon de neige.',
    },
  },
  {
    day: 6,
    title: 'Le petit train',
    text: 'Il fait le tour du sapin chaque 6 décembre. Personne ne sait qui le conduit.',
    surprise: { kind: 'scene', scene: 'train' },
  },
  {
    day: 7,
    title: "Sucre d'orge",
    text: 'Rayé rouge et blanc, rangé comme une pièce à conviction.',
    surprise: { kind: 'objet', object: 'sucre' },
  },
  {
    day: 8,
    title: 'Fête des Lumières',
    text: 'Ce soir, on pose des lumignons aux fenêtres. Ici, ils préfèrent s’envoler.',
    surprise: { kind: 'lanternes' },
  },
  {
    day: 9,
    title: 'Note du carnet',
    text: 'Page 9 du carnet de Sherlock.',
    surprise: { kind: 'typo', lines: ['Il neige', 'doucement', "sur l'enquête."] },
  },
  {
    day: 10,
    title: 'Boule de neige !',
    text: 'Sherlock a trouvé une cible. Il présente ses excuses pour l’écran.',
    surprise: { kind: 'sherlock', action: 'theme_special' },
  },
  {
    day: 11,
    title: 'Le flocon parfait',
    text: 'Six branches, aucune pareille. Sherlock l’a observé à la loupe pendant une heure.',
    surprise: { kind: 'objet', object: 'flocon' },
  },
  {
    day: 12,
    title: 'Coup de vent',
    text: 'Le blizzard se lève sur le col. Sherlock tient bon.',
    surprise: { kind: 'ambiance', mood: 'blizzard' },
  },
  {
    day: 13,
    title: 'Deuxième énigme',
    text: 'Une question de saison.',
    surprise: {
      kind: 'enigme',
      question: 'Je pends vide toute l’année, et une seule nuit on me remplit. Qui suis-je ?',
      answer: 'La chaussette de Noël.',
    },
  },
  { day: 14, title: "Feu d'artifice", text: 'Quatorze cases ouvertes : il ne reste que dix nuits.', surprise: { kind: 'feu' } },
  {
    day: 15,
    title: "L'étoile en pain d'épices",
    text: "Encore tiède. Sherlock jure qu'il n'en a pas croqué une branche.",
    surprise: { kind: 'objet', object: 'etoile' },
  },
  {
    day: 16,
    title: 'Le bonhomme de neige',
    text: "Il s'est construit tout seul pendant la nuit. Affaire à suivre.",
    surprise: { kind: 'scene', scene: 'bonhomme' },
  },
  {
    day: 17,
    title: 'Note du carnet',
    text: 'Page 17, écrite à la lueur des lanternes.',
    surprise: { kind: 'typo', lines: ['Chaque indice', 'nous rapproche', 'de Noël.'] },
  },
  {
    day: 18,
    title: 'Nuit étoilée',
    text: 'Faites un vœu : une étoile filante vient de passer.',
    surprise: { kind: 'ambiance', mood: 'etoiles' },
  },
  {
    day: 19,
    title: 'La cloche du hameau',
    text: 'Elle sonne pour dire qu’il ne reste que cinq jours.',
    surprise: { kind: 'objet', object: 'cloche' },
  },
  {
    day: 20,
    title: 'La sieste du détective',
    text: 'Vingt cases d’enquête. Sherlock s’accorde une pause bien méritée.',
    surprise: { kind: 'sherlock', action: 'dort' },
  },
  {
    day: 21,
    title: "Solstice d'hiver",
    text: 'La nuit la plus longue de l’année. Des lanternes montent pour l’éclairer.',
    surprise: { kind: 'lanternes' },
  },
  {
    day: 22,
    title: 'Dernière énigme',
    text: 'Sherlock la garde depuis le début.',
    surprise: {
      kind: 'enigme',
      question: 'Plus il y en a, moins on y voit. En montagne, il dort au fond des vallées. Qui suis-je ?',
      answer: 'Le brouillard.',
    },
  },
  {
    day: 23,
    title: 'Chocolat chaud',
    text: 'Dernière nuit d’attente. Une tasse pour tenir jusqu’à demain.',
    surprise: { kind: 'objet', object: 'chocolat' },
  },
  {
    day: 24,
    title: 'Joyeux Noël',
    text: 'Vingt-quatre cases, vingt-quatre indices. L’enquête est close : c’est Noël.',
    surprise: { kind: 'final' },
  },
];

export function dayContent(day: number): DayContent {
  const content = DAYS[day - 1];
  if (!content) throw new Error(`Contenu manquant pour la case ${day}`);
  return content;
}
