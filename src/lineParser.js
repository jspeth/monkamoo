export const Preposition = {
  WITH: "with",
  AT: "at",
  IN_FRONT: "in_front",
  INTO: "into",
  ONTO: "onto",
  FROM: "from",
  OVER: "over",
  THROUGH: "through",
  UNDER: "under",
  BEHIND: "behind",
  BESIDE: "beside",
  FOR: "for",
  IS: "is",
  AS: "as",
  OFF: "off",
};

// Insertion order matters: synonyms() must return candidates in this order to
// match the Python implementation's dict ordering.
export const prepositionKeys = new Map([
  ["with", Preposition.WITH],
  ["using", Preposition.WITH],
  ["at", Preposition.AT],
  ["to", Preposition.AT],
  ["in front of", Preposition.IN_FRONT],
  ["in", Preposition.INTO],
  ["inside", Preposition.INTO],
  ["into", Preposition.INTO],
  ["on top of", Preposition.ONTO],
  ["on", Preposition.ONTO],
  ["onto", Preposition.ONTO],
  ["upon", Preposition.ONTO],
  ["out of", Preposition.FROM],
  ["from inside", Preposition.FROM],
  ["from", Preposition.FROM],
  ["over", Preposition.OVER],
  ["through", Preposition.THROUGH],
  ["under", Preposition.UNDER],
  ["underneath", Preposition.UNDER],
  ["beneath", Preposition.UNDER],
  ["behind", Preposition.BEHIND],
  ["beside", Preposition.BESIDE],
  ["for", Preposition.FOR],
  ["about", Preposition.FOR],
  ["is", Preposition.IS],
  ["as", Preposition.AS],
  ["off", Preposition.OFF],
  ["off of", Preposition.OFF],
]);

export function prepositionSynonyms(preposition) {
  const synonyms = [];
  for (const [key, value] of prepositionKeys) {
    if (value === preposition) {
      synonyms.push(key);
    }
  }
  return synonyms;
}

export class Command {
  constructor(line, verb = null, directObjectStr = null, preposition = null, indirectObjectStr = null) {
    this.player = null;
    this.line = line;
    this.verb = verb;
    this.directObject = null;
    this.directObjectStr = directObjectStr;
    this.preposition = preposition;
    this.indirectObject = null;
    this.indirectObjectStr = indirectObjectStr;
    // create args
    const words = line.split(" ");
    if (words.length > 1) {
      this.args = words.slice(1);
      this.argsStr = this.args.join(" ");
    } else {
      this.args = null;
      this.argsStr = null;
    }
    // indirect args: everything after the (first synonym of the) preposition
    const getRemainder = (string, word) => {
      for (const prep of prepositionSynonyms(word)) {
        const index = string.indexOf(prep);
        if (index === -1) {
          continue;
        }
        return string.slice(index + prep.length).trim();
      }
      return null;
    };
    this.indirectArgs = (preposition && getRemainder(line, preposition)) || null;
  }

  /**
   * Identify direct and indirect objects in the command relative to player.
   *
   * Varies from LambdaMOO slightly:
   *     '@name' identifies player by name
   *     '#room' identifies a room by name
   *     '$uuid' identifies an object by id
   *
   * Otherwise it looks for the objects in the player contents then the player's room contents.
   */
  resolve(world, player) {
    const resolveObject = (name) => {
      if (!name) {
        return null;
      }
      const lowered = name.toLowerCase();
      if (lowered === "me") {
        return player;
      }
      if (lowered === "here") {
        return player.location;
      }
      if (lowered.startsWith("@")) {
        return world.findPlayer(stripLeading(lowered, "@"));
      }
      if (lowered.startsWith("#")) {
        return world.findRoom(stripLeading(lowered, "#"));
      }
      if (lowered.startsWith("$")) {
        return world.contents[stripLeading(lowered, "$")] || null;
      }
      const candidates = [...Object.values(player.contents), ...Object.values(player.location?.contents || {})];
      for (const obj of candidates) {
        if (obj.name && obj.name.toLowerCase() === lowered) {
          return obj;
        }
      }
      return null;
    };
    this.player = player;
    this.directObject = resolveObject(this.directObjectStr);
    this.indirectObject = resolveObject(this.indirectObjectStr);
  }
}

function stripLeading(string, char) {
  let start = 0;
  while (start < string.length && string[start] === char) {
    start += 1;
  }
  return string.slice(start);
}

/**
 * MOO command parser.
 *
 * Structure:
 *     verb
 *     verb direct-object
 *     verb direct-object preposition indirect-object
 *
 * Examples:
 *     look
 *     take yellow bird
 *     put yellow bird in cuckoo clock
 */
export const Parser = {
  articles: ["a", "an", "the"],

  /** Parse a line of text into a MOO command. */
  parse(line) {
    if (!line) {
      return null;
    }
    // split line into words, dropping articles
    let words = line
      .replace(/^[ .]+/, "")
      .replace(/[ .]+$/, "")
      .split(" ");
    words = words.filter((w) => !Parser.articles.includes(w.toLowerCase()));
    if (!words.length || !words[0]) {
      return null;
    }
    // verb is always the first word
    const verb = words[0].toLowerCase();
    if (words.length === 1) {
      return new Command(line, verb);
    }
    // find preposition
    let i = 1;
    let preposition = null;
    for (const w of words.slice(1)) {
      preposition = prepositionKeys.get(w.toLowerCase()) || null;
      if (preposition) {
        break;
      }
      i += 1;
    }
    // find objects
    let directObject = null;
    let indirectObject = null;
    if (preposition) {
      directObject = words.slice(1, i).join(" ") || null;
      indirectObject = words.slice(i + 1).join(" ") || null;
    } else {
      directObject = words.slice(1).join(" ");
    }
    return new Command(line, verb, directObject, preposition, indirectObject);
  },
};
