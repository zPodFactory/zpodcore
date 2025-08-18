import socket
import ssl
import sys
import time
import random

import OpenSSL.crypto


def get_certificate(hostname, port=443, max_retries=5, base_delay=1):
    """Get certificate with retry logic for network errors"""
    for attempt in range(max_retries):
        try:
            # Create an SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Set up a socket and connect to the remote host
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                    # Get the remote certificate in DER format
                    der_cert = secure_sock.getpeercert(binary_form=True)

            # Convert DER-encoded certificate to PEM format
            pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
            return OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, pem_cert
            )

        except (socket.gaierror, socket.timeout, ConnectionRefusedError, OSError) as e:
            if attempt == max_retries - 1:
                print(
                    f"Failed to connect to {hostname}:{port} after {max_retries} attempts. Last error: {e}"
                )
                raise

            # Exponential backoff with jitter
            delay = base_delay * (2**attempt) + random.uniform(0, 1)
            print(
                f"Connection attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f} seconds..."
            )
            time.sleep(delay)

        except Exception as e:
            print(f"Unexpected error while getting certificate: {e}")
            raise


# Match for both hostname & FQDN in CN
def wait_for_cn_with_value(hostname, desired_cn):
    while True:
        try:
            cert = get_certificate(hostname)
            cn = cert.get_subject().commonName
            print(f"Checking if {desired_cn} in CN:{cn}...")
            if desired_cn in cn:
                print("Certificate CN has been updated to include hostname, exiting !")
                exit(0)
            print("Sleeping 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"Error checking certificate: {e}")
            print("Sleeping 5s before retry...")
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python esxi_check_certificate.py <hostname> <desired_cn>")
        sys.exit(1)

    hostname = sys.argv[1]
    desired_cn = sys.argv[2]

    wait_for_cn_with_value(hostname, desired_cn)
