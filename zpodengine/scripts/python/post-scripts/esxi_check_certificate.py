import socket
import ssl
import sys
import time

import OpenSSL.crypto


def get_certificate(hostname, port=443):
    # Create an SSL context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Set up a socket and connect to the remote host
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
            # Get the remote certificate in DER format
            der_cert = secure_sock.getpeercert(binary_form=True)

    # Convert DER-encoded certificate to PEM format
    pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)

    return OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_cert)


def wait_for_cn_with_value(hostname, value):
    while True:
        cert = get_certificate(hostname)
        cn = cert.get_subject().commonName
        print(f"Checking if CN:{cn} matches {value}...")
        if cn == value:
            print("Certificate matches, exiting !")
            exit(0)
        print("Sleeping 5s...")
        time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python esxi_check_certificate.py <hostname> <desired_cn>")
        sys.exit(1)

    hostname = sys.argv[1]
    desired_cn = sys.argv[2]

    wait_for_cn_with_value(hostname, desired_cn)
