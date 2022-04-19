from aiohttp import web
import aiohttp_jinja2
import jinja2
import yaml

import os
import uuid

config = yaml.safe_load(open('config.yml'))
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

if not os.path.isfile(config['db_location']):
    f = open(config['db_location'], 'x')
    f.close()

if not os.path.isdir(config['box_location']):
    os.mkdir(config['box_location'])

routes = web.RouteTableDef()


@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def index(request):
    return {'title': config['page_name']}

@routes.post('/')
@aiohttp_jinja2.template('upload.html')
async def upload(request):
    reader = await request.multipart()

    id_code = str(uuid.uuid1().hex)
    path = os.path.join(config['box_location'], id_code)
    os.mkdir(path)

    while True:
        field = await reader.next()
        if field.name == "upload":
            filename = field.filename
            if not filename:
                return {'report': "Select a file to upload", 'title': config['page_name']}
            size = 0
            with open(os.path.join(path, filename), 'wb') as f:
                while True:
                    chunk = await field.read_chunk()  # 8192 bytes by default.
                    if not chunk:
                        #if size == 0:
                        #    return {'report': "Select a file to upload", 'title': config['page_name']}
                        break
                    size += len(chunk)
                    f.write(chunk)
            break
    
    report = "{} with a size of {} bytes has been successfully uploaded to {}".format(filename, size, id_code)
    return {'report': report, 'title': config['page_name']}

@routes.get('/{id}')
@routes.get('/{id}/')
async def download(request):
    path = os.path.join(config['box_location'], request.match_info['id'])
    filename = os.listdir(path)[0]
    return web.FileResponse(os.path.join(path, filename), status=200)

routes.static('/', 'static/')

app.add_routes(routes)
web.run_app(app, port=config['port'])