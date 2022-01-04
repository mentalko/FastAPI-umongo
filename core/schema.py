from umongo import Document, fields, ValidationError, RemoveMissingSchema, set_gettext
from umongo.frameworks import PyMongoInstance

from pydantic import BaseModel, validator

import json
import datetime as dt

from core.db import instance


class UserSerializer(BaseModel):
    nick: str
    firstname: str
    lastname: str
    birthday: str
    password: str

    class Config:
        orm_mode = True

class UserPassSerializer(BaseModel):
    password: str



@instance.register
class User(Document):

    # We specify `RemoveMissingSchema` as a base marshmallow schema so that
    # auto-generated marshmallow schemas skip missing fields instead of returning None
    MA_BASE_SCHEMA_CLS = RemoveMissingSchema

    nick = fields.StrField(required=True, unique=True)
    firstname = fields.StrField()
    lastname = fields.StrField()
    birthday = fields.StrField() #fields.AwareDateTimeField()
    password = fields.StrField()  # Don't store it in clear in real life !

    class Meta:
        collection_name = "user"




# Define a custom marshmallow schema from User document to exclude password field
class UserNoPassSchema(User.schema.as_marshmallow_schema()):
    class Meta:
        exclude = ('password',)

user_no_pass_schema = UserNoPassSchema()

def dump_user_no_pass(u):
    return user_no_pass_schema.dump(u)


async def populate_db():
    await User.collection.drop()
    await User.ensure_indexes()
    with open('./data/data.json') as json_file:
        datas = json.load(json_file)
        for data in datas:
            user = User(**data)
            await user.commit()



"""
# Define a custom marshmallow schema to ignore read-only fields
class UserCreateSchema(User.schema.as_marshmallow_schema()):
    pass
    # class Meta:
    #     dump_only = ('nick', 'password',)


user_create_schema = UserCreateSchema()


# Define a custom marshmallow schema to ignore read-only fields
class UserUpdateSchema(User.schema.as_marshmallow_schema()):
    class Meta:
        dump_only = ('nick', 'password',)


user_update_schema = UserUpdateSchema()

# Define a custom marshmallow schema from User document to expose only password field
class ChangePasswordSchema(User.schema.as_marshmallow_schema()):
    class Meta:
        fields = ('password',)
        required = ('password',)


change_password_schema = ChangePasswordSchema()
"""