# -*- coding: utf-8 -*-

__all__ = ['KNOWN_PRESETS']


from repoze.who.interfaces import IIdentifier
from repoze.who.interfaces import IChallenger
from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.cookie import InsecureCookiePlugin
from repoze.who.plugins.form import FormPlugin
from repoze.who.plugins.htpasswd import HTPasswdPlugin
from repoze.who.classifiers import default_request_classifier
from repoze.who.classifiers import default_challenge_decider

from views import render_login_form


def get_docu_plugin():
    # import postponed so this module can be safely imported by admin, etc.
    # without circular imports
    from plugins import DocuPlugin
    return DocuPlugin()

def get_basic_auth_config_preset(**kwargs):
    basic_auth = BasicAuthPlugin('repoze.who')
    docu_plugin = get_docu_plugin()

    return {
        'identifiers':       [('basic_auth', basic_auth)],
        'authenticators':    [('docu', docu_plugin)],
        'challengers':       [('basic_auth', basic_auth)],
        'mdproviders':       [('docu', docu_plugin)],
        'classifier':        default_request_classifier,
        'challenge_decider': default_challenge_decider,
    }

def get_form_config_preset(**kwargs):
    secret = kwargs['secret']
    assert secret
    auth_tkt = AuthTktCookiePlugin(secret, 'auth_tkt', secure=True,
                                   timeout=7*24*60*60,
                                   reissue_time=5*24*60*60)
    # FIXME: the proper form (with callable) doesn't work
    #form = FormPlugin('__do_login',
    #                  rememberer_name='auth_tkt',
    #                  formcallable=render_login_form)
    form = FormPlugin('__do_login', rememberer_name='auth_tkt')
    form.classifications = { IIdentifier:['browser'],
                             IChallenger:['browser'] } # only for browser
    docu_plugin = get_docu_plugin()

    return {
        'identifiers':       [('form', form), ('auth_tkt', auth_tkt)],
        'authenticators':    [('docu', docu_plugin),   # no cookie yet
                              ('auth_tkt', auth_tkt)], # cookie exists
        'challengers':       [('form', form)],
        'mdproviders':       [('docu', docu_plugin)],
        'classifier':        default_request_classifier,
        'challenge_decider': default_challenge_decider,
    }


KNOWN_PRESETS = {
    'basic': get_basic_auth_config_preset,
    'form': get_form_config_preset,
}
