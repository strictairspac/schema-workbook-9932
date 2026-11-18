from pydantic import BaseModel,Field,field_validator
class PlanInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    relation_id:int=Field(gt=0)
    fragments:list[list[str]]=Field(min_length=1,max_length=12)
    @field_validator('fragments')
    @classmethod
    def fragments_valid(cls,value):
        for fragment in value:
            if not fragment:raise ValueError('每张分表至少包含一个属性')
            if len(set(fragment))!=len(fragment) or any(not x.strip() or len(x)>40 for x in fragment):
                raise ValueError('分表属性不能为空或重复，每项不超过40字')
        return value
