// Load the playground data set: a JSON header plus one little-endian binary file
// (layout in the header; written by figures/playground/build_gaia_xp_mh.py).
// XMLHttpRequest rather than fetch so a local file:// build of the site also works.

function request(url, type) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url);
    xhr.responseType = type;
    xhr.onload = () => {
      if (xhr.status === 200 || (xhr.status === 0 && xhr.response)) resolve(xhr.response);
      else reject(new Error(`${url}: HTTP ${xhr.status}`));
    };
    xhr.onerror = () => reject(new Error(`${url}: network error`));
    xhr.send();
  });
}

const VIEWS = { uint64: BigUint64Array, float32: Float32Array, uint16: Uint16Array, uint8: Uint8Array };

// Typed views on the binary; the features are restored from their 16-bit storage
// as offset + stored value * step, per feature.
export function readArrays(header, buffer) {
  const arrays = {};
  for (const a of header.arrays) {
    const View = VIEWS[a.dtype];
    if (!View) throw new Error(`unknown dtype ${a.dtype}`);
    arrays[a.name] = new View(buffer, a.offset, a.length);
  }
  const q = arrays.features;
  const off = header.feature_offset;
  const step = header.feature_step;
  const d = off.length;
  const x = new Float32Array(q.length);
  for (let i = 0; i < q.length; i++) {
    const j = i % d;
    x[i] = off[j] + q[i] * step[j];
  }
  arrays.features = x;
  return arrays;
}

export async function loadDataset(headerUrl) {
  const header = await request(headerUrl, "json");
  const binUrl = new URL(header.binary, new URL(headerUrl, document.baseURI)).href;
  const buffer = await request(binUrl, "arraybuffer");
  return { header, arrays: readArrays(header, buffer) };
}
