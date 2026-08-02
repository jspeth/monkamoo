/** Return a string by joining the items with the conjunction. */
export function joinStrings(items, conj = "and") {
  const list = [...items];
  if (list.length === 1) {
    return list[0];
  }
  if (list.length === 2) {
    return `${list[0]} ${conj} ${list[1]}`;
  }
  return `${list.slice(0, -1).join(", ")}, ${conj} ${list[list.length - 1]}`;
}

/** Strip any of the given characters from both ends of a string (like Python's str.strip(chars)). */
export function stripChars(string, chars) {
  let start = 0;
  let end = string.length;
  while (start < end && chars.includes(string[start])) {
    start += 1;
  }
  while (end > start && chars.includes(string[end - 1])) {
    end -= 1;
  }
  return string.slice(start, end);
}

/**
 * Serialize a value to JSON with recursively sorted keys, matching Python's
 * `json.dumps(..., sort_keys=True, indent=2)` output byte-for-byte so world
 * files stay interchangeable between the Python and Node implementations.
 */
export function sortedJSONStringify(value, indent = 2) {
  const sortKeysDeep = (input) => {
    if (input && typeof input === "object" && typeof input.toJSON === "function") {
      return sortKeysDeep(input.toJSON());
    }
    if (Array.isArray(input)) {
      return input.map(sortKeysDeep);
    }
    if (input && typeof input === "object") {
      const out = {};
      for (const key of Object.keys(input).sort()) {
        out[key] = sortKeysDeep(input[key]);
      }
      return out;
    }
    return input;
  };
  return JSON.stringify(sortKeysDeep(value), null, indent);
}
