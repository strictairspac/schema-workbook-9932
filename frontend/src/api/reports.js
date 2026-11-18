import {api} from './client.js';
export const reportsApi={list:()=>api('/reports'),create:data=>api('/reports','POST',data)};
