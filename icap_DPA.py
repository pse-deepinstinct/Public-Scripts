import argparse
import logging
import socket
import sys
from typing import List

logger = logging.getLogger()


def send_icap_content(scanner_ip: str, file_content: bytes):
    service = f'icap://{scanner_ip}/classify'.encode('latin-1')
    port = 1344
    logger.info(f'Sending scan request to {service.decode()} on port {port}')
    sock = _establish_socket_connection(host=scanner_ip, port=port)
    chunks, req, resp = _create_icap_request_parts(file_content=file_content)
    _send_content(content_chunks=chunks, perimeter_ip=scanner_ip, req=req, resp=resp, service=service, sock=sock)
    response = _receive_response(sock=sock)

    result_content, header, verdict = _parse_response(response=response)
    return result_content, header, verdict


def _parse_response(response: bytes):
    # allure.attach(body=str(response), name='ICAP raw response', attachment_type=allure.attachment_type.TEXT)
    icap_headers_bytes, http_headers_bytes, content, *extra_stuff = response.strip().split(b'\r\n\r\n')
    icap_headers = icap_headers_bytes.decode()
    http_headers = http_headers_bytes.decode()
    logger.info(f'ICAP response headers are: {icap_headers}')
    # allure.attach(body=icap_headers, name='ICAP response headers', attachment_type=allure.attachment_type.TEXT)
    # allure.attach(body=http_headers, name='http headers', attachment_type=allure.attachment_type.TEXT)
    verdict = 'Malicious' if 'Malware' in icap_headers else 'Benign'

    if verdict == 'Benign':
        file_data_raw = response.split(b'content-length: ')[1]
        res_lines = file_data_raw.splitlines()
        file_data_length = int(res_lines[0])

        start_bytes = b''
        start_bytes += res_lines[0]
        start_bytes += b'\r\n\r\n'
        start_bytes += res_lines[2]
        start_bytes += b'\r\n'

        file_data_raw = file_data_raw[len(start_bytes):]

        return file_data_raw[:file_data_length], icap_headers, verdict

    else:
        return 'NON-RELEVANT', icap_headers, verdict


def _receive_response(sock: socket.socket) -> bytes:
    sock.shutdown(socket.SHUT_WR)
    data = sock.recv(1024)
    response = data
    while len(data):
        data = sock.recv(1024)
        response = response + data
    sock.close()
    return response


def _send_content(content_chunks: List, perimeter_ip: str, req: bytes, resp: bytes, service: bytes,
                  sock: socket.socket):
    send_messages = [b"RESPMOD %s ICAP/1.0\r\n" % service, b"Host: %s\r\n" % (perimeter_ip.encode('latin-1')),
                     f"Encapsulated: req-hdr=0, res-hdr={len(req)}, res-body={len(req) + len(resp)}\r\n".encode(
                         'latin-1'), b"\r\n", req, resp]
    for message in send_messages:
        sock.send(message)
    for chunk in content_chunks:
        sock.send(hex((len(chunk)))[2:].encode('latin-1') + b"\r\n")
        sock.send(chunk + b'\r\n')
    sock.send(b"0\r\n")
    sock.send(b"\r\n")


def _create_icap_request_parts(file_content: bytes):
    req = b"GET /origin-resource HTTP/1.1\r\n" + b"Host: www.origin-server.com\r\n" + \
          b"Accept: text/html, text/plain, image/gif\r\n" + b"Accept-Encoding: gzip, compress\r\n\r\n"
    resp = b"HTTP/1.1 200 OK\r\n" + b"Date: Mon, 10 Jan 2000 09:52:22 GMT\r\n" + b"Server: Apache/1.3.6 (Unix)\r\n" + \
           b'ETag: "63840-1ab7-378d415b"\r\n' + b"Content-Type: text/html\r\n" + \
           f"Content-Length: {len(file_content)}\r\n".encode('latin-1') + b"\r\n"
    chunks = [file_content[i:i + 1000] for i in range(0, len(file_content), 1000)]
    return chunks, req, resp


def _establish_socket_connection(host: str, port: int):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        logger.info(f"SOCKET CREATION ERROR: {msg}")
        sys.exit(1)
    try:
        sock.connect((host, port))
    except socket.error as msg:
        logger.info(f"SOCKET CONNECTION ERROR: {msg}")
        sys.exit(2)
    return sock


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scanner-ip', action='store', dest='scanner_ip', required=True)
    parser.add_argument('-f', '--file-path', action='store', dest='file_path', required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.file_path, 'rb') as f:
        content = f.read()
        result_content, header, verdict = send_icap_content(scanner_ip=args.scanner_ip, file_content=content)
        print(f'Verdict is {verdict}')
        print(f'header is {header}')


if __name__ == '__main__':
    main()
