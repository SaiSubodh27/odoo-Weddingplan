import http from 'node:http';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DATA_FILE = join(__dirname, 'data', 'mockClients.json');

const PORT = process.env.PORT || 5000;

// Load clients into memory from JSON
let clients = [];
try {
  const data = readFileSync(DATA_FILE, 'utf-8');
  clients = JSON.parse(data);
} catch (err) {
  console.error('Error loading initial mock data, starting empty:', err);
  clients = [];
}

const saveClients = () => {
  try {
    writeFileSync(DATA_FILE, JSON.stringify(clients, null, 2), 'utf-8');
  } catch (err) {
    console.error('Error persisting clients:', err);
  }
};

const sendJSON = (res, statusCode, data) => {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  });
  res.end(JSON.stringify(data));
};

const parseBody = (req) => {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (err) {
        reject(err);
      }
    });
    req.on('error', reject);
  });
};

const server = http.createServer(async (req, res) => {
  // CORS Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    });
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;
  const searchParams = parsedUrl.searchParams;

  console.log(`[${new Date().toISOString()}] ${req.method} ${pathname}`);

  // Health check
  if (pathname === '/' || pathname === '/api/health') {
    return sendJSON(res, 200, {
      service: 'The Royal Knot — Backend API',
      status: 'operational',
      operatingRegions: ['Jaipur', 'Udaipur'],
      version: '1.0.0'
    });
  }

  // GET /api/clients
  if (req.method === 'GET' && pathname === '/api/clients') {
    const search = searchParams.get('search')?.toLowerCase();
    const status = searchParams.get('status');

    let result = [...clients];

    if (status && status !== 'All') {
      result = result.filter(c => c.status === status);
    }

    if (search) {
      result = result.filter(c =>
        c.partner1Name.toLowerCase().includes(search) ||
        c.partner2Name.toLowerCase().includes(search) ||
        c.email.toLowerCase().includes(search) ||
        c.phone.includes(search) ||
        c.weddingLocation.toLowerCase().includes(search) ||
        c.id.toLowerCase().includes(search)
      );
    }

    return sendJSON(res, 200, {
      total: result.length,
      data: result
    });
  }

  // GET /api/clients/:id
  if (req.method === 'GET' && pathname.startsWith('/api/clients/')) {
    const id = pathname.replace('/api/clients/', '');
    const client = clients.find(c => c.id === id);
    if (!client) {
      return sendJSON(res, 404, { error: `Client record ${id} not found` });
    }
    return sendJSON(res, 200, { data: client });
  }

  // POST /api/clients
  if (req.method === 'POST' && pathname === '/api/clients') {
    try {
      const payload = await parseBody(req);
      const nextId = `TRK-2026-0${80 + clients.length + 1}`;
      const newClient = {
        ...payload,
        id: nextId,
        createdAt: new Date().toISOString().split('T')[0]
      };
      clients.unshift(newClient);
      saveClients();
      return sendJSON(res, 201, {
        message: 'Client dossier registered successfully',
        data: newClient
      });
    } catch {
      return sendJSON(res, 400, { error: 'Invalid JSON request body' });
    }
  }

  // PATCH /api/clients/:id/status
  if (req.method === 'PATCH' && pathname.includes('/status')) {
    const id = pathname.split('/')[3];
    try {
      const { status } = await parseBody(req);
      const client = clients.find(c => c.id === id);
      if (!client) {
        return sendJSON(res, 404, { error: `Client ${id} not found` });
      }
      client.status = status;
      saveClients();
      return sendJSON(res, 200, {
        message: `Status updated to ${status}`,
        data: client
      });
    } catch {
      return sendJSON(res, 400, { error: 'Failed to update client status' });
    }
  }

  // GET /api/weddings
  if (req.method === 'GET' && pathname === '/api/weddings') {
    const weddings = clients.map(c => ({
      id: c.id,
      couple: `${c.partner1Name} & ${c.partner2Name}`,
      weddingDate: c.weddingDate,
      weddingLocation: c.weddingLocation,
      guestCount: c.expectedGuestCount,
      budget: c.estimatedBudget,
      theme: c.weddingTheme,
      status: c.status
    }));
    return sendJSON(res, 200, { total: weddings.length, data: weddings });
  }

  // Phase 2 Placeholders
  if (pathname === '/api/agreements' || pathname === '/api/catering' || pathname === '/api/vendors' || pathname === '/api/payments') {
    return sendJSON(res, 200, {
      module: pathname.replace('/api/', ''),
      status: 'Coming Soon in Phase 2',
      message: 'This module is scheduled for database schema integration.'
    });
  }

  // 404 Fallback
  return sendJSON(res, 404, { error: 'Route not found' });
});

server.listen(PORT, () => {
  console.log(`\n✦ The Royal Knot Backend API Server ✦`);
  console.log(`Operating Hubs: Jaipur & Udaipur`);
  console.log(`Server running at: http://localhost:${PORT}`);
  console.log(`Health check:     http://localhost:${PORT}/api/health`);
  console.log(`Clients API:      http://localhost:${PORT}/api/clients\n`);
});
