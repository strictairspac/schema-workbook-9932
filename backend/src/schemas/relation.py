from pydantic import BaseModel,Field,field_validator
class RelationInput(BaseModel):
    code:str=Field(min_length=2,max_length=80)
    title:str=Field(min_length=2,max_length=160)
    attributes:list[str]=Field(min_length=1,max_length=10)
    note:str=Field(default='',max_length=300)
    @field_validator('attributes')
    @classmethod
    def attributes_valid(cls,value):
        if len(set(value))!=len(value) or any(not x.strip() or len(x)>40 for x in value): raise ValueError('属性必须唯一且非空，每项不超过40字')
        return value
