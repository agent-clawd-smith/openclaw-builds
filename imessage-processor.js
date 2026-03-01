#!/usr/bin/env node
/**
 * iMessage Smart Processor
 * 
 * Polls iMessages from whitelisted contacts. For each new message:
 *   1. Extracts and describes any image attachments (via Claude vision)
 *   2. Fetches and summarizes any URLs (via Firecrawl)
 *   3. Builds an enriched message with all context
 *   4. Routes through `openclaw agent --to <number>` for a proper response
 *   5. Response is delivered back via iMessage
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const https = require('https');

const CONTACTS_FILE = path.join(process.env.HOME, '.openclaw/workspace/family-contacts.json');
const STATE_FILE = '/tmp/imessage-processor-state.json';
const POLL_INTERVAL = 10000;

// Generate a stable session ID per identifier so each person
// gets their own session in the main agent (no lock conflicts with webchat)
const crypto = require('crypto');
function stableSessionId(identifier) {
  // UUID v5-style: deterministic UUID from identifier string
  const hash = crypto.createHash('sha1').update('imessage:' + identifier).digest('hex');
  return [hash.slice(0,8), hash.slice(8,12), '5' + hash.slice(13,16), hash.slice(16,20), hash.slice(20,32)].join('-');
}
const IMSG = '/opt/homebrew/bin/imsg';
const OPENCLAW = '/opt/homebrew/bin/openclaw';

// Load API keys from local secrets
const secrets = JSON.parse(fs.readFileSync(path.join(process.env.HOME, '.openclaw/secrets.json')));
const FIRECRAWL_KEY = secrets?.firecrawl?.apiKey;
const authProfiles = JSON.parse(fs.readFileSync(path.join(process.env.HOME, '.openclaw/agents/main/agent/auth-profiles.json')));
const ANTHROPIC_KEY = authProfiles?.profiles?.['anthropic:default']?.key;

function log(msg) {
  console.log(`${new Date().toISOString()} ${msg}`);
}

function run(cmd, opts = {}) {
  return execSync(cmd, { encoding: "utf8", timeout: 60000, ...opts }).trim();
}

function runAsync(cmd, timeoutMs = 150000) {
  return new Promise((resolve, reject) => {
    const { exec } = require("child_process");
    exec(cmd, { encoding: "utf8", timeout: timeoutMs }, (err, stdout) => {
      if (err) reject(err); else resolve((stdout || "").trim());
    });
  });
}

function loadContacts() {
  return JSON.parse(fs.readFileSync(CONTACTS_FILE, 'utf8'));
}

function loadState() {
  if (!fs.existsSync(STATE_FILE)) return {};
  return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function getChats() {
  try {
    return run(`${IMSG} chats --json`).split('\n').filter(Boolean).map(l => JSON.parse(l));
  } catch(e) { return []; }
}

function getMessages(chatId, limit = 10) {
  try {
    return run(`${IMSG} history --chat-id ${chatId} --limit ${limit} --attachments --json`)
      .split('\n').filter(Boolean).map(l => JSON.parse(l));
  } catch(e) { return []; }
}

// POST request helper
function post(hostname, path, headers, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = https.request({ hostname, path, method: 'POST', headers: { ...headers, 'Content-Length': Buffer.byteLength(data) } }, res => {
      let buf = '';
      res.on('data', d => buf += d);
      res.on('end', () => { try { resolve(JSON.parse(buf)); } catch(e) { resolve(buf); } });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Describe an image using Claude vision
async function describeImage(imgPath) {
  if (!ANTHROPIC_KEY) return '[image - no API key]';
  try {
    // Convert HEIC to JPEG — Claude can't read HEIC
    const ext = path.extname(imgPath).toLowerCase();
    if (ext === '.heic' || ext === '.heif') {
      const jpgPath = imgPath.replace(/\.hei[cf]$/i, '_converted.jpg');
      const conv = spawnSync('sips', ['-s', 'format', 'jpeg', imgPath, '--out', jpgPath], { encoding: 'utf8' });
      if (conv.status === 0 && fs.existsSync(jpgPath)) {
        imgPath = jpgPath;
      } else {
        log(`HEIC conversion failed: ${conv.stderr}`);
        return '[image - HEIC conversion failed]';
      }
    }
    const finalExt = path.extname(imgPath).toLowerCase();
    const imgData = fs.readFileSync(imgPath).toString('base64');
    const mediaType = finalExt === '.png' ? 'image/png' : finalExt === '.gif' ? 'image/gif' : finalExt === '.webp' ? 'image/webp' : 'image/jpeg';
    
    const result = await post('api.anthropic.com', '/v1/messages', {
      'Content-Type': 'application/json',
      'x-api-key': ANTHROPIC_KEY,
      'anthropic-version': '2023-06-01',
    }, {
      model: 'claude-haiku-4-5',
      max_tokens: 300,
      messages: [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: mediaType, data: imgData } },
        { type: 'text', text: 'Describe this image concisely in 1-3 sentences.' }
      ]}]
    });
    return result?.content?.[0]?.text || '[image - description failed]';
  } catch(e) {
    log(`Vision error: ${e.message}`);
    return '[image - description failed]';
  }
}

// Fetch URL content via Firecrawl
async function fetchUrl(url) {
  if (!FIRECRAWL_KEY) return `[link: ${url}]`;
  try {
    const result = await post('api.firecrawl.dev', '/v1/scrape', {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${FIRECRAWL_KEY}`,
    }, { url, formats: ['markdown'] });
    
    if (result?.success && result?.data?.markdown) {
      // Trim to first 800 chars to keep context manageable
      const text = result.data.markdown.replace(/!\[.*?\]\(.*?\)/g, '').trim().slice(0, 800);
      const title = result.data.metadata?.title || url;
      return `[Link: "${title}" — ${text}...]`;
    }
    return `[link: ${url}]`;
  } catch(e) {
    log(`Firecrawl error: ${e.message}`);
    return `[link: ${url}]`;
  }
}

// Extract URLs from text
function extractUrls(text) {
  const urlRegex = /https?:\/\/[^\s]+/g;
  return (text || '').match(urlRegex) || [];
}

// Build enriched message with image descriptions + URL content
async function enrichMessage(msg) {
  const parts = [];
  
  // Clean text
  let text = (msg.text || '').replace(/[\uFFFC\u0000-\u0008\u000B-\u001F]/g, '').trim();
  
  // Process image attachments
  for (const att of (msg.attachments || [])) {
    if (!att.mime_type?.startsWith('image/') || att.missing) continue;
    const srcPath = att.original_path.replace('~', process.env.HOME);
    if (!fs.existsSync(srcPath)) continue;
    log(`  Describing image: ${att.transfer_name}`);
    const description = await describeImage(srcPath);
    parts.push(`[Photo: ${description}]`);
  }
  
  // Extract and fetch URLs
  const urls = extractUrls(text);
  for (const url of urls.slice(0, 2)) { // max 2 URLs per message
    log(`  Fetching URL: ${url}`);
    const content = await fetchUrl(url);
    text = text.replace(url, ''); // remove raw URL from text
    parts.push(content);
  }
  
  if (text.trim()) parts.unshift(text.trim());
  
  return parts.join('\n\n') || '[message with no readable content]';
}

async function poll() {
  const contacts = loadContacts();
  const state = loadState();
  const chats = getChats();

  for (const chat of chats) {
    const identifier = chat.identifier;
    if (!contacts[identifier]) continue;

    const name = contacts[identifier];
    const chatId = chat.id;
    const messages = getMessages(chatId, 10);
    const lastSeenId = state[identifier] || 0;

    const newMessages = messages
      .filter(m => !m.is_from_me && m.id > lastSeenId)
      .sort((a, b) => a.id - b.id);

    if (newMessages.length === 0) continue;

    // Mark all as seen immediately to prevent double-processing
    state[identifier] = newMessages[newMessages.length - 1].id;
    saveState(state);

    log(`${newMessages.length} new message(s) from ${name} (${identifier})`);

    // Send immediate ack so the person knows we're on it
    const acks = [
      "On it 👀",
      "One sec… 🕶️",
      "Got it, let me take a look 🔍",
      "On it! Give me just a moment ✨",
      "👀 One sec…"
    ];
    const ack = acks[Math.floor(Math.random() * acks.length)];
    try { run(`${IMSG} send --to "${identifier}" --text "${ack}"`); } catch(e) {}

    // Batch: wait 4 seconds then re-fetch to catch any trailing messages sent quickly
    await new Promise(r => setTimeout(r, 4000));
    const batchedMessages = getMessages(chatId, 15)
      .filter(m => !m.is_from_me && m.id > lastSeenId)
      .sort((a, b) => a.id - b.id);

    // Update state to cover any new messages that arrived during wait
    if (batchedMessages.length > 0) {
      state[identifier] = batchedMessages[batchedMessages.length - 1].id;
      saveState(state);
    }

    // Merge all messages into one context block per batch
    const mergedText = batchedMessages.map(m => (m.text || '').replace(/[\uFFFC\u0000-\u0008\u000B-\u001F]/g, '').trim()).filter(Boolean).join(' ');
    const mergedAttachments = batchedMessages.flatMap(m => m.attachments || []);
    const mergedMsg = { text: mergedText, attachments: mergedAttachments, id: batchedMessages[batchedMessages.length-1]?.id };

    const msgs = batchedMessages.length > 0 ? [mergedMsg] : [];

    for (const msg of msgs) {
      try {
        log(`  Processing message id=${msg.id}`);
        const enriched = await enrichMessage(msg);
        log(`  Enriched: ${enriched.substring(0, 100)}...`);

        // Skip unreadable messages silently
        if (enriched === '[message with no readable content]') {
          log(`  Skipping unreadable message`);
          state[identifier] = msg.id;
          saveState(state);
          continue;
        }

        // Route through openclaw agent (per-person session via --to)
        // Use spawnSync to avoid shell escaping/length issues with large messages
        const agentArgs = [
          'agent', '--agent', 'imessage', '--to', identifier,
          '--deliver', '--reply-channel', 'imessage', '--reply-to', identifier,
          '--message', enriched, '--timeout', '120'
        ];
        
        try {
          const result = spawnSync(OPENCLAW, agentArgs, { encoding: 'utf8', timeout: 130000 });
          if (result.status !== 0) {
            throw new Error(result.stderr || result.stdout || 'unknown error');
          }
          log(`  Response delivered to ${name}`);
        } catch(e) {
          log(`  Agent error: ${e.message.split('\n')[0]}`);
        }

      } catch(e) {
        log(`  Error processing message: ${e.message}`);
      }
    }
  }
}

log('iMessage smart processor started');
log(`Contacts: ${Object.values(loadContacts()).filter((v,i,a) => a.indexOf(v) === i).join(', ')}`);
log(`Firecrawl: ${FIRECRAWL_KEY ? 'configured' : 'missing'}`);
log(`Vision: ${ANTHROPIC_KEY ? 'configured' : 'missing'}`);

poll().catch(e => log(`Initial poll error: ${e.message}`));
setInterval(() => poll().catch(e => log(`Poll error: ${e.message}`)), POLL_INTERVAL);
