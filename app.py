"""Instagram Reels 자동화 파이프라인 - 진입점

실행:
    python app.py
    python app.py --share    # 외부 공유 링크 생성
"""
import argparse
import os

from reels.gui.app import build_app


def main():
    parser = argparse.ArgumentParser(description="Reels 자동화 GUI")
    parser.add_argument("--share", action="store_true", help="외부 공유 링크 생성")
    parser.add_argument("--port", type=int, default=7860, help="포트 번호")
    args = parser.parse_args()

    server_name = os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1")

    app = build_app()
    app.launch(share=args.share, server_name=server_name, server_port=args.port)


if __name__ == "__main__":
    main()
