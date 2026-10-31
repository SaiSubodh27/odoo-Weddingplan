const BASE = 'http://localhost:8000/api/v1/projects';
const json = async (url: string, method = 'GET', body?: unknown) => {
  const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  if (!res.ok) { const error = await res.json().catch(() => ({})); throw new Error(typeof error.detail === 'string' ? error.detail : `Request failed (${res.status})`); }
  return res.status === 204 ? null : res.json();
};
export const planningApi = {
  staff: (project: string) => json(`${BASE}/${encodeURIComponent(project)}/planning-staff`),
  audit: (project: string) => json(`${BASE}/${encodeURIComponent(project)}/planning-audit`),
  summary: (project: string) => json(`${BASE}/${encodeURIComponent(project)}/planning-summary`),
  plan: (project: string) => json(`${BASE}/${encodeURIComponent(project)}/plan`),
  list: (project: string, resource: string) => json(`${BASE}/${encodeURIComponent(project)}/${resource === 'tasks' ? 'plan/tasks' : 'planning/' + resource}`),
  create: (project: string, resource: string, data: object) => json(`${BASE}/${encodeURIComponent(project)}/${resource === 'tasks' ? 'plan/tasks' : 'planning/' + resource}`, 'POST', data),
  update: (project: string, resource: string, id: string, data: object) => json(`${BASE}/${encodeURIComponent(project)}/${resource === 'tasks' ? 'plan/tasks' : 'planning/' + resource}/${encodeURIComponent(id)}`, 'PATCH', data),
  remove: (project: string, resource: string, id: string) => json(`${BASE}/${encodeURIComponent(project)}/${resource === 'tasks' ? 'plan/tasks' : 'planning/' + resource}/${encodeURIComponent(id)}`, 'DELETE'),
};
