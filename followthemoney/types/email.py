import re
import logging
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlparse
from normality import latinize_text

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

    def latinize_non_latin(self, text: str) -> str:
        """Transliterate non-Latin characters to Latin."""
        # Check if the domain contains only ASCII characters
        if not text.isascii():
            # If the text contains non-ASCII characters, transliterate it
            return latinize_text(text)
        return text

    def clean_domain_part(self, domain: str) -> Optional[str]:
        """Clean and normalize the domain part of the email."""
        if len(domain) < 4 or "." not in domain:
            return None
        if "," in domain:
            return None
        domain = urlparse(domain).hostname or domain
        domain = domain.lower()
        domain = domain.rstrip(".")
        domain = self.latinize_non_latin(domain)
        tld = domain.rsplit(".", 1)[-1]
        if len(tld) == 1:
            return None
        return domain

    def clean_local_part(self, mailbox: str) -> Optional[str]:
        """Clean and validate the local part of the email."""
        mailbox = mailbox.strip()
        if mailbox.lower().startswith("mailto:") or mailbox.lower().startswith(
            "email:"
        ):
            mailbox = mailbox.split(":", 1)[-1]
        mailbox = mailbox.strip()
        if " " in mailbox:
            return None
        mailbox = self.latinize_non_latin(mailbox)
        if mailbox.startswith("<") and mailbox.endswith(">"):
            mailbox = mailbox[1:-1]
        if ")" in mailbox or "(" in mailbox:
            return None
        if "?" in mailbox:
            return None
        if "!" in mailbox:
            # `!` is technically valid in quoted local parts, but we don't allow it.
            return None
        if "(" in mailbox or ")" in mailbox:
            return None
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
        if text is None or not isinstance(text, str) or not len(text):
            return None
        email = text.strip().strip('"')
        if email.startswith("<") and email.endswith(">"):
            email = email[1:-1]
        if email is None or not self.REGEX.match(email):
            return None
        mailbox, domain = email.rsplit("@", 1)
        mailbox = self.clean_local_part(mailbox)
        domain = self.clean_domain_part(domain)
        # TODO: https://pypi.python.org/pypi/publicsuffix/
        # handle URLs by extracting the domain names
        if domain is not None and mailbox is not None:
            return "@".join((mailbox, domain))
        return None

    # def country_hint(self, value)
    # TODO: do we want to use TLDs as country evidence?
