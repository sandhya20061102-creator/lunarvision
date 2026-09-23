/**
 * pdsMetadata.js
 * Utility to extract lunar geographic metadata from PDS/PDS3 label files.
 *
 * Supported label sources:
 *   - Standalone .LBL files uploaded alongside an image
 *   - Embedded ASCII PDS label at the start of a .IMG file
 *
 * Supported PDS fields (case-insensitive):
 *   Bounding box:
 *     MINIMUM_LATITUDE, MAXIMUM_LATITUDE, MINIMUM_LONGITUDE, MAXIMUM_LONGITUDE
 *   Center:
 *     CENTER_LATITUDE, CENTER_LONGITUDE
 *   Corner coordinates (polygon when all four present):
 *     UPPER_LEFT_LATITUDE,  UPPER_LEFT_LONGITUDE
 *     UPPER_RIGHT_LATITUDE, UPPER_RIGHT_LONGITUDE
 *     LOWER_LEFT_LATITUDE,  LOWER_LEFT_LONGITUDE
 *     LOWER_RIGHT_LATITUDE, LOWER_RIGHT_LONGITUDE
 *   Mission / instrument:
 *     TARGET_NAME, INSTRUMENT_NAME, INSTRUMENT_ID, INSTRUMENT_HOST_NAME,
 *     INSTRUMENT_HOST_ID, MISSION_NAME, SENSOR, INSTRUMENT
 *
 * Returns null if no usable spatial metadata is found.
 * NEVER invents or infers coordinates beyond deriving center from min/max.
 */

/** Strip unit annotations like <DEGREES> or <KM> from a PDS value string. */
function stripUnits(value) {
  if (typeof value !== 'string') return value;
  return value.replace(/<[^>]+>/g, '').trim();
}

/** Parse a numeric PDS value, handling quotes and unit annotations. */
function parseNumber(value) {
  if (typeof value !== 'string') return null;
  const cleaned = stripUnits(value).replace(/['"]+/g, '').trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? null : num;
}

/** Clean a string PDS value for display. */
function parseString(value) {
  if (typeof value !== 'string') return null;
  const s = value.replace(/['"]+/g, '').trim();
  return s || null;
}

/**
 * Extracts geographic metadata from a PDS label file or embedded-label .IMG file.
 *
 * @param {File} file - the .LBL / .LBL.TXT / .IMG file
 * @returns {Promise<{
 *   minLat: number, maxLat: number, minLon: number, maxLon: number,
 *   centerLat: number, centerLon: number,
 *   corners: Array<{lat:number, lon:number}>|null,
 *   hasPolygon: boolean,
 *   targetName: string|null, instrument: string|null, missionName: string|null
 * }|null>}
 */
export async function extractPdsMetadata(file) {
  if (!file) return null;
  try {
    // Read up to 64 KB — enough for any PDS label header without loading full image
    const MAX_BYTES = 65536;
    const slice = file.slice(0, MAX_BYTES);
    const text = await slice.text();

    // Build a flat key -> value map (first occurrence wins)
    const map = {};
    const regex = /^([\w]+)\s*=\s*([^;\r\n]+)/gm;
    let match;
    while ((match = regex.exec(text)) !== null) {
      const key = match[1].toUpperCase().trim();
      if (!(key in map)) {
        map[key] = match[2].trim();
      }
    }

    // Get numeric value from first matching candidate key
    const getNum = (...candidates) => {
      for (const c of candidates) {
        const v = map[c.toUpperCase()];
        if (v !== undefined) {
          const n = parseNumber(v);
          if (n !== null) return n;
        }
      }
      return null;
    };

    // Get string value from first matching candidate key
    const getStr = (...candidates) => {
      for (const c of candidates) {
        const v = map[c.toUpperCase()];
        if (v !== undefined) {
          const s = parseString(v);
          if (s) return s;
        }
      }
      return null;
    };

    // ── Bounding box ──────────────────────────────────────────────────────────
    const minLat = getNum(
      'MINIMUM_LATITUDE', 'LATITUDE_MINIMUM', 'LATITUDE_MIN', 'LAT_MIN'
    );
    const maxLat = getNum(
      'MAXIMUM_LATITUDE', 'LATITUDE_MAXIMUM', 'LATITUDE_MAX', 'LAT_MAX'
    );
    const minLon = getNum(
      'MINIMUM_LONGITUDE', 'LONGITUDE_MINIMUM', 'LONGITUDE_MIN', 'LON_MIN',
      'MINIMUM_LONGITUDE_E', 'WESTERNMOST_LONGITUDE'
    );
    const maxLon = getNum(
      'MAXIMUM_LONGITUDE', 'LONGITUDE_MAXIMUM', 'LONGITUDE_MAX', 'LON_MAX',
      'MAXIMUM_LONGITUDE_E', 'EASTERNMOST_LONGITUDE'
    );

    // Must have a complete bounding box to be useful
    if (minLat === null || maxLat === null || minLon === null || maxLon === null) {
      return null;
    }

    // ── Center ────────────────────────────────────────────────────────────────
    let centerLat = getNum(
      'CENTER_LATITUDE', 'LATITUDE_CENTER',
      'SUB_SPACECRAFT_LATITUDE', 'SPACECRAFT_GEOCENTRIC_LATITUDE'
    );
    let centerLon = getNum(
      'CENTER_LONGITUDE', 'LONGITUDE_CENTER',
      'SUB_SPACECRAFT_LONGITUDE', 'SPACECRAFT_EAST_LONGITUDE'
    );
    // Derive from bounding box when not explicit (this is geometric, not invented)
    if (centerLat === null) centerLat = (minLat + maxLat) / 2;
    if (centerLon === null) centerLon = (minLon + maxLon) / 2;

    // ── Corner coordinates (polygon) ──────────────────────────────────────────
    const ulLat = getNum('UPPER_LEFT_LATITUDE',   'UL_CORNER_LAT');
    const ulLon = getNum('UPPER_LEFT_LONGITUDE',  'UL_CORNER_LON');
    const urLat = getNum('UPPER_RIGHT_LATITUDE',  'UR_CORNER_LAT');
    const urLon = getNum('UPPER_RIGHT_LONGITUDE', 'UR_CORNER_LON');
    const llLat = getNum('LOWER_LEFT_LATITUDE',   'LL_CORNER_LAT');
    const llLon = getNum('LOWER_LEFT_LONGITUDE',  'LL_CORNER_LON');
    const lrLat = getNum('LOWER_RIGHT_LATITUDE',  'LR_CORNER_LAT');
    const lrLon = getNum('LOWER_RIGHT_LONGITUDE', 'LR_CORNER_LON');

    const hasPolygon = [ulLat, ulLon, urLat, urLon, llLat, llLon, lrLat, lrLon]
      .every(v => v !== null);
    const corners = hasPolygon
      ? [
          { lat: ulLat, lon: ulLon },
          { lat: urLat, lon: urLon },
          { lat: lrLat, lon: lrLon },
          { lat: llLat, lon: llLon },
        ]
      : null;

    // ── Mission / instrument ──────────────────────────────────────────────────
    const targetName  = getStr('TARGET_NAME', 'BODY_NAME', 'PLANET_NAME');
    const instrument  = getStr(
      'INSTRUMENT_NAME', 'INSTRUMENT_ID', 'INSTRUMENT_HOST_NAME',
      'INSTRUMENT_HOST_ID', 'SENSOR', 'INSTRUMENT'
    );
    const missionName = getStr('MISSION_NAME', 'MISSION_ID', 'PROJECT_NAME');

    return {
      minLat,
      maxLat,
      minLon,
      maxLon,
      centerLat,
      centerLon,
      corners,
      hasPolygon,
      targetName,
      instrument,
      missionName,
    };
  } catch {
    return null;
  }
}

