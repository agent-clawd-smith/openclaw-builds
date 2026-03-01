#!/usr/bin/env node
/**
 * Family iMessage Handler
 * - Polls iMessage for new messages from whitelisted contacts
 * - Processes photos and URLs
 * - Routes each person to their own OpenClaw session via `/opt/homebrew/bin/openclaw agent --to`
 * - Sends responses back via imsg
 */

const { execSync, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const STATE_FILE = '/tmp/imessage-family-state.json';
const LOG_FILE = '/tmp/imessage-family.log';
const CONTACTS_FILE = path.join(process.env.HOME, '.openclaw/workspace/family-contacts.json');
const POLL_INTERVAL = 8000; // 8 seconds

function log(msg) {
  const line = `${new Date().toISOString()} ${msg}`;
  console.log(line);
}

function run(cmd) {
  return execSync(cmd, { encoding: 'utf8' }).trim();
}

// Load whitelisted contacts: { "+19163030339": "Adam", ... }
function loadContacts() {
  if (!fs.existsSync(CONTACTS_FILE)) {
    log('ERROR: family-contacts.json not found');
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(CONTACTS_FILE, 'utf8'));
}

// Load last-seen message ID per chat
function loadState() {
  if (!fs.existsSync(STATE_FILE)) return {};
  return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

// Get recent messages for a chat
function getMessages(chatId, limit = 10) {
  try {
    const output = run(`/opt/homebrew/bin/imsg history --chat-id ${chatId} --limit ${limit} --attachments --json`);
    return output.split('\n').filter(Boolean).map(line => JSON.parse(line));
  } catch (e) {
    return [];
  }
}

// Get all chats
function getChats() {
  try {
    const output = run('/opt/homebrew/bin/imsg chats --json');
    return output.split('\n').filter(Boolean).map(line => JSON.parse(line));
  } catch (e) {
    return [];
  }
}

// Copy attachment to workspace for processing
function stageAttachment(originalPath) {
  const expanded = originalPath.replace('~', process.env.HOME);
  if (!fs.existsSync(expanded)) return null;
  const dest = `/tmp/imsg-attach-${Date.now()}${path.extname(expanded) || '.bin'}`;
  fs.copyFileSync(expanded, dest);
  return dest;
}

// Build message text to send to the agent
function buildAgentMessage(msg, contacts) {
  let text = msg.text || '';
  // Clean up placeholder characters
  text = text.replace(/[\uFFFC\u0000-\u0008\u000B-\u001F]/g, '').trim();

  const parts = [];

  // Add attachment descriptions
  for (const att of (msg.attachments || [])) {
    if (!att.mime_type) continue;
    if (att.mime_type.startsWith('image/')) {
      const staged = stageAttachment(att.original_path);
      if (staged) {
        parts.push(`[Image attached: ${staged}]`);
      }
    }
  }

  if (text) parts.push(text);
  return parts.join('\n') || '[message with no readable content]';
}

// Send agent response via imsg
function sendReply(identifier, response) {
  // Escape single quotes
  const safe = response.replace(/'/g, "'\\''");
  try {
    run(`/opt/homebrew/bin/imsg send --to "${identifier}" --text '${safe}'`);
    log(`Sent reply to ${identifier}`);
  } catch (e) {
    log(`ERROR sending to ${identifier}: ${e.message}`);
  }
}

// Route message through OpenClaw agent
function routeToAgent(number, agentMessage, name) {
  log(`Routing message from ${name} (${number}) to agent`);
  const safe = agentMessage.replace(/'/g, "'\\''").replace(/"/g, '\\"');
  try {
    const result = run(
      `/opt/homebrew/bin/openclaw agent --to "${number}" --deliver --reply-channel imessage --reply-to "${number}" --message "${safe}" --timeout 60`
    );
    log(`Agent response delivered for ${name}`);
    return result;
  } catch (e) {
    log(`ERROR routing to agent for ${name}: ${e.message}`);
    return null;
  }
}

async function poll() {
  const contacts = loadContacts();
  const state = loadState();
  const chats = getChats();

  for (const chat of chats) {
    const identifier = chat.identifier;
    if (!contacts[identifier]) continue; // not whitelisted

    const name = contacts[identifier];
    const chatId = chat.id;
    const messages = getMessages(chatId, 5);

    const lastSeenId = state[identifier] || 0;
    const newMessages = messages
      .filter(m => !m.is_from_me && m.id > lastSeenId)
      .sort((a, b) => a.id - b.id);

    if (newMessages.length === 0) continue;

    log(`${newMessages.length} new message(s) from ${name}`);

    for (const msg of newMessages) {
      const agentMsg = buildAgentMessage(msg, contacts);
      log(`Message from ${name}: ${agentMsg.substring(0, 80)}`);
      routeToAgent(identifier, agentMsg, name);
      state[identifier] = msg.id;
      saveState(state);
    }
  }
}

log('Family iMessage handler started');
log(`Watching contacts: ${Object.values(loadContacts()).join(', ')}`);

// Poll loop
setInterval(() => {
  poll().catch(e => log(`Poll error: ${e.message}`));
}, POLL_INTERVAL);

// Initial poll
poll().catch(e => log(`Initial poll error: ${e.message}`));
