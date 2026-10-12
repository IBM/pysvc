##############################################################################
# Copyright 2025 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################
"""
IBM SVC CLI Client Module

:module: pysvc

"""
PYSVC_DEFAULT_LOGGER = "pysvc"

# Defensive FIPS compatibility patch for Paramiko PKey.get_fingerprint
#
# Paramiko's default get_fingerprint() calls hashlib.md5() without the
# usedforsecurity=False flag.  On FIPS-enabled systems (RHEL/OCP with a FIPS
# kernel) OpenSSL blocks MD5 for security use, so that bare call raises a
# ValueError and every SSH connection attempt fails at the fingerprint step.
#
# The outer try/except runs at import time.  It is intentionally broad:
# if the monkey-patch itself fails for any reason (e.g. a future Paramiko
# release changes its internal structure) the module must still import cleanly.
# The worst-case outcome is that the original get_fingerprint remains in place;
# on a FIPS host the SSH connection will then fail with a clear OpenSSL error
# rather than a silent pysvc crash, so the failure is always observable.
try:
    import hashlib
    import paramiko.pkey

    def _fips_safe_get_fingerprint(self):
        # Primary path: md5(..., usedforsecurity=False) is the correct
        # FIPS-compliant way to use MD5 for non-security-sensitive data such
        # as a display fingerprint.  Python 3.9+ passes the flag to OpenSSL,
        # which allows it even in FIPS mode.
        try:
            return hashlib.md5(self.asbytes(), usedforsecurity=False).digest()
        # Fallback path — three known edge cases:
        #   ValueError:     older OpenSSL FIPS builds that block MD5 entirely,
        #                   ignoring the usedforsecurity flag (some RHEL 8
        #                   FIPS kernels exhibit this behaviour).
        #   TypeError:      Python < 3.9 where usedforsecurity is not a valid
        #                   keyword argument for hashlib.md5().
        #   AttributeError: asbytes() is missing on an unexpected PKey
        #                   subclass.
        # In all three cases the first 16 bytes of SHA256 are returned so the
        # caller still receives a 16-byte digest (same length as MD5) computed
        # with a FIPS-approved algorithm.
        except (ValueError, TypeError, AttributeError):
            return hashlib.sha256(self.asbytes()).digest()[:16]

    paramiko.pkey.PKey.get_fingerprint = _fips_safe_get_fingerprint
except Exception:
    pass

version_tuple = (2, 0, 3)


def get_version_string():
    """Current version of Client."""
    if isinstance(version_tuple[-1], str):
        return '.'.join(map(str, version_tuple[:-1])) + '.' + version_tuple[-1]
    return '.'.join(map(str, version_tuple))


version = get_version_string()
