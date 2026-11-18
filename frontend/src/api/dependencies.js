import {api} from './client.js';
export const dependenciesApi={list:()=>api('/dependencies'),create:data=>api('/dependencies','POST',data)};
