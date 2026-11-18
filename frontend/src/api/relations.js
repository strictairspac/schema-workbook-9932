import {api} from './client.js';
export const relationsApi={list:()=>api('/relations'),create:data=>api('/relations','POST',data)};
