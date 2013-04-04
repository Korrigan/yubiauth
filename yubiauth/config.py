#
# Copyright (c) 2013 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

__all__ = [
    'settings'
]

import imp
import errno
import default_settings


VALUES = {
    'DATABASE_CONFIGURATION': 'db',
    'YKVAL_SERVERS': 'ykval',
    'YHSM_DEVICES': 'yhsm_devices',
    'CRYPT_CONTEXT': 'crypt_context',
}


def parse(conf, settings={}):
    for confkey, settingskey in VALUES.items():
        try:
            settings[settingskey] = conf.__getattribute__(confkey)
        except AttributeError:
            pass
    return settings


settings = parse(default_settings)

try:
    user_settings = imp.load_source('user_settings',
                                    '/etc/yubico/yubiauth/yubiauth')
    settings = parse(user_settings, settings)
except IOError, e:
    if not e.errno in [errno.ENOENT]:
        raise e

if isinstance(settings['yhsm_devices'], basestring):
    settings['yhsm_devices'] = {'main': settings['yhsm_devices']}
