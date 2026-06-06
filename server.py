import os
import json
from aiohttp import web
from datetime import date

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

async def handle_index(request):
    with open("webapp/index.html","r",encoding="utf-8") as f:
        content=f.read()
    return web.Response(text=content,content_type="text/html")

async def handle_get_data(request):
    user_id=request.query.get("user_id","0")
    data=load_data()
    return web.json_response(data.get(str(user_id),{}))

async def handle_add_entry(request):
    body=await request.json()
    user_id=str(body.get("user_id","0"))
    entry=body.get("entry",{})
    mk=body.get("month_key",date.today().strftime("%Y-%m"))
    dk=body.get("day_key",date.today().strftime("%Y-%m-%d"))
    data=load_data()
    if user_id not in data: data[user_id]={}
    if mk not in data[user_id]: data[user_id][mk]={}
    if dk not in data[user_id][mk]: data[user_id][mk][dk]=[]
    data[user_id][mk][dk].append(entry)
    save_data(data)
    return web.json_response({"ok":True})

async def handle_delete_entry(request):
    body=await request.json()
    user_id=str(body.get("user_id","0"))
    entry_id=body.get("entry_id")
    mk=body.get("month_key")
    data=load_data()
    ud=data.get(user_id,{})
    if mk in ud:
        for dk in ud[mk]:
            ud[mk][dk]=[e for e in ud[mk][dk] if e.get("id")!=entry_id]
    save_data(data)
    return web.json_response({"ok":True})

async def handle_set_budget(request):
    body=await request.json()
    user_id=str(body.get("user_id","0"))
    mk=body.get("month_key")
    budgets=body.get("budgets",{})
    data=load_data()
    if user_id not in data: data[user_id]={}
    data[user_id][f"budget_{mk}"]=budgets
    save_data(data)
    return web.json_response({"ok":True})

async def handle_get_budget(request):
    user_id=request.query.get("user_id","0")
    mk=request.query.get("month_key",date.today().strftime("%Y-%m"))
    data=load_data()
    return web.json_response(data.get(str(user_id),{}).get(f"budget_{mk}",{}))

def create_app():
    app=web.Application()
    app.router.add_get("/",handle_index)
    app.router.add_get("/api/data",handle_get_data)
    app.router.add_post("/api/entry",handle_add_entry)
    app.router.add_post("/api/delete",handle_delete_entry)
    app.router.add_post("/api/budget",handle_set_budget)
    app.router.add_get("/api/budget",handle_get_budget)
    return app

if __name__=="__main__":
    port=int(os.getenv("PORT",8080))
    web.run_app(create_app(),port=port)