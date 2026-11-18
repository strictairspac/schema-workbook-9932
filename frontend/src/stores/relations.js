import {relationsApi} from '../api/relations.js';
export const relationsStore={items:[],async refresh(){this.items=await relationsApi.list();return this.items;}};
