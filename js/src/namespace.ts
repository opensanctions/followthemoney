
export class Namespace {
  private separator = '.'
  private namespaceKey: string

  constructor(namespaceKey: string) {
    this.namespaceKey = namespaceKey;
  }

  parse(id: string): string[] {
    return id.split(this.separator);
  }

  async signature(id: string): Promise<string> {
    // Generate an HMAC signature for the given ID using the namespace key, using 
    // SHA-1 as the hashing algorithm and returning the result as a hexadecimal string.
    // Use in-browser crypto library for compatibility with browsers.
    if (!this.namespaceKey.length) {
      return id;
    }
    // Convert strings to ArrayBuffers
    const encoder = new TextEncoder();
    const keyData = encoder.encode(this.namespaceKey);
    const data = encoder.encode(id);

    // Import the key
    const key = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'HMAC', hash: 'SHA-1' },
      false,
      ['sign']
    );

    // Generate the signature
    const signature = await crypto.subtle.sign('HMAC', key, data);

    // Convert to hexadecimal string
    const hashArray = Array.from(new Uint8Array(signature));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  }

  async sign(id: string): Promise<string> {
    const entityId = this.parse(id)[0];
    if (!entityId) {
      return id;
    }
    if (!this.namespaceKey.length) {
      return entityId;
    }
    const digest = await this.signature(entityId);

    return [entityId, digest].join(this.separator);
  }
}
