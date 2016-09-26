#!/usr/bin/env python

#import atom
import sys
import os
import os.path
import json
import httplib2
import codecs

from pprint import pprint
from oauth2client import client
from oauth2client import file
from oauth2client import tools

# Native application Client ID JSON from the Google Developers Console,
# store in the same directory as this script:
CLIENT_SECRETS_JSON = 'client_secrets.json'

parser = tools.argparser
args = parser.parse_args()

if not os.path.isfile(CLIENT_SECRETS_JSON):
    if 'CLIENT_SECRETS_JSON' in os.environ.keys():
        CLIENT_SECRETS_JSON = os.environ['CLIENT_SECRETS_JSON']
    else:
        print("ERROR: Clien Secrets JSON file missing.")
        print("\tplease create it with name 'client_secrets.json' or define the env. variable CLIENT_SECRETS_JSON")
        sys.exit(-1)


class SyncGoogleContacts:
    def __init__(self, client_secrets):
        self._token_filename = os.path.splitext(client_secrets)[0] + '.dat'
        self.datastore = os.path.splitext(client_secrets)[0] + '-datastore.json'
        self._client_secrets = client_secrets
        self._scope = 'https://www.googleapis.com/auth/contacts.readonly'
        self._user_agent = 'SnomSync'

    def get_auth_token(self, non_interactive=False):
        flow = client.flow_from_clientsecrets(self._client_secrets, scope=self._scope, message=tools.message_if_missing(self._client_secrets))
        storage = file.Storage(self._token_filename)
        self.credentials = storage.get()
        if self.credentials is None or self.credentials.invalid:
            if non_interactive:
                sys.stderr.write('ERROR: Invalid or missing Oauth2 credentials. To reset auth flow manually, run without --non_interactive\n')
            else:
                self.credentials = tools.run_flow(flow, storage, args)
        self.token = httplib2.Http()
        self.token = self.credentials.authorize(self.token)

    def get_groups(self):
        res, content = self.token.request('https://www.google.com/m8/feeds/groups/default/thin?alt=json', method='GET')
        if res['status'] == "200":
            data = json.loads(content.decode('utf8'))
            groups = []
            for gdata in data['feed']['entry']:
                name = gdata['title']['$t']
                id = gdata['id']['$t']
                groups.append(
                        {'name': name, 'id': id}
                        )
                return groups
        else:
            raise Exception("Error getting the list of groups")
        

    def get_contacts(self, group_id=None):
        if group_id:
            query_str = '&group={0}'.format(group_id)
        else:
            query_str = ''
        res, content = self.token.request('https://www.google.com/m8/feeds/contacts/default/thin?alt=json{0}'.format(query_str), method="GET")
        if res['status'] == "200":
            data = json.loads(content.decode('utf8'))
            contacts = []
            id = 0
            for gdata in data['feed']['entry']:
                c = {}
                c['id'] = id
                if 'gd$email' in gdata:
                    emails = [e['address'] for e in gdata.get('gd$email')]
                else:
                    emails = []
                c['emails'] = emails

                if 'gd$phoneNumber' in gdata:
                    phones = [e['$t'] for e in gdata['gd$phoneNumber']] 
                else:
                    phones = []
                c['phones'] = phones

                if 'title' in gdata:
                    title = gdata['title']['$t']
                else:
                    title = None
                c['title'] = title

                if 'gd$organization' in gdata:
                    organizations = [{'name': e.get('gd$orgName',{'$t': None})['$t'], 'job_title': e.get('gd$orgTitle',{'$t':None})['$t']} for e in gdata['gd$organization']]
                else:
                    organizations = []
                c['organizations'] = organizations
                id = id + 1
                contacts.append(c)
            return contacts    
        else:
            raise Exception("Error getting contacts")

    def store_all_contacts(self):
        self.store = {}
        my_contacts = self.get_contacts()
        self.store['My Contacts'] = my_contacts
        print("Found %d Personal Contacts" % len(my_contacts))
        groups = self.get_groups()
        for g in groups:
            self.store[g['name']] = self.get_contacts(group_id=g['id'])
            print("Found %d contacts in group '%s'" % (len(self.store[g['name']]), g['name']))
        fd = open(self.datastore, 'w+')
        json.dump(self.store, fd)
        fd.close()

def main():
    g = SyncGoogleContacts(CLIENT_SECRETS_JSON)
    g.get_auth_token()
    g.store_all_contacts()

if __name__ == '__main__':
    main()
