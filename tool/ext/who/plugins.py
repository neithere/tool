__all__ = ['DocuPlugin']


from tool.ext.documents import db    # FIXME use bundle conf
from schema import User


class DocuPlugin(object):
    """ Docu-powered authenticator and metadata provider for repoze.who.
    """

    def __init__(self):
        pass

    # IAuthenticatorPlugin
    def authenticate(self, environ, identity):
        try:
            username = identity['login']
            password = identity['password']
        except KeyError:
            return None

        users = User.objects(db).where(username=username)

        if not users:
            return None

        assert len(users) == 1, ('expected only one user with username {0}, '
                                 'got {1}'.format(username, len(users)))

        user = users[0]

        if user.check_password(password):
            return user.pk

        return None

    # IMetadataProvider
    def add_metadata(self, environ, identity):
        userid = identity.get('repoze.who.userid')
        try:
            instance = User.object(db, userid)
        except KeyError:
            pass
        else:
            identity['instance'] = instance
            #identity.update(info)
