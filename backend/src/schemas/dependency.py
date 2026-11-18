from pydantic import BaseModel,Field,field_validator
class DependencyInput(BaseModel):
    relation_id:int=Field(gt=0)
    lhs:list[str]=Field(max_length=10)
    rhs:list[str]=Field(min_length=1,max_length=10)
    note:str=Field(default='',max_length=300)
    @field_validator('lhs','rhs')
    @classmethod
    def valid_attributes(cls,v):
        if len(set(v))!=len(v) or any(not x.strip() or len(x)>40 for x in v): raise ValueError('依赖属性不能为空或重复')
        return v
