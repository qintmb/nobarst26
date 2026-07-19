const { google } = require('googleapis');

const SPREADSHEET_ID = process.env.GOOGLE_SHEET_ID || '11E7hmKvQtGMNWqSzyLK78HToDhiFgYEJ9XBchoG5c0g';

function getAuth() {
  const auth = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    'urn:ietf:wg:oauth:2.0:oob'
  );
  auth.setCredentials({ refresh_token: process.env.GOOGLE_REFRESH_TOKEN });
  return auth;
}

async function appendRow(sheet, values) {
  const auth = getAuth();
  const sheets = google.sheets({ version: 'v4', auth });
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  const { data } = await sheets.spreadsheets.values.append({
    spreadsheetId: SPREADSHEET_ID,
    range: `${sheet}!A:A`,
    valueInputOption: 'USER_ENTERED',
    insertDataOption: 'INSERT_ROWS',
    requestBody: { values: [[ts, ...values]] },
  });
  return data.updates?.updatedCells ?? 0;
}

/** Check if SAP already exists in the given sheet (column C = index 2) */
async function sapExists(sheet, sap) {
  const auth = getAuth();
  const sheets = google.sheets({ version: 'v4', auth });
  const { data } = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: `${sheet}!C:C`,
  });
  const rows = data.values || [];
  return rows.some(row => row[0] && row[0].toString().trim() === sap.toString().trim());
}

const headers = {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '{}' };
  if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

  let data;
  try {
    const raw = event.isBase64Encoded ? Buffer.from(event.body, 'base64').toString() : event.body;
    data = JSON.parse(raw);
  } catch {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'Invalid JSON' }) };
  }

  try {
    const path = event.path;
    if (path.endsWith('/api/daftar-hadir')) {
      const c = await appendRow('daftar hadir', [data.nama || '', data.sap || '', data.unit_kerja || '']);
      return { statusCode: 200, headers, body: JSON.stringify({ status: 'ok', cells: c }) };
    }
    if (path.endsWith('/api/tebak-skor')) {
      // Check 1 device 1 submission
      if (await sapExists('tebakskor', data.sap)) {
        return { statusCode: 409, headers, body: JSON.stringify({ error: 'Anda sudah pernah mengisi. 1 device hanya 1x submit.' }) };
      }
      const c = await appendRow('tebakskor', [
        data.nama || '', data.sap || '', data.kategori || '',
        data.juara || '', String(data.skor_arg ?? ''), String(data.skor_spa ?? ''),
      ]);
      return { statusCode: 200, headers, body: JSON.stringify({ status: 'ok', cells: c }) };
    }
    return { statusCode: 404, headers, body: JSON.stringify({ error: 'Not found' }) };
  } catch (err) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: err.message }) };
  }
};
