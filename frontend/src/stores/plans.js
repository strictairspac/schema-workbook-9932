import {plansApi} from '../api/plans.js';
export const plansStore={items:[],async refresh(){this.items=await plansApi.list();return this.items;}};
