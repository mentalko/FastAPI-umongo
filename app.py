from fastapi import  HTTPException, status
from fastapi.applications import FastAPI

from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from umongo import ValidationError

from core.schema import *

app = FastAPI()

@app.on_event("startup")
async def startup_event(): 
    await populate_db()

def _to_objid(data):
    try:
        return ObjectId(data)
    except Exception:
        return None

def _nick_or_id_lookup(nick_or_id):
    return {'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]}


@app.get('/users/page_{page}')
async def list_users(
    page: int,
    limit: int = 5
):
    users = User.find().limit(limit).skip((page - 1) * limit)
    return jsonable_encoder({
        '_total':  await User.count_documents(),
        '_page': page,
        '_per_page': limit,
        '_items': [dump_user_no_pass(item) async for item in users]# item.dump()
    })

@app.get('/users/{nick_or_id}', response_model=UserSerializer)
async def get_user(
    nick_or_id: str
):
    user = await User.find_one(_nick_or_id_lookup(nick_or_id))
    if not user:
        raise HTTPException(status_code=404, detail=f"User {nick_or_id} not found")
    return dump_user_no_pass(user)

@app.post('/users/create', response_model=UserSerializer)
async def create_user(payload: UserSerializer):
    print(payload)
    
    try:
        user = User(**payload.dict()) 
        await user.commit()
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return user


@app.patch('/users/{nick_or_id}', response_model=UserSerializer)
async def update_user(
    nick_or_id: str,
    payload: UserSerializer
):
    user = await User.find_one(_nick_or_id_lookup(nick_or_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        print(payload.dict())  #user_update_schema.load(payload.dict())
        user.update(payload.dict())
        user.commit()
        print (user)
    except ValidationError as ve:
        pass

    return user #jsonify(dump_user_no_pass(user))

@app.put('/users/{nick_or_id}/change_password', response_model=UserSerializer)
async def change_user_password(
    nick_or_id: str,
    payload: UserPassSerializer
):
    user = await User.find_one(_nick_or_id_lookup(nick_or_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        data = payload.dict() #change_password_schema.load(payload)
        user.password = data['password']
        user.commit()
    except ValidationError as ve:
        pass
    return user #jsonify(dump_user_no_pass(user))

@app.delete('/users/{nick_or_id}')
async def delete_user(nick_or_id):
    user = await User.find_one(_nick_or_id_lookup(nick_or_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        await user.delete()
    except ValidationError as ve:
        pass
    return 'Ok'



