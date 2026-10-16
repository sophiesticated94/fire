export type SceneId = 'burner'|'candle'|'wood';
export type Layer = 'fire'|'temperature'|'flow'|'oxygen';
export interface Config {
  scene:SceneId; quality:'preview'|'fine'; duration:number; fuel:number; oxygen:number;
  wind:number; primary_air:number; ambient:number; moisture:number; ignition:number;
}
export interface Job {id:string;status:string;progress:number;physicalTime?:number;elapsed?:number;error?:string;cached?:boolean;config?:Config;attempt?:string;previewFrames?:number;profile?:{mode:string;ranks:number;threads:number}}
export interface HistoryItem {id:string;config:Config;elapsed:number;sample:boolean;featured?:boolean}
export interface Result {
  id:string;config:Config;solver:string;model:string;dimensions:[number,number,number];
  coordinates:{x:number[];y:number[];z:number[]};times:number[];elapsed:number;
  extrema:{temperature:number;hrr:number;velocity:number}[];
  series:Record<string,number[]>;devices:Record<string,number[]>;
  solidBounds?:number[][];
  complete?:boolean;attempt?:string;revision?:number;status?:string;profile?:{mode:string;ranks:number;threads:number};
}
export const defaults:Record<SceneId,Config> = {
  burner:{scene:'burner',quality:'preview',duration:2,fuel:12,oxygen:20.9,wind:0,primary_air:.3,ambient:20,moisture:0,ignition:0},
  candle:{scene:'candle',quality:'preview',duration:2,fuel:1.2,oxygen:20.9,wind:0,primary_air:0,ambient:20,moisture:0,ignition:0},
  wood:{scene:'wood',quality:'preview',duration:15,fuel:0,oxygen:20.9,wind:0,primary_air:0,ambient:20,moisture:12,ignition:35},
};
export const sceneNames:Record<SceneId,string> = {burner:'Palnik gazowy',candle:'Świeca',wood:'Drewno'};
export const sceneCopy:Record<SceneId,{tag:string;title:string;description:string;equation:string;notes:string[]}> = {
  burner:{tag:'01 / SPALANIE GAZU',title:'Anatomia płomienia',description:'Tam, gdzie paliwo spotyka tlen, energia chemiczna zamienia się w ciepło i światło.',equation:'CH₄ + 2 O₂ → CO₂ + 2 H₂O + energia',notes:[
    'Paliwo i tlen','Metan wypływa z palnika. Powietrze pierwotne miesza się z paliwem przed wylotem, a pozostały tlen dociera z otoczenia.',
    'Ciepło wprawia gaz w ruch','Ogrzane gazy mają mniejszą gęstość. Siła wyporu unosi je, a chłodne powietrze napływa w ich miejsce.',
    'Światło ma różne źródła','Niebieską emisję mogą tworzyć wzbudzone cząsteczki. Żółte światło pochodzi głównie od rozgrzanej sadzy. Kolor nie jest termometrem.',
  ]},
  candle:{tag:'02 / PŁOMIEŃ DYFUZYJNY',title:'Mały płomień. Wielka fizyka.',description:'Świeca spala pary paliwa. Tlen dociera do nich z otoczenia, tworząc cienką strefę reakcji.',equation:'paliwo + O₂ → produkty + ciepło + światło',notes:[
    'Spalają się pary','W prawdziwej świecy wosk topi się i wędruje przez knot. Ten model zadaje dopływ zastępczych par n-heptanu; nie oblicza transportu w knocie.',
    'Granica spotkania','Paliwo i tlen docierają do płomienia z przeciwnych stron. To przykład spalania dyfuzyjnego.',
    'Dlaczego płomień jest żółty?','Cząstki sadzy rozgrzewają się i emitują światło. Ich powstawanie w modelu jest opisane zadanym współczynnikiem, a transport oblicza CFD.',
  ]},
  wood:{tag:'03 / PIROLIZA MATERIAŁU',title:'Ogień zaczyna się w drewnie',description:'Zanim pojawi się płomień, materiał nagrzewa się, traci wodę i uwalnia palne gazy.',equation:'ciepło → suszenie → piroliza → spalanie gazów',notes:[
    'Najpierw odparowuje woda','Wilgoć pochłania energię podczas nagrzewania i odparowania. Zmiana wilgotności wpływa na temperaturę i przebieg rozkładu materiału.',
    'Płomień ponad powierzchnią','Piroliza rozkłada materiał pod wpływem ciepła. Uwolnione gazy mieszają się z powietrzem i mogą spalać nad próbką.',
    'Co zostaje po płomieniu?','Model tworzy pozostałość zwęgloną. Nie obejmuje jej utleniania: widoczny gorący materiał nie oznacza obliczonego spalania żarowego.',
  ]},
};
