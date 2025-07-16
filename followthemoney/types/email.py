import re
import logging
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlparse
from normality.cleaning import strip_quotes

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
        if len(domain) < 4 or "." not in domain:
            return None
        domain = domain.replace(",", "")
        domain = domain.lower()
        if domain.endswith("."):
            domain = domain[:-1]
        # Check for single-letter TLDs (very rare, not currently valid)
        if domain.count(".") >= 1:
            tld = domain.rsplit(".", 1)[-1]
            if len(tld) == 1:
                return None
        return domain

    def clean_local_part(self, mailbox: str) -> Optional[str]:
        """Clean and validate the local part of the email."""
        mailbox = mailbox.strip()
        if mailbox.startswith("mailto:") or mailbox.startswith("email:"):
            mailbox = mailbox.split(":", 1)[-1]
        if " " in mailbox:
            return None
        if mailbox.startswith("<") and mailbox.endswith(">"):
            mailbox = mailbox[1:-1]
        if mailbox.startswith('"') and mailbox.endswith('"'):
            mailbox = mailbox[1:-1]
        if "?" in mailbox:
            return None
        if "(" in mailbox or ")" in mailbox:
            return None
        # `!` is technically valid in quoted local parts, but flag if needed.
        return mailbox

    def validate(
        self, value: str, fuzzy: bool = False, format: Optional[str] = None
    ) -> bool:
        """Check to see if this is a valid email address."""
        # TODO: adopt email.utils.parseaddr
        cleaned_value = self.clean_text(value, fuzzy=fuzzy, format=format)
        if cleaned_value is None:
            return False
        email = sanitize_text(cleaned_value)
        if email is None or not self.REGEX.match(email):
            return False
        if "@" not in email:
            return False
        mailbox, domain = email.rsplit("@", 1)
        mailbox = self.clean_local_part(mailbox)
        domain = self.clean_domain_part(domain)

        if mailbox is None or domain is None:
            return False
        return True

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
        email = strip_quotes(text)
        if email is None or not self.REGEX.match(email):
            return None
        mailbox, domain = email.rsplit("@", 1)
        # TODO: https://pypi.python.org/pypi/publicsuffix/
        # handle URLs by extracting the domain name
        domain = urlparse(domain).hostname or domain
        domain = domain.lower()
        domain = domain.rstrip(".")
        # handle unicode
        try:
            domain = domain.encode("idna").decode("ascii")
        except UnicodeError:
            return None
        if domain is not None and mailbox is not None:
            return "@".join((mailbox, domain))
        return None

    # def country_hint(self, value)
    # TODO: do we want to use TLDs as country evidence?
