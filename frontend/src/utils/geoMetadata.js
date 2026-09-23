/**
 * geoMetadata.js
 * Extracts real GPS / spatial metadata from an image File using ExifReader.
 * Never invents or approximates coordinates.
 * Returns null if reliable data is unavailable.
 */

/**
 * Convert a GPS rational array [deg, min, sec] (as returned by ExifReader)
 * into a decimal-degrees number.
 * @param {Array} components  e.g. [{numerator:34,denominator:1},{numerator:5,...},...]
 * @param {string} ref        'N'|'S'|'E'|'W'
 * @returns {number|null}
 */
function rationalToDecimal(components, ref) {
  if (!Array.isArray(components) || components.length < 3) return null;
  const [degObj, minObj, secObj] = components;
  if (!degObj || !minObj || !secObj) return null;

  const deg = degObj.numerator / (degObj.denominator || 1);
  const min = minObj.numerator / (minObj.denominator || 1);
  const sec = secObj.numerator / (secObj.denominator || 1);

  let decimal = deg + min / 60 + sec / 3600;
  if (ref === 'S' || ref === 'W') decimal = -decimal;
  return decimal;
}

/**
 * Parse an ExifReader GPS altitude tag.
 * @param {object} altTag   ExifReader tag for GPSAltitude
 * @param {object} refTag   ExifReader tag for GPSAltitudeRef (0=above, 1=below)
 * @returns {number|null}
 */
function parseAltitude(altTag, refTag) {
  if (!altTag) return null;
  const val = altTag.numerator / (altTag.denominator || 1);
  const below = refTag && refTag.value === 1;
  return below ? -val : val;
}

/**
 * Extract geographic metadata from an image File object.
 * Uses ExifReader (already installed as 'exifreader') to read EXIF tags.
 *
 * @param {File} file  Browser File object
 * @returns {Promise<{centerLat: number, centerLon: number, altitudeM: number|null, sensor: string|null}|null>}
 *   Resolves to a metadata object if valid GPS coordinates found, otherwise null.
 */
export async function extractGeoMetadata(file) {
  if (!file) return null;

  try {
    const ExifReader = (await import('exifreader')).default;

    const buffer = await file.arrayBuffer();
    const tags = ExifReader.load(buffer, { expanded: true });

    const gps = tags.gps || tags.GPS || {};

    // Latitude
    const latComponents = gps.GPSLatitude?.value ?? gps['GPS GPSLatitude']?.value;
    const latRef = gps.GPSLatitudeRef?.value?.[0] ?? gps['GPS GPSLatitudeRef']?.value?.[0];

    // Longitude
    const lonComponents = gps.GPSLongitude?.value ?? gps['GPS GPSLongitude']?.value;
    const lonRef = gps.GPSLongitudeRef?.value?.[0] ?? gps['GPS GPSLongitudeRef']?.value?.[0];

    const centerLat = rationalToDecimal(latComponents, latRef);
    const centerLon = rationalToDecimal(lonComponents, lonRef);

    // Both coordinates must be present and finite
    if (centerLat === null || centerLon === null ||
        !isFinite(centerLat) || !isFinite(centerLon)) {
      return null;
    }

    // Optional altitude
    const altTag = gps.GPSAltitude?.value ?? gps['GPS GPSAltitude']?.value;
    const altRefTag = gps.GPSAltitudeRef?.value ?? gps['GPS GPSAltitudeRef']?.value;
    const altitudeM = parseAltitude(
      altTag ? { numerator: altTag[0]?.numerator ?? altTag[0], denominator: altTag[0]?.denominator ?? 1 } : null,
      altRefTag ? { value: altRefTag[0] } : null
    );

    // Optional sensor/camera model
    const exif = tags.exif || tags.Exif || {};
    const sensor = exif.Model?.description ?? exif['Image Model']?.description ?? null;

    return { centerLat, centerLon, altitudeM, sensor };
  } catch {
    // ExifReader throws when no EXIF data is found — that is expected for lunar images
    return null;
  }
}
