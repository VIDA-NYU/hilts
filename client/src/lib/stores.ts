import { writable } from 'svelte/store';
import { animals, descriptions, negativeKeywords } from "./Descriptions";

// type LabelType = "relevant" |  " animal";

// interface Label {
//     name: string;
//     type: LabelType;
// }

// const labels: Label[];

// interface LabelList = {
//     [key: LabelType]: string[];
// };

export const descriptionsStore = writable<string[]>(descriptions);

export const animalStore = writable<string[]>(animals);

export const negativeKeywordStore = writable<string[]>(negativeKeywords);

export const selectedDataStore = writable({});

export const modal = writable(null);
export const windowStyle = writable({});
