#!/usr/bin/env node
/**
 * iMessage Attachment Watcher
 * 
 * Monitors iMessages from allowlisted contacts, copies attachments to:
 *   ~/Library/Mobile Documents/com~apple~CloudDocs/AgentShare/<Name>/
 * 
 * Filenames are prefixed with timestamp to avoid collisions.
 * State is tracked so we don't reprocess old messages.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const CONTACTS_FILE = path.join(process.env.HOME, '.openclaw/workspace/family-contacts.json');
const STATE_FILE = '/tmp/imessage-attachments-state.json';
const AGENTSHARE = path.join(process.env.HOME, 'Library/Mobile Documents/com~apple~CloudDocs/AgentShare');
const POLL_INTERVAL = 10000; // 10 seconds
const IMSG = '/opt/homebrew/bin/imsg';

function log(msg) {
  console.log(`${new Date().toISOString()} ${msg}`);
}

function run(cmd) {
  return execSync(cmd, { encoding: 'utf8' }).trim();
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
  } catch (e) { return []; }
}

function getMessages(chatId, limit = 20) {
  try {
    return run(`${IMSG} history --chat-id ${chatId} --limit ${limit} --attachments --json`)
      .split('\n').filter(Boolean).map(l => JSON.parse(l));
  } catch (e) { return []; }
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function poll() {
  const contacts = loadContacts();
  const state = loadState();
  const chats = getChats();

  for (const chat of chats) {
    const identifier = chat.identifier;
    if (!contacts[identifier]) continue;

    const name = contacts[identifier];
    const chatId = chat.id;
    const messages = getMessages(chatId, 20);
    const lastSeenId = state[identifier] || 0;

    const newMessages = messages
      .filter(m => !m.is_from_me && m.id > lastSeenId)
      .sort((a, b) => a.id - b.id);

    for (const msg of newMessages) {
      const attachments = (msg.attachments || []).filter(a => a.mime_type && !a.missing);

      if (attachments.length > 0) {
        const destDir = path.join(AGENTSHARE, name);
        ensureDir(destDir);

        for (const att of attachments) {
          const srcPath = att.original_path.replace('~', process.env.HOME);
          if (!fs.existsSync(srcPath)) {
            log(`Missing attachment, skipping: ${att.transfer_name}`);
            continue;
          }

          const ext = path.extname(att.transfer_name) || '';
          const timestamp = new Date(msg.created_at).toISOString().replace(/[:.]/g, '-').slice(0, 19);
          const destName = `${timestamp}_${att.transfer_name}`;
          const destPath = path.join(destDir, destName);

          try {
            fs.copyFileSync(srcPath, destPath);
            log(`Saved attachment from ${name}: ${destName}`);
          } catch (e) {
            log(`ERROR copying ${att.transfer_name}: ${e.message}`);
          }
        }
      }

      // Update state to latest seen id
      state[identifier] = Math.max(state[identifier] || 0, msg.id);
    }

    if (newMessages.length > 0) {
      saveState(state);
    }
  }
}

log('iMessage attachment watcher started');
log(`Contacts: ${Object.values(loadContacts()).join(', ')}`);
log(`AgentShare: ${AGENTSHARE}`);

// Initial poll
poll();

// Poll loop
setInterval(poll, POLL_INTERVAL);
