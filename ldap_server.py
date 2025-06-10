import os
import json
from twisted.internet import reactor, defer
from twisted.python import log
from twisted.python.logfile import LogFile
from ldaptor.protocols.ldap import distinguishedname, ldaperrors
from ldaptor import ldapfilter, interfaces, attributeset
from ldaptor.entry import BaseLDAPEntry
from ldaptor.protocols.ldap.ldapserver import BaseLDAPServer
from zope.interface import implementer

LDAP_DATA_DIR = 'ldap-data'
LOGS_DIR = 'logs'
USERS_FILE = os.path.join(LDAP_DATA_DIR, 'users.json')
GROUPS_FILE = os.path.join(LDAP_DATA_DIR, 'groups.json')

def load_data(file_path):
    if not os.path.exists(file_path):
        if file_path == USERS_FILE:
            save_data(USERS_FILE, {}) # Create empty users file if not exists
            return {}
        elif file_path == GROUPS_FILE:
            save_data(GROUPS_FILE, {}) # Create empty groups file if not exists
            return {}
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        log.err(f"Error decoding JSON from {file_path}. Returning empty data.")
        return {} # Return empty dict if JSON is malformed

def save_data(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

if not os.path.exists(LDAP_DATA_DIR):
    os.makedirs(LDAP_DATA_DIR)

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Initialize data files if they don't exist or are empty
if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
    save_data(USERS_FILE, {})
if not os.path.exists(GROUPS_FILE) or os.path.getsize(GROUPS_FILE) == 0:
    save_data(GROUPS_FILE, {})

@implementer(interfaces.IConnectedLDAPEntry)
class MyLDAPEntry(BaseLDAPEntry):  # Changed base class to BaseLDAPEntry
    def __init__(self, dn, attributes):
        super().__init__(dn, attributes)

    def bind(self, password):
        users = load_data(USERS_FILE)
        # Assuming DN is like "uid=username,ou=users,dc=example,dc=com"
        # For simplicity, we'll extract the uid part.
        # A more robust solution would parse the DN properly.
        dn_str = self.dn.getText()
        try:
            # Attempt to get the RDN (Relative Distinguished Name)
            # For a DN like "uid=testuser,ou=users,dc=example,dc=com", the first RDN is "uid=testuser"
            first_rdn = self.dn.split()[0]
            if first_rdn.attributeType.getText().lower() == 'uid':
                uid = first_rdn.value.getText()
                if uid in users and users[uid].get('password') == password.decode(): # password is bytes
                    return defer.succeed(self)
        except IndexError:
            log.err(f"Could not parse RDN from DN: {dn_str}")
            pass # Fall through to fail
        except Exception as e:
            log.err(f"Error during bind for {dn_str}: {e}")
            pass # Fall through to fail
        
        return defer.fail(ldaperrors.LDAPInvalidCredentials())


class MyLDAPServer(BaseLDAPServer):
    # Base DN for our LDAP server
    base_dn_str = "ou=users,dc=data-gadgets,dc=com" # You can make this configurable
    base_dn = distinguishedname.DistinguishedName(base_dn_str)

    def _get_user_entry(self, uid):
        users = load_data(USERS_FILE)
        if uid in users:
            user_data = users[uid].copy()
            # Construct DN for the user
            user_dn_str = f"uid={uid},{self.base_dn_str}"
            user_dn = distinguishedname.DistinguishedName(user_dn_str)
            
            attributes = {'objectClass': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                          'uid': [uid]}
            # Add other attributes, excluding password
            for key, value in user_data.items():
                if key != 'password':
                    attributes[key] = [str(value)] # LDAP attributes are often lists
            return MyLDAPEntry(user_dn, attributes)
        return None

    def handle_LDAPBindRequest(self, request, controls, reply):
        log.msg(f"Bind request for DN: {request.dn.getText()}")
        # For simplicity, we'll assume the DN is a user DN we can look up directly
        # e.g., uid=someuser,ou=users,dc=example,dc=com
        
        dn_str = request.dn.getText()
        password = request.password
        
        users = load_data(USERS_FILE)

        try:
            # Attempt to get the RDN (Relative Distinguished Name)
            # For a DN like "uid=testuser,ou=users,dc=example,dc=com", the first RDN is "uid=testuser"
            parsed_dn = distinguishedname.DistinguishedName(dn_str)
            first_rdn = parsed_dn.split()[0]

            if first_rdn.attributeType.getText().lower() == 'uid':
                uid = first_rdn.value.getText()
                if uid in users and users[uid].get('password') == password.decode():
                    log.msg(f"Bind successful for {uid}")
                    return defer.succeed(MyLDAPEntry(request.dn, {}))
                else:
                    log.msg(f"Bind failed for {uid}: Invalid credentials")
                    return defer.fail(ldaperrors.LDAPInvalidCredentials())
            else:
                log.msg(f"Bind failed: DN {dn_str} not in expected format (uid=...)")
                return defer.fail(ldaperrors.LDAPInvalidCredentials())
        except Exception as e:
            log.err(f"Error during bind processing for {dn_str}: {e}")
            return defer.fail(ldaperrors.LDAPOperationsError(str(e)))

    def handle_LDAPSearchRequest(self, request, controls, reply):
        log.msg(f"Search request: base='{request.baseObject.getText()}', filter='{request.filter}'")
        users = load_data(USERS_FILE)
        results = []

        # Very basic filter parsing: (uid=username)
        filter_text = request.filter.asText()
        
        # Handle one-level search (children of the base DN)
        if request.scope == 1:  # SCOPE_ONELEVEL
            # If the base is our main user OU, list users
            if request.baseObject.getText() == self.base_dn_str:
                if filter_text.startswith('(uid=') and filter_text.endswith(')'):
                    target_uid = filter_text[5:-1]
                    user_entry = self._get_user_entry(target_uid)
                    if user_entry:
                        results.append(user_entry)
                elif filter_text == '(objectClass=*)': # List all users
                    for uid in users.keys():
                        user_entry = self._get_user_entry(uid)
                        if user_entry:
                            results.append(user_entry)

        return defer.succeed(results)


def main():
    from twisted.internet import protocol

    # Initialize data files if they don't exist or are empty
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        save_data(USERS_FILE, {})
    if not os.path.exists(GROUPS_FILE) or os.path.getsize(GROUPS_FILE) == 0:
        save_data(GROUPS_FILE, {})

    # Create logs directory if it doesn't exist
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # Configure log rotation: 10MB max size, keep 5 files
    log_file = LogFile(
        name='ldap_server.log',
        directory=LOGS_DIR,
        rotateLength=10 * 1024 * 1024,  # 10MB in bytes
        maxRotatedFiles=5
    )
    log.startLogging(log_file)
    
    factory = protocol.ServerFactory()
    factory.protocol = MyLDAPServer
    
    port = 389 # Standard LDAP port
    reactor.listenTCP(port, factory)
    print(f"LDAP server starting on port {port} with base DN 'ou=users,dc=data-gadgets,dc=com'...")
    print(f"Data directory: {os.path.abspath(LDAP_DATA_DIR)}")
    print(f"Logs directory: {os.path.abspath(LOGS_DIR)}")
    print("Make sure your ldap-data/users.json and ldap-data/groups.json exist and are valid JSON.")
    reactor.run()

if __name__ == '__main__':
    main()
