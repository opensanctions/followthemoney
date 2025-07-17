import re
import logging
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlparse
from rigour.env import ENCODING

from followthemoney.types.common import PropertyType
from followthemoney.util import sanitize_text, defer as _

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class EmailType(PropertyType):
    """Internet mail address (e.g. user@example.com). These are notoriously hard
    to validate, but we use an irresponsibly simple rule and hope for the best."""

    REGEX_RAW = r"^[^@\s]+@[^@\s]+\.\w+$"
    REGEX = re.compile(REGEX_RAW)
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

        if not domain or len(domain) < 4 or "." not in domain:
            return None
        if "," in domain:
            return None
        # Normalize and lowercase
        domain = urlparse(domain).hostname or domain
        domain = domain.lower().rstrip(".")
        # Validate the domain using IDNA encoding.
        # If the domain contains non-ASCII characters (e.g., Cyrillic),
        # it will be converted to its punycode representation (e.g., "почта@орг.ру" → "почта@xn--c1avg.xn--p1ag").
        # We discard the result since we're only validating that encoding succeeds.
        try:
            _ = domain.encode("idna").decode(ENCODING)
        except UnicodeError:
            return None
        # Reject TLDs shorter than 2 characters (e.g., "a.b")
        tld = domain.rsplit(".", 1)[-1]
        if len(tld) < 2:
            return None
        return domain

    def clean_local_part(self, mailbox: str) -> Optional[str]:
        """Clean and validate the local part of the email."""
        if not mailbox or not isinstance(mailbox, str):
            return None
        mailbox = mailbox.strip()
        # Remove prefixes like "mailto:" or "email:"
        if mailbox.lower().startswith(("mailto:", "email:")):
            mailbox = mailbox.split(":", 1)[-1].strip()
        # Remove enclosing angle brackets
        if mailbox.startswith("<") and mailbox.endswith(">"):
            mailbox = mailbox[1:-1].strip()
        # Reject if it contains invalid characters
        if any(char in mailbox for char in (" ", "(", ")", "?")):
            return None
        return mailbox

    def validate(
        self, value: str, fuzzy: bool = False, format: Optional[str] = None
    ) -> bool:
        """Check to see if this is a valid email address."""
        # TODO: adopt email.utils.parseaddr
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
        if not isinstance(text, str) or not text:
            return None

        email = sanitize_text(text)
        if not email:
            return None

        email = email.strip().strip('"')
        if email.startswith("<") and email.endswith(">"):
            email = email[1:-1]

        if not self.REGEX.match(email) or "@" not in email:
            return None

        mailbox, domain = email.rsplit("@", 1)
        mailbox_clean = self.clean_local_part(mailbox)
        domain_clean = self.clean_domain_part(domain)

        if domain_clean and mailbox_clean:
            return "@".join((mailbox_clean, domain_clean))
        return None

    # def country_hint(self, value)
    # TODO: do we want to use TLDs as country evidence?
