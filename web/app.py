import web
import json
import os
import sys

urls = (
    '/snom', 'snom',
    '/snom/lookup', 'snom_lookup',
    '/snom/search', 'snom_search',
    '/snom/search/(.+)', 'snom_search',
    '/snom/contact/(.+)/(.+)', 'snom_contact',
    '/snom/group/(.+)/(.+)', 'snom_group',
    '/snom/group/(.+)', 'snom_group'
    )

template_globals = {
    'app_path': lambda p: web.ctx.homedomain + '/' + web.ctx.homepath + p,
}

CLIENT_SECRETS_JSON = 'client_secrets.json'
if not os.path.isfile(CLIENT_SECRETS_JSON):
    if 'CLIENT_SECRETS_JSON' in os.environ.keys():
        CLIENT_SECRETS_JSON = os.environ['CLIENT_SECRETS_JSON']
    else:
        print("ERROR: Clien Secrets JSON file missing.")
        print("\tplease create it with name 'client_secrets.json' or define the env. variable CLIENT_SECRETS_JSON")
        sys.exit(-1)

data_store = os.path.splitext(CLIENT_SECRETS_JSON)[0] + '-datastore.json'

render = web.template.render('templates/', globals=template_globals)

def get_data():
    fp = open(data_store)
    store = json.load(fp)
    fp.close()
    return store

class snom_lookup:
    def GET(self):
        user_data = web.input(number=None)
        number = user_data.number.split('@')[0]
        if number.startswith('sip:'):
            number = number[4:]
        store = get_data()
        web.header('Content-Type', 'text/xml')
        for group in store:
            items = store[group]
            try:
                contact = (item for item in items if number in item["phones"]).next()
                return render.snom_lookup({'contact': contact, 'number': number})
            except StopIteration:
                return
        return

class snom_search:
    def GET(self, name=None):
        store = get_data()
        web.header('Content-Type', 'text/xml')
        if name == None:
            return render.snom_search()

        contacts = {}
        for group in store:
            items = store[group]
            g_contacts = [item for item in items if name.lower() in item["title"].lower()]
            if len(g_contacts) > 0:
                contacts[group] = g_contacts
        
        if len(contacts) == 0:    
            return render.snom_notfound("Contact not found")
        return render.snom_search_res({'contacts': contacts})

class snom:
    def GET(self):
        store = get_data()
        web.header('Content-Type', 'text/xml')
        # first level keys are the group names
        return render.snom_main(store.keys())

class snom_contact:
    def GET(self, group, id):
        id = int(id)
        store = get_data()
        web.header('Content-Type', 'text/xml')
        if store.has_key(group):
            items = store[group]
            try:
                contact = (item for item in items if item["id"] == id).next()
                return render.snom_contact({'contact': contact, 'group': group})
            except StopIteration:
                raise web.notfound(render.snom_notfound("Contact not found"))
        else:
            raise web.notfound(render.snom_notfound("Group not found"))
        pass

class snom_group:
    def GET(self, group, page=0):
        page_items = 2
        page = int(page)
        store = get_data()
        web.header('Content-Type', 'text/xml')
        if store.has_key(group):
            data = {
                    'group': group,
                    'contacts': store[group][page*page_items:(page+1)*page_items],
                    'next_page': page+1, 
                    'prev_page': page-1,
                    'max_pages': len(store[group])/page_items }
            return render.snom_group(data)
        else:
            raise web.notfound(render.snom_notfound("Group not found"))

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    app.run()
