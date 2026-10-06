"""Launch SEEF — Self-Evolving Feature Engineering Framework locally."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Timer
import webbrowser


def main():
    assets = Path(__file__).resolve().parent / 'browser'
    handler = partial(SimpleHTTPRequestHandler, directory=str(assets))
    try:
        server = ThreadingHTTPServer(('127.0.0.1', 8000), handler)
    except OSError as error:
        raise SystemExit(f'Could not start SEEF on port 8000: {error}. Close the other server and try again.')
    url = 'http://localhost:8000'
    print('SEEF — Self-Evolving Feature Engineering Framework')
    print(f'Open {url} · Press Ctrl+C to stop.')
    Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nSEEF stopped.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
