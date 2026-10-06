export const environment = {
  production: true,
  apiUrl: '/api',
  wsUrl: `${typeof location !== 'undefined' && location.protocol === 'https:' ? 'wss' : 'ws'}://${typeof location !== 'undefined' ? location.host : 'localhost'}/ws`,
};
