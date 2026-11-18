import {api} from './client.js';
export const plansApi={list:()=>api('/plans'),create:data=>api('/plans','POST',data),detail:id=>api('/plans/'+id)};
