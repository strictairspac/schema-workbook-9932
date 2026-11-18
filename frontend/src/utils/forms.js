export function formValues(form, numbers=[]){const values=Object.fromEntries(new FormData(form));for(const key of numbers)values[key]=Number(values[key]);return values;}
