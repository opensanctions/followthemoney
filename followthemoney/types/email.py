import logging
import re
from typing import TYPE_CHECKING

import idna

from followthemoney.types.common import PropertyType
from followthemoney.util import defer as _

# Regex to filter out invalid emails from a CSV file:
# csvgrep -c value -r '^(?![a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)' contrib/statements_emails.csv > contrib/test_invalid_emails.csv

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class EmailType(PropertyType):
    """Internet mail address (e.g. user@example.com). These are notoriously hard
    to validate, but we use an irresponsibly simple rule and hope for the best."""

    LOCAL_RE = re.compile(r"^[^<>()\[\]\,;:\?\s@\"]{1,64}$", re.UNICODE)

    name = "email"
    group = "emails"
    label = _("E-Mail Address")
    plural = _("E-Mail Addresses")
    matchable = True
    pivot = True

    # def _check_exists(self, domain):
    #     """Actually try to resolve a domain name."""
    #     try:
    #         domain = domain.encode('idna').lower()
    #         socket.getaddrinfo(domain, None)
    #         return True
    #     except:
    #         return False

    def clean_domain_part(self, domain: str) -> str | None:
        """Clean and normalize the domain part of the email."""
        domain = domain.rstrip(".").lower()
        try:
            # IDNA 2008 with UTS #46 mapping. The stdlib "idna" codec implements IDNA 2003,
            # which folds deviation characters (ß -> ss, ς -> σ) into a different domain.
            # This is idempotent for domains that are already IDNA-encoded.
            domain = idna.encode(domain, uts46=True).decode("ascii")

            # idna accepts any DNS name; a public mail domain additionally needs a TLD
            # that is not a single character or numeric (rules out localhost, IPs).
            _, dot, tld = domain.rpartition(".")
            if len(dot) == 0 or len(tld) < 2 or tld.isdigit():
                return None

            return idna.decode(domain)
        except (idna.IDNAError, UnicodeError):
            return None

    def validate(
        self, value: str, fuzzy: bool = False, format: str | None = None
    ) -> bool:
        """Check to see if this is a valid email address."""
        return self.clean_text(value, fuzzy=fuzzy, format=format) is not None

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        """Parse and normalize an email address.

        Returns None if this is not an email address.
        """
        # TODO: https://pypi.python.org/pypi/publicsuffix/
        # handle URLs by extracting the domain names
        # or TODO: adopt email.utils.parseaddr

        # Remove mailto: prefix if present
        email = text.strip()
        email = email.removeprefix("mailto:")

        try:
            local, domain = email.rsplit("@", 1)
            """Clean and validate the local part of the email."""
            if self.LOCAL_RE.match(local) is None:
                return None

            domain_clean = self.clean_domain_part(domain)
            if domain_clean is None:
                return None
            return f"{local}@{domain_clean}"
        except ValueError:
            return None
