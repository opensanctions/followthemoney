import re
import logging
from typing import Optional, TYPE_CHECKING
from rigour.env import ENCODING

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

    DOMAIN_RE = re.compile(r"^(?!-)(?:[a-z0-9-]{1,63}(?<!-)\.)+[a-z0-9-]{2,}$", re.U)
    LOCAL_RE = re.compile(r"^[^<>()\[\]\,;:\?\s@\"]{1,64}$", re.U)

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

    def clean_domain_part(self, domain: str) -> Optional[str]:
        """Clean and normalize the domain part of the email."""
        domain = domain.rstrip(".").lower()
        try:
            # Convert domain to IDNA encoding if it contains non-ASCII characters. This should
            # be idempotent for domains that are already IDNA-encoded.
            domain = domain.encode("idna").decode(ENCODING)

            # Check if the domain matches the regex pattern, which requires labels to be
            # alphanumeric and hyphenated, and the TLD to be at least two characters long.
            if self.DOMAIN_RE.match(domain) is None:
                return None

            domain = domain.encode(ENCODING).decode("idna")
            return domain
        except UnicodeError:
            return None

    def validate(
        self, value: str, fuzzy: bool = False, format: Optional[str] = None
    ) -> bool:
        """Check to see if this is a valid email address."""
        return self.clean_text(value, fuzzy=fuzzy, format=format) is not None

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: Optional[str] = None,
        proxy: Optional["EntityProxy"] = None,
    ) -> Optional[str]:
        """Parse and normalize an email address.

        Returns None if this is not an email address.
        """
        # TODO: https://pypi.python.org/pypi/publicsuffix/
        # handle URLs by extracting the domain names
        # or TODO: adopt email.utils.parseaddr

        # Remove mailto: prefix if present
        email = text.strip()
        if email.startswith("mailto:"):
            email = email[7:]

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
