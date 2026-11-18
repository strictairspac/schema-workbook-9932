import {dependenciesApi} from '../api/dependencies.js';
export const dependenciesStore={items:[],async refresh(){this.items=await dependenciesApi.list();return this.items;}};
