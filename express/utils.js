
export function getBase64EncodedCredentials(client_id , client_secret) {
    const credentials = `${client_id}:${client_secret}`;
    return btoa(credentials);
}