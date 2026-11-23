import { dayContent } from '../../content/days';
import { useApp } from '../../store';
import { Ambiance, Reframe, SherlockAction } from './Moments';
import { Fireworks, GrandStar, Lanterns } from './Sky';
import { Snowman } from './Snowman';
import { SurpriseObject } from './SurpriseObject';
import { Train } from './Train';

/** Monte la surprise de la case active une fois l'ouverture jouée. */
export function Surprises() {
  const day = useApp((s) => s.activeDay);
  const revealed = useApp((s) => s.revealed);
  if (day === null || !revealed) return null;
  const s = dayContent(day).surprise;
  switch (s.kind) {
    case 'objet':
      return <SurpriseObject key={day} day={day} kind={s.object} />;
    case 'sherlock':
      return <SherlockAction key={day} action={s.action} />;
    case 'ambiance':
      return <Ambiance key={day} mood={s.mood} />;
    case 'scene':
      return (
        <group key={day}>
          <Reframe to="ground" />
          {s.scene === 'train' ? <Train /> : <Snowman />}
        </group>
      );
    case 'lanternes':
      return (
        <group key={day}>
          <Reframe to="sky" />
          <Lanterns />
        </group>
      );
    case 'feu':
      return (
        <group key={day}>
          <Reframe to="sky" />
          <Fireworks />
        </group>
      );
    case 'final':
      return (
        <group key={day}>
          <GrandStar />
          <Fireworks finale />
        </group>
      );
    case 'typo':
    case 'enigme':
      return null;
  }
}
