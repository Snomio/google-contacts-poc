#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import os
import os.path
import json
import httplib2

from oauth2client import client
from oauth2client import tools

from apiclient import discovery
from oauth2client.file import Storage

# Native application Client ID JSON from the Google Developers Console,
# store in the same directory as this script:
CLIENT_SECRETS_JSON = 'client_secrets.json'
SCOPES = 'https://www.googleapis.com/auth/admin.directory.user'
APPLICATION_NAME = 'G Suite global Directory SnomSync'

parser = tools.argparser
args = parser.parse_args()

if not os.path.isfile(CLIENT_SECRETS_JSON):
    if 'CLIENT_SECRETS_JSON' in os.environ.keys():
        CLIENT_SECRETS_JSON = os.environ['CLIENT_SECRETS_JSON']
    else:
        print("ERROR: Clien Secrets JSON file missing.")
        print("\tplease create it with name 'client_secrets.json' or define the env. variable CLIENT_SECRETS_JSON")
        sys.exit(-1)


class SyncGoogleDirectoryContacts:
    def __init__(self, client_secrets):
        self._token_filename = os.path.splitext(client_secrets)[0] + '-directory.dat'
        self.datastore = os.path.splitext(client_secrets)[0] + '-datastore.json'
        self._client_secrets = client_secrets
        self._scope = SCOPES

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """

        credential_path = self._token_filename
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self._client_secrets, self._scope)
            flow.user_agent = APPLICATION_NAME

            if args:
                credentials = tools.run_flow(flow, store, args)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def get_groups(self):
        """
        todo: Groups implementation goes here
        """

        return []

    def get_contacts(self, group_id=None):
        """ Creates a Google Admin SDK API service object and outputs a list of first
            100 users in the domain.
        """

        credentials = self.get_credentials()

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('admin', 'directory_v1', http=http)

        print('Getting the first 100 users in the domain')
        results = service.users().list(
            customer='my_customer',
            maxResults=100,
            showDeleted=False,
            orderBy='givenName',
            viewType='domain_public'
        ).execute()
        users = results.get('users', [])

        if not users:
            print('No users in the domain.')
        else:
            print('Users:')
            for user in users:
                print('{0} ({1})'.format(user['primaryEmail'],
                                         user['name']['fullName']))

            contacts = []
            id = 0
            for user in users:
                c = {}
                # c['id'] = id
                c['id'] = int(user['id'])

                c['emails'] = [user['primaryEmail']]

                if 'phones' in user:
                    phones = [e['value'] for e in user['phones']]
                else:
                    phones = []
                c['phones'] = phones

                # todo: fix title
                # if 'title' in user:
                #     title = user['organisations'][0]['name']
                # else:
                #     title = None
                c['title'] = user['name']['fullName']

                if 'organizations' in user:

                    organizations = [{'name': organization.get('name'),
                                      'title': organization.get('title')} for organization in
                                     user['organizations']]
                else:
                    organizations = []

                c['organizations'] = organizations
                id = id + 1
                contacts.append(c)
            return contacts

    def store_all_contacts(self):
        self.store = {}
        my_contacts = self.get_contacts()
        self.store['Directory'] = my_contacts
        print("Found %d Personal Contacts" % len(my_contacts))
        # groups = self.get_groups()
        # for g in groups:
        #     self.store[g['name']] = self.get_contacts(group_id=g['id'])
        #     print("Found %d contacts in group '%s'" % (len(self.store[g['name']]), g['name']))
        fd = open(self.datastore, 'w+')
        json.dump(self.store, fd)
        fd.close()


def main():
    g = SyncGoogleDirectoryContacts(CLIENT_SECRETS_JSON)
    g.store_all_contacts()


if __name__ == '__main__':
    main()
