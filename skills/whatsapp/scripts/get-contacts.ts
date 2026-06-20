import * as dotenv from 'dotenv';
import * as path from 'path';
import * as fs from 'fs';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '.env') });

const API_URL = process.env.GREEN_API_URL || 'https://api.green-api.com';
const INSTANCE_ID = process.env.GREEN_API_INSTANCE;
const API_TOKEN = process.env.GREEN_API_TOKEN;

// Raw Green API dump — the source for send-by-name lookups (match name/contactName).
const OUT_FILE = path.join(__dirname, 'contacts-raw.json');

interface Contact {
  id: string;
  name?: string;
  type?: string;
}

async function getContacts(): Promise<Contact[]> {
  const url = `${API_URL}/waInstance${INSTANCE_ID}/getContacts/${API_TOKEN}`;

  const response = await fetch(url);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API request failed: ${response.status} - ${text}`);
  }

  return response.json();
}

async function main() {
  // Validate credentials
  if (!INSTANCE_ID || !API_TOKEN) {
    console.error('Error: Missing credentials!');
    console.error('Please configure GREEN_API_INSTANCE and GREEN_API_TOKEN in .env file');
    process.exit(1);
  }

  try {
    const contacts = await getContacts();
    fs.writeFileSync(OUT_FILE, JSON.stringify(contacts, null, 2));

    const users = contacts.filter((c) => c.type === 'user').length;
    const groups = contacts.filter((c) => c.type === 'group').length;

    console.log(`Wrote ${contacts.length} contacts to ${OUT_FILE}`);
    console.log(`  users: ${users}, groups: ${groups}, other: ${contacts.length - users - groups}`);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
