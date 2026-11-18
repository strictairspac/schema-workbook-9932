import {reportsApi} from '../api/reports.js';
export const reportsStore={items:[],async refresh(){this.items=await reportsApi.list();return this.items;}};
